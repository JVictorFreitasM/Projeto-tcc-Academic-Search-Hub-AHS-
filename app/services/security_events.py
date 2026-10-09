"""Registro de eventos de segurança, sem dados pessoais (OS-029: consulta e retenção)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SecurityEvent
from app.models.security_event import EVENT_TYPES

FORBIDDEN_DETAIL_KEYS = frozenset({"email", "password", "token", "name"})


def _check_details(details: dict[str, Any]) -> None:
    forbidden = FORBIDDEN_DETAIL_KEYS & {str(key).lower() for key in details}
    if forbidden:
        raise ValueError("details não pode conter: " + ", ".join(sorted(forbidden)))


async def record_event(
    session: AsyncSession,
    event_type: str,
    *,
    user_id: uuid.UUID | None = None,
    ip_hash: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Adiciona o evento à sessão (quem chama decide quando confirmar)."""
    if event_type not in EVENT_TYPES:
        raise ValueError(f"tipo de evento desconhecido: {event_type}")
    details = details or {}
    _check_details(details)
    session.add(
        SecurityEvent(event_type=event_type, user_id=user_id, ip_hash=ip_hash, details=details)
    )
    await session.flush()
