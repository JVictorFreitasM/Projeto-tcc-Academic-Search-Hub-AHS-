"""Conector das fontes OAI-PMH: busca de texto completo sobre o índice local `oai_records`."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import ColumnElement, case, cast, func, literal, select
from sqlalchemy.dialects.postgresql import REGCONFIG
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.connectors.base import SourcePage, SourceQuery, SourceStatus
from app.connectors.errors import failure_page
from app.models import OaiRecord
from app.schemas.common import RecordType
from app.schemas.record import AuthorOut, RecordOut, SourceRef
from app.services.normalize import build_record_id, clean_text, normalize_doi, safe_url

logger = logging.getLogger(__name__)

NOT_HARVESTED = "Fonte ainda não colhida"
STOPWORDS_ONLY = "A consulta só tem palavras comuns demais para a busca local; tente outros termos."
TS_CONFIG = "pt_unaccent"


def to_record(row: OaiRecord, slug: str) -> RecordOut:
    """Converte uma linha do índice local em `RecordOut`."""
    doi = normalize_doi(row.doi)
    authors = [
        AuthorOut(name=item["name"], orcid=item.get("orcid"))
        for item in row.authors or []
        if isinstance(item, dict) and item.get("name")
    ]
    return RecordOut(
        id=build_record_id(doi, slug, row.oai_identifier),
        title=clean_text(row.title) or row.title,
        authors=authors,
        abstract=row.abstract,
        year=row.year,
        doi=doi,
        url=safe_url(row.url),
        pdf_url=safe_url(row.pdf_url),
        type=RecordType(row.type),
        language=row.language,
        keywords=[str(k) for k in row.keywords or []],
        sources=[SourceRef(source=slug, source_id=row.oai_identifier, url=safe_url(row.url))],
    )


class OaiLocalConnector:
    """Uma instância por fonte OAI (`slug`) declarada em `config/oai_sources.yml`."""

    supports_year_sort = True

    def __init__(
        self,
        slug: str,
        name: str,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        enabled: bool = True,
    ) -> None:
        self.slug = slug
        self.name = name
        self._session_factory = session_factory
        self._enabled = enabled

    def is_enabled(self) -> bool:
        return self._enabled

    async def _has_records(self, session: AsyncSession) -> bool:
        found = await session.execute(
            select(OaiRecord.id)
            .where(OaiRecord.source == self.slug, OaiRecord.deleted.is_(False))
            .limit(1)
        )
        return found.first() is not None

    async def availability(self) -> tuple[bool, str | None]:
        if not self._enabled:
            return False, NOT_HARVESTED
        try:
            async with self._session_factory() as session:
                has = await self._has_records(session)
        except Exception:
            logger.error("Falha ao consultar o índice local", extra={"source": self.slug})
            return False, "Índice local indisponível."
        return (True, None) if has else (False, NOT_HARVESTED)

    def _filters(
        self, query: SourceQuery, ts_query: ColumnElement[Any]
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = [
            OaiRecord.source == self.slug,
            OaiRecord.deleted.is_(False),
            OaiRecord.search_vector.op("@@")(ts_query),
        ]
        # Com filtro de ano, registros sem ano ficam de fora (year NULL nunca satisfaz o filtro).
        if query.year_from is not None:
            conditions.append(OaiRecord.year >= query.year_from)
        if query.year_to is not None:
            conditions.append(OaiRecord.year <= query.year_to)
        if query.types:
            conditions.append(OaiRecord.type.in_([t.value for t in query.types]))
        return conditions

    async def search(self, query: SourceQuery) -> SourcePage:
        if not self._enabled:
            return SourcePage(status=SourceStatus.DISABLED, message=NOT_HARVESTED)
        try:
            async with self._session_factory() as session:
                if not await self._has_records(session):
                    return SourcePage(status=SourceStatus.DISABLED, message=NOT_HARVESTED)
                return await self._search(session, query)
        except Exception as exc:
            return failure_page(exc, source=self.slug, auth_message="Índice local indisponível.")

    async def _search(self, session: AsyncSession, query: SourceQuery) -> SourcePage:
        # Texto do usuário só entra como parâmetro ligado (nunca concatenado ao SQL).
        ts_query = func.websearch_to_tsquery(cast(literal(TS_CONFIG), REGCONFIG), query.q)
        if (await session.execute(select(func.numnode(ts_query)))).scalar_one() == 0:
            return SourcePage(records=[], total=0, status=SourceStatus.OK, message=STOPWORDS_ONLY)

        conditions = self._filters(query, ts_query)
        total = (
            await session.execute(select(func.count()).select_from(OaiRecord).where(*conditions))
        ).scalar_one()

        rank = func.ts_rank_cd(OaiRecord.search_vector, ts_query)
        year_last = case((OaiRecord.year.is_(None), 1), else_=0)
        order: tuple[Any, ...]
        if query.sort == "year_desc":
            order = (year_last, OaiRecord.year.desc(), rank.desc(), OaiRecord.id)
        else:
            order = (rank.desc(), year_last, OaiRecord.year.desc(), OaiRecord.id)
        statement = (
            select(OaiRecord)
            .where(*conditions)
            .order_by(*order)
            .limit(query.page_size)
            .offset((query.page - 1) * query.page_size)
        )
        rows = (await session.execute(statement)).scalars().all()
        records = [to_record(row, self.slug) for row in rows]
        return SourcePage(records=records, total=total, status=SourceStatus.OK)
