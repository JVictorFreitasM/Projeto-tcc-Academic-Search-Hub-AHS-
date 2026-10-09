"""Busca educada de páginas HTML: `robots.txt`, identificação, pausa por domínio e limites."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from app.services.normalize import safe_url

logger = logging.getLogger(__name__)

MIN_DELAY_SECONDS = 2.0
MAX_PAGE_BYTES = 1024 * 1024
MAX_REDIRECTS = 3
HTML_TYPES = ("text/html", "application/xhtml+xml")
ROBOTS_TOKEN = "AcademicSearchHub"  # noqa: S105 (nome do agente no robots.txt, não é segredo)

Clock = Callable[[], float]
Sleep = Callable[[float], Awaitable[None]]


class PoliteScraper:
    """Nunca contorna bloqueio: `robots.txt` proibido, login ou erro significam "não raspar"."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        min_delay: float = MIN_DELAY_SECONDS,
        clock: Clock = time.monotonic,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self._client = client
        self._min_delay = min_delay
        self._clock = clock
        self._sleep = sleep
        self._robots: dict[str, RobotFileParser | None] = {}  # None = proibido por prudência
        self._last_request: dict[str, float] = {}
        self.requests_made = 0

    async def _pace(self, domain: str) -> None:
        """Garante a pausa mínima entre duas requisições ao mesmo domínio."""
        last = self._last_request.get(domain)
        if last is not None:
            wait = self._min_delay - (self._clock() - last)
            if wait > 0:
                await self._sleep(wait)
        self._last_request[domain] = self._clock()

    async def _plain_get(self, url: str, domain: str) -> httpx.Response:
        await self._pace(domain)
        self.requests_made += 1
        return await self._client.get(url, follow_redirects=False)

    async def _load_robots(self, scheme: str, domain: str) -> RobotFileParser | None:
        if domain in self._robots:
            return self._robots[domain]
        parser: RobotFileParser | None
        try:
            response = await self._plain_get(f"{scheme}://{domain}/robots.txt", domain)
        except httpx.HTTPError:
            parser = None  # sem resposta: por prudência, não raspar
        else:
            parser = RobotFileParser()
            if response.status_code >= 500:
                parser = None
            elif response.status_code >= 400:
                parser.parse([])  # sem robots.txt: tudo permitido
            elif response.status_code == 200:
                parser.parse(response.text.splitlines())
            else:
                parser = None
        self._robots[domain] = parser
        return parser

    async def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        parser = await self._load_robots(parts.scheme, parts.netloc.lower())
        return parser is not None and parser.can_fetch(ROBOTS_TOKEN, url)

    async def fetch(self, url: str) -> str | None:
        """Devolve o HTML da página ou `None` (proibida, login, erro, grande ou não-HTML)."""
        current = safe_url(url)
        try:
            for _ in range(MAX_REDIRECTS + 1):
                if current is None or not await self.allowed(current):
                    return None
                domain = urlsplit(current).netloc.lower()
                response = await self._plain_get(current, domain)
                if response.is_redirect and response.headers.get("location"):
                    current = safe_url(urljoin(current, response.headers["location"]))
                    continue  # o destino passa de novo por robots.txt e pausa
                return self._read(response)
        except httpx.HTTPError:
            logger.info("Página não obtida na raspagem")
        return None

    @staticmethod
    def _read(response: httpx.Response) -> str | None:
        if response.status_code != 200:  # inclui 401/403: nunca raspar o que exige login
            return None
        content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
        if content_type not in HTML_TYPES:
            return None
        if len(response.content) > MAX_PAGE_BYTES:
            return None
        return response.text
