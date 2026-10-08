"""Tradução de falhas de rede/HTTP em `SourcePage` (a busca nunca propaga exceção de fonte)."""

from __future__ import annotations

import logging

from app.connectors.base import SourcePage, SourceStatus
from app.connectors.http import UpstreamHttpError, UpstreamTimeoutError
from app.core.errors import RateLimitedError, UpstreamError

logger = logging.getLogger(__name__)


def failure_page(exc: Exception, *, source: str, auth_message: str) -> SourcePage:
    """Converte a exceção em estado da fonte, com mensagem em português sem dados sensíveis."""
    if isinstance(exc, RateLimitedError):
        message = "Limite de requisições da fonte atingido."
        if exc.retry_after:
            message += f" Tente novamente em {exc.retry_after} s."
        return SourcePage(status=SourceStatus.RATE_LIMITED, message=message)
    if isinstance(exc, UpstreamTimeoutError):
        return SourcePage(status=SourceStatus.TIMEOUT, message="A fonte demorou para responder.")
    if isinstance(exc, UpstreamHttpError) and exc.upstream_status in (401, 403):
        return SourcePage(status=SourceStatus.ERROR, message=auth_message)
    if isinstance(exc, UpstreamError):
        return SourcePage(status=SourceStatus.ERROR, message=exc.message)
    # Qualquer outra coisa é um defeito nosso ou uma resposta inesperada: detalhe só no log.
    logger.error("Falha inesperada na fonte", extra={"source": source}, exc_info=exc)
    return SourcePage(status=SourceStatus.ERROR, message="Resposta inesperada da fonte.")
