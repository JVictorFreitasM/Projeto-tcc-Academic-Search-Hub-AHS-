"""Limite de requisições por IP (slowapi, contadores em memória do processo).

Limitação conhecida (docs/SEGURANCA.md): os contadores ficam na memória de UM processo. Com mais de
um processo (`--workers N`, vários contêineres) cada um conta separado e o limite por IP deixa de
valer. Por isso a aplicação deve rodar com um único processo. Redis está fora do escopo.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.errors import error_body

limiter = Limiter(key_func=get_remote_address, headers_enabled=False)


def rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    """429 no formato padrão de erro, com `Retry-After` quando conhecido."""
    assert isinstance(exc, RateLimitExceeded)  # noqa: S101
    response = JSONResponse(
        error_body("rate_limited", "Muitas requisições. Tente novamente em instantes."),
        status_code=429,
    )
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        response.headers["X-Request-ID"] = request_id
    response.headers["Retry-After"] = "60"
    return response
