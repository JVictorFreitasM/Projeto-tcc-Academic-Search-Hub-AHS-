"""Conector do CORE (API v3 consultada ao vivo, chave gratuita em `Authorization: Bearer`)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.connectors.base import SourcePage, SourceQuery, SourceStatus
from app.connectors.errors import failure_page
from app.connectors.http import get_json, make_client
from app.core.config import Settings
from app.schemas.common import RecordType
from app.schemas.record import AuthorOut, RecordOut, SourceRef
from app.services.normalize import (
    build_record_id,
    clean_text,
    normalize_author,
    normalize_doi,
    normalize_language,
    parse_year,
    safe_url,
)
from app.services.type_mapping import map_core_type

logger = logging.getLogger(__name__)

BASE_URL = "https://api.core.ac.uk/v3/search/works/"
WORK_PAGE = "https://core.ac.uk/works/{id}"
MAX_LIMIT = 100  # [VERIFICAR] com chave real

# `documentType` do CORE para cada tipo do sistema. Tipos sem equivalente (preprint, outros)
# não podem ser filtrados na fonte.
_CORE_TYPES: dict[RecordType, tuple[str, ...]] = {
    RecordType.ARTICLE: ("research", "journal", "article"),
    RecordType.THESIS: ("thesis",),
    RecordType.BOOK: ("book",),
}


def build_query_string(query: SourceQuery) -> tuple[str, bool]:
    """Monta o parâmetro `q`. O booleano indica se o tipo precisa ser filtrado localmente."""
    q = "".join(ch for ch in query.q if ch.isprintable()).strip()
    clauses = [f"({q})"]
    if query.year_from is not None:
        clauses.append(f"yearPublished>={query.year_from}")
    if query.year_to is not None:
        clauses.append(f"yearPublished<={query.year_to}")

    local_type_filter = False
    if query.types:
        if all(t in _CORE_TYPES for t in query.types):
            names = [f'documentType:"{name}"' for t in query.types for name in _CORE_TYPES[t]]
            clauses.append("(" + " OR ".join(names) + ")")
        else:
            local_type_filter = True
    return " AND ".join(clauses), local_type_filter


def work_to_record(work: dict[str, Any]) -> RecordOut | None:
    """Converte um resultado do CORE em `RecordOut`; `None` se não tiver título."""
    title = clean_text(work.get("title"))
    core_id = work.get("id")
    if not title or core_id is None:
        return None
    core_id = str(core_id)
    doi = normalize_doi(work.get("doi"))
    core_page = safe_url(WORK_PAGE.format(id=core_id))

    authors: list[AuthorOut] = []
    for author in work.get("authors") or []:
        name = (author or {}).get("name")
        if name and name.strip():
            authors.append(normalize_author(name))

    landing = None
    for link in work.get("links") or []:
        if (link or {}).get("type") == "display":
            landing = safe_url(link.get("url"))
            break
    fulltext = next(
        (u for u in (safe_url(x) for x in work.get("sourceFulltextUrls") or []) if u), None
    )
    language = work.get("language")
    language_code = language.get("code") if isinstance(language, dict) else language
    year = work.get("yearPublished")
    if not (isinstance(year, int) and 1000 <= year <= 2100):
        year = parse_year(work.get("publishedDate"))

    return RecordOut(
        id=build_record_id(doi, "core", core_id),
        title=title,
        authors=authors,
        abstract=clean_text(work.get("abstract")) or None,
        year=year,
        doi=doi,
        url=landing or fulltext or core_page,
        pdf_url=safe_url(work.get("downloadUrl")),
        type=map_core_type(work.get("documentType")),
        language=normalize_language(language_code),
        keywords=[],
        sources=[SourceRef(source="core", source_id=core_id, url=core_page)],
    )


class CoreConnector:
    slug = "core"
    name = "CORE"
    kind = "api"
    # O CORE não ordena por ano: o orquestrador ordena a página combinada (6.4).
    supports_year_sort = False

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client

    def is_enabled(self) -> bool:
        return bool(self._settings.core_api_key)

    async def availability(self) -> tuple[bool, str | None]:
        return (True, None) if self.is_enabled() else (False, "Chave do CORE não configurada.")

    async def search(self, query: SourceQuery) -> SourcePage:
        if not self.is_enabled():
            return SourcePage(
                status=SourceStatus.DISABLED, message="Chave do CORE não configurada."
            )
        notes: list[str] = []
        limit = query.page_size
        if limit > MAX_LIMIT:
            limit = MAX_LIMIT
            notes.append(f"Tamanho de página reduzido para {MAX_LIMIT} (limite da fonte).")

        q, local_type_filter = build_query_string(query)
        params = {"q": q, "limit": limit, "offset": (query.page - 1) * limit}
        headers = {"Authorization": f"Bearer {self._settings.core_api_key}"}

        try:
            if self._client is not None:
                data = await get_json(self._client, BASE_URL, params, headers)
            else:
                async with make_client(self._settings) as client:
                    data = await get_json(client, BASE_URL, params, headers)
            records: list[RecordOut] = []
            ignored = 0
            for work in data["results"]:
                record = work_to_record(work)
                if record is None:
                    ignored += 1
                else:
                    records.append(record)
            total = int(data.get("totalHits") or 0)
        except Exception as exc:
            return failure_page(
                exc,
                source=self.slug,
                auth_message="Chave do CORE inválida ou sem permissão.",
            )

        if ignored:
            notes.append(f"{ignored} resultados sem título foram ignorados.")
        if local_type_filter:
            records = [r for r in records if r.type in query.types]
        return SourcePage(
            records=records,
            total=total,
            status=SourceStatus.OK,
            message=" ".join(notes) or None,
        )
