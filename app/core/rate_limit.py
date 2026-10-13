"""Limite de requisições por IP (slowapi, contadores em memória do processo).

Limitação conhecida (docs/SEGURANCA.md): os contadores ficam na memória de UM processo. Com mais de
um processo (`--workers N`, vários contêineres) cada um conta separado e o limite por IP deixa de
valer. Por isso a aplicação deve rodar com um único processo. Redis está fora do escopo.
"""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import Settings, get_settings
from app.core.errors import error_body
from app.core.security import hash_ip
from app.db.session import get_sessionmaker
from app.services.security_events import record_event

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address, headers_enabled=False)


def auth_limit() -> str:
    """Limite de login e cadastro (`RATE_LIMIT_AUTH`), lido a cada requisição."""
    return get_settings().rate_limit_auth


def search_limit() -> str:
    """Limite da busca (`RATE_LIMIT_SEARCH`), lido a cada requisição."""
    return get_settings().rate_limit_search


def client_ip_hash(request: Request, settings: Settings) -> str:
    return hash_ip(get_remote_address(request), settings.secret_key)


async def rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    """429 no formato padrão de erro, com `Retry-After`, registrando o evento `rate_limited`."""
    if not isinstance(exc, RateLimitExceeded):
        raise exc
    settings: Settings = request.app.state.settings
    try:
        factory = getattr(request.app.state, "session_factory", None) or get_sessionmaker()
        async with factory() as session:
            await record_event(
                session,
                "rate_limited",
                ip_hash=client_ip_hash(request, settings),
                details={"path": request.url.path},
            )
            await session.commit()
    except Exception:
        # Registrar o evento nunca pode impedir a resposta 429.
        logger.error("Não foi possível registrar o evento rate_limited")
    response = JSONResponse(
        error_body("rate_limited", "Muitas requisições. Tente novamente em instantes."),
        status_code=429,
    )
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        response.headers["X-Request-ID"] = request_id
    response.headers["Retry-After"] = "60"
    return response
