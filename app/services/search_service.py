"""Orquestrador da busca unificada: paralelismo, intercalação, deduplicação e falha parcial."""

from __future__ import annotations

import asyncio
import logging
import math
import time
import uuid
from collections.abc import Sequence
from dataclasses import dataclass

import httpx

from app.connectors.base import Connector, SourcePage, SourceQuery, SourceStatus
from app.connectors.http import make_client
from app.connectors.registry import build_connectors
from app.core.config import Settings
from app.core.errors import UpstreamError, ValidationAppError
from app.schemas.record import RecordOut
from app.schemas.search import SearchParams, SearchResponse, SourceInfo, SourceStatusOut
from app.scraping.completion import complete_abstracts
from app.scraping.polite_scraper import PoliteScraper
from app.services.dedup import deduplicate
from app.services.favorite_service import FavoriteLookup

logger = logging.getLogger(__name__)

# Folga sobre SOURCE_TIMEOUT_SECONDS para o tempo limite global de cada fonte (D4).
GLOBAL_TIMEOUT_MARGIN = 2.0
NOT_SELECTED = "Fonte não selecionada."
YEAR_SORT_NOTE = "A fonte não ordena por ano; a página combinada foi ordenada pelo sistema."


@dataclass
class _Outcome:
    page: SourcePage
    duration_ms: int


def _year_sort_key(record: RecordOut) -> tuple[int, int]:
    return (1, 0) if record.year is None else (0, -record.year)


class SearchService:
    def __init__(
        self,
        connectors: Sequence[Connector],
        settings: Settings,
        favorite_lookup: FavoriteLookup | None = None,
        scraper: PoliteScraper | None = None,
    ) -> None:
        self._connectors = list(connectors)
        self._settings = settings
        self._favorite_lookup = favorite_lookup
        self._scraper = scraper
        self._scraper_client: httpx.AsyncClient | None = None

    async def aclose(self) -> None:
        """Libera o cliente HTTP da raspagem, se tiver sido criado."""
        if self._scraper_client is not None:
            await self._scraper_client.aclose()
            self._scraper_client = None
            self._scraper = None

    async def _complete_abstracts(self, results: list[RecordOut]) -> list[RecordOut]:
        """Raspagem complementar (D8): desligada por padrão; falhas não alteram sources_status."""
        if not self._settings.scraping_enabled:
            return results
        if self._scraper is None:
            # Um único raspador por serviço, para a pausa por domínio valer entre buscas.
            self._scraper_client = make_client(self._settings)
            self._scraper = PoliteScraper(self._scraper_client)
        return await complete_abstracts(results, self._scraper)

    @property
    def slugs(self) -> list[str]:
        return [c.slug for c in self._connectors]

    def _select(self, params: SearchParams) -> list[Connector]:
        if params.sources is None:
            return list(self._connectors)
        unknown = [s for s in params.sources if s not in self.slugs]
        if unknown:
            raise ValidationAppError(
                "Fonte desconhecida. Valores válidos: " + ", ".join(self.slugs),
                details=[
                    {"field": "sources", "issue": f"fonte desconhecida: {slug}"} for slug in unknown
                ],
            )
        return [c for c in self._connectors if c.slug in params.sources]

    async def _run(self, connector: Connector, query: SourceQuery) -> _Outcome:
        started = time.perf_counter()
        limit = self._settings.source_timeout_seconds + GLOBAL_TIMEOUT_MARGIN
        try:
            page = await asyncio.wait_for(connector.search(query), timeout=limit)
        except TimeoutError:
            page = SourcePage(
                status=SourceStatus.TIMEOUT, message="A fonte demorou para responder."
            )
        except Exception:
            logger.error(
                "Falha inesperada em conector", extra={"source": connector.slug}, exc_info=True
            )
            page = SourcePage(status=SourceStatus.ERROR, message="Falha ao consultar a fonte.")
        return _Outcome(page, round((time.perf_counter() - started) * 1000))

    async def describe_sources(self) -> list[SourceInfo]:
        """Estado público de cada fonte (sem endereços internos, chaves nem contagens)."""
        states = await asyncio.gather(*(c.availability() for c in self._connectors))
        return [
            SourceInfo(
                slug=c.slug,
                name=c.name,
                kind="oai" if getattr(c, "kind", "api") == "oai" else "api",
                enabled=c.is_enabled(),
                status="ok" if available else "disabled",
                message=reason,
            )
            for c, (available, reason) in zip(self._connectors, states, strict=True)
        ]

    async def search(
        self,
        params: SearchParams,
        user_id: uuid.UUID | None = None,
        favorite_lookup: FavoriteLookup | None = None,
    ) -> SearchResponse:
        requested = self._select(params)
        status: dict[str, SourceStatusOut] = {
            c.slug: SourceStatusOut(
                status=SourceStatus.DISABLED, count=0, total=0, message=NOT_SELECTED
            )
            for c in self._connectors
        }

        availability = await asyncio.gather(*(c.availability() for c in requested))
        active: list[Connector] = []
        for connector, (available, reason) in zip(requested, availability, strict=True):
            if available:
                active.append(connector)
            else:
                status[connector.slug] = SourceStatusOut(
                    status=SourceStatus.DISABLED, count=0, total=0, message=reason
                )

        if not active:
            raise self._unavailable("Nenhuma fonte está disponível para esta busca.", status)

        per_source = math.ceil(params.page_size / len(active))
        query = SourceQuery(
            q=params.q,
            page=params.page,
            page_size=per_source,
            year_from=params.year_from,
            year_to=params.year_to,
            types=tuple(params.types or ()),
            sort=params.sort,
        )
        outcomes = await asyncio.gather(*(self._run(c, query) for c in active))

        include_duration = self._settings.app_env == "development"
        pages: list[list[RecordOut]] = []
        total = 0
        any_ok = False
        needs_manual_sort = False
        for connector, outcome in zip(active, outcomes, strict=True):
            page = outcome.page
            message = page.message
            if page.status is SourceStatus.OK:
                any_ok = True
                pages.append(page.records)
                total += page.total if page.total is not None else len(page.records)
                if params.sort == "year_desc" and not getattr(
                    connector, "supports_year_sort", False
                ):
                    needs_manual_sort = True
                    message = f"{message} {YEAR_SORT_NOTE}" if message else YEAR_SORT_NOTE
            status[connector.slug] = SourceStatusOut(
                status=page.status,
                count=len(page.records) if page.status is SourceStatus.OK else 0,
                total=page.total if page.status is SourceStatus.OK else 0,
                message=message,
                duration_ms=outcome.duration_ms if include_duration else None,
            )

        if not any_ok:
            raise self._unavailable("Todas as fontes falharam ou estão indisponíveis.", status)

        results = deduplicate(self._interleave(pages))[: params.page_size]
        if params.sort == "year_desc" or needs_manual_sort:
            results.sort(key=_year_sort_key)  # estável: empates mantêm a intercalação

        results = await self._complete_abstracts(results)
        results = await self._mark_favorites(results, user_id, favorite_lookup)
        return SearchResponse(
            query=params.q,
            page=params.page,
            page_size=params.page_size,
            total_estimated=total,
            total_is_estimate=True,
            results=results,
            sources_status=status,
        )

    @staticmethod
    def _interleave(pages: list[list[RecordOut]]) -> list[RecordOut]:
        """Primeiro de cada fonte, depois o segundo de cada uma, e assim por diante."""
        merged: list[RecordOut] = []
        for index in range(max((len(p) for p in pages), default=0)):
            merged.extend(page[index] for page in pages if index < len(page))
        return merged

    async def _mark_favorites(
        self,
        results: list[RecordOut],
        user_id: uuid.UUID | None,
        favorite_lookup: FavoriteLookup | None,
    ) -> list[RecordOut]:
        """Devolve cópias marcadas; os objetos do conector nunca são alterados."""
        lookup = favorite_lookup or self._favorite_lookup
        if user_id is None or lookup is None or not results:
            return results
        favorites = await lookup(user_id, [r.id for r in results])
        return [r.model_copy(update={"is_favorite": r.id in favorites}) for r in results]

    @classmethod
    def _unavailable(cls, message: str, status: dict[str, SourceStatusOut]) -> UpstreamError:
        """502 com o estado de cada fonte ao lado de "error" (contrato 6.4)."""
        return UpstreamError(
            message,
            details=cls._details(status),
            extra={
                "sources_status": {
                    slug: item.model_dump(mode="json") for slug, item in status.items()
                }
            },
        )

    @staticmethod
    def _details(status: dict[str, SourceStatusOut]) -> list[dict[str, str]]:
        return [
            {"field": slug, "issue": f"{item.status.value}: {item.message or 'sem detalhe'}"}
            for slug, item in status.items()
            if item.message != NOT_SELECTED
        ]


def build_default_service(settings: Settings) -> SearchService:
    """Serviço da aplicação: todos os conectores configurados (OpenAlex, CORE e fontes OAI)."""
    return SearchService(build_connectors(settings), settings)
