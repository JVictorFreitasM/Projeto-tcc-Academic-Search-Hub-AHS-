"""Cliente HTTP resiliente para as fontes externas."""

from __future__ import annotations

import asyncio
import json
import logging
import ssl
import time
from collections.abc import Awaitable, Callable, Mapping
from functools import lru_cache
from typing import Any
from urllib.parse import urlsplit

import httpx

from app import __version__
from app.core.config import Settings
from app.core.errors import RateLimitedError, UpstreamError

logger = logging.getLogger(__name__)

MAX_REDIRECTS = 3
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
RETRY_STATUS = frozenset({502, 503, 504})
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF_SECONDS = 0.3

Sleep = Callable[[float], Awaitable[None]]


class UpstreamTimeoutError(UpstreamError):
    code = "upstream_timeout"
    default_message = "A fonte demorou demais para responder."


class UpstreamHttpError(UpstreamError):
    """Resposta HTTP de erro (4xx/5xx) da fonte."""

    code = "upstream_http_error"

    def __init__(self, status: int, message: str | None = None) -> None:
        super().__init__(message or f"A fonte respondeu com erro HTTP {status}.")
        self.upstream_status = status


class ResponseTooLargeError(UpstreamError):
    code = "upstream_response_too_large"
    default_message = "A resposta da fonte excedeu o tamanho máximo permitido."


@lru_cache
def _ssl_context() -> ssl.SSLContext:
    """Cria o contexto SSL uma vez só: montá-lo a cada cliente é lento (sobretudo no Windows)."""
    return httpx.create_ssl_context()


def make_client(settings: Settings, *, timeout: float | None = None) -> httpx.AsyncClient:
    """Cliente com tempo limite, identificação (`User-Agent`) e redirecionamentos limitados.

    `timeout` troca o tempo limite padrão (`SOURCE_TIMEOUT_SECONDS`) para fontes sabidamente lentas.
    """
    contact = settings.contact_email or "nao-informado"
    return httpx.AsyncClient(
        timeout=httpx.Timeout(timeout if timeout is not None else settings.source_timeout_seconds),
        verify=_ssl_context(),
        headers={"User-Agent": f"AcademicSearchHub/{__version__} (+contato: {contact})"},
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        follow_redirects=True,
        max_redirects=MAX_REDIRECTS,
    )


def _base_url(url: str) -> str:
    """Endereço sem consulta nem fragmento: é o único que vai para o log (chaves ficam fora)."""
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}{parts.path}"


def _retry_after(response: httpx.Response) -> int | None:
    value = response.headers.get("Retry-After", "").strip()
    return int(value) if value.isdigit() else None


async def _read_limited(response: httpx.Response) -> bytes:
    declared = response.headers.get("Content-Length")
    if declared and declared.isdigit() and int(declared) > MAX_RESPONSE_BYTES:
        raise ResponseTooLargeError
    chunks: list[bytes] = []
    size = 0
    async for chunk in response.aiter_bytes():
        size += len(chunk)
        if size > MAX_RESPONSE_BYTES:
            raise ResponseTooLargeError
        chunks.append(chunk)
    return b"".join(chunks)


async def get_json(
    client: httpx.AsyncClient,
    url: str,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    *,
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF_SECONDS,
    sleep: Sleep = asyncio.sleep,
) -> Any:
    """GET com JSON de resposta.

    Repete (até `retries` vezes, com espera exponencial) só em erro de rede, tempo esgotado e
    HTTP 502/503/504. Nunca repete em 4xx. HTTP 429 vira `RateLimitedError`.
    """
    base = _base_url(url)
    attempt = 0
    while True:
        started = time.perf_counter()
        try:
            async with client.stream("GET", url, params=params, headers=headers) as response:
                status = response.status_code
                elapsed = round((time.perf_counter() - started) * 1000)
                logger.info(
                    "Chamada externa",
                    extra={"url": base, "status": status, "duration_ms": elapsed},
                )
                if status == 429:
                    raise RateLimitedError(
                        "A fonte limitou as requisições.", retry_after=_retry_after(response)
                    )
                if status in RETRY_STATUS and attempt < retries:
                    pass  # segue para a espera e a nova tentativa
                elif status >= 400:
                    raise UpstreamHttpError(status)
                else:
                    body = await _read_limited(response)
                    try:
                        return json.loads(body)
                    except ValueError:
                        raise UpstreamError("A fonte devolveu uma resposta inválida.") from None
        except httpx.TimeoutException:
            if attempt >= retries:
                raise UpstreamTimeoutError from None
        except httpx.TooManyRedirects:
            raise UpstreamError("A fonte redirecionou demais.") from None
        except httpx.TransportError:
            if attempt >= retries:
                raise UpstreamError("Falha de rede ao consultar a fonte.") from None
        await sleep(backoff * (2**attempt))
        attempt += 1
