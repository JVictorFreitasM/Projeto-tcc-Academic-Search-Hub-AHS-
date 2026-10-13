"""Registro, consulta e retenção de eventos de segurança, sem dados pessoais.

Relacionado a OWASP A10 e LGPD art. 46.

`record_event` é a ÚNICA porta de entrada para gravar em `security_events`: recusa detalhes com
chaves ou valores que pareçam dado pessoal, e o IP só existe como hash.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Request
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import client_ip_hash
from app.models import SecurityEvent
from app.models.security_event import EVENT_TYPES

FORBIDDEN_DETAIL_KEYS = frozenset({"email", "password", "token", "name", "ip", "user_agent"})
DEFAULT_RETENTION_DAYS = 180
_EMAIL_LIKE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
_IPV4_LIKE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")


def _check_details(value: Any, path: str = "details") -> None:
    """Recusa chaves proibidas e valores que pareçam dado pessoal (percorre dicts e listas)."""
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in FORBIDDEN_DETAIL_KEYS:
                raise ValueError(f"{path}.{key}: chave proibida em eventos de segurança")
            _check_details(item, f"{path}.{key}")
    elif isinstance(value, list | tuple):
        for index, item in enumerate(value):
            _check_details(item, f"{path}[{index}]")
    elif isinstance(value, str) and (_EMAIL_LIKE.search(value) or _IPV4_LIKE.search(value)):
        raise ValueError(f"{path}: valor parece e-mail ou IP; eventos não guardam dado pessoal")


async def record_event(
    session: AsyncSession,
    event_type: str,
    user_id: uuid.UUID | None = None,
    request: Request | None = None,
    details: dict[str, Any] | None = None,
    *,
    ip_hash: str | None = None,
) -> None:
    """Adiciona o evento à sessão (quem chama decide quando confirmar).

    Com `request`, calcula o `ip_hash` (HMAC com sal de `SECRET_KEY`). Camadas sem acesso à
    requisição podem passar o `ip_hash` já calculado.
    """
    if event_type not in EVENT_TYPES:
        raise ValueError(f"tipo de evento desconhecido: {event_type}")
    details = details or {}
    _check_details(details)
    if request is not None and ip_hash is None:
        settings: Settings = request.app.state.settings
        ip_hash = client_ip_hash(request, settings)
    session.add(
        SecurityEvent(event_type=event_type, user_id=user_id, ip_hash=ip_hash, details=details)
    )
    await session.flush()


async def list_events(
    session: AsyncSession,
    *,
    event_type: str | None = None,
    since: datetime | None = None,
    limit: int = 50,
) -> list[SecurityEvent]:
    """Eventos mais recentes primeiro, com filtros opcionais."""
    statement = select(SecurityEvent).order_by(SecurityEvent.created_at.desc(), SecurityEvent.id)
    if event_type:
        statement = statement.where(SecurityEvent.event_type == event_type)
    if since:
        statement = statement.where(SecurityEvent.created_at >= since)
    result = await session.execute(statement.limit(limit))
    return list(result.scalars())


async def purge_older_than(session: AsyncSession, days: int, *, now: datetime | None = None) -> int:
    """Apaga só os eventos mais antigos que `days` dias e devolve quantos foram apagados."""
    if days < 1:
        raise ValueError("a retenção mínima é de 1 dia")
    limit = (now or datetime.now(UTC)) - timedelta(days=days)
    result = await session.execute(delete(SecurityEvent).where(SecurityEvent.created_at < limit))
    return int(result.rowcount)  # type: ignore[attr-defined]
