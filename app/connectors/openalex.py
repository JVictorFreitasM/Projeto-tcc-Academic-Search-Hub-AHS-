"""Conector do OpenAlex (API REST consultada ao vivo)."""

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
    safe_url,
)
from app.services.type_mapping import map_openalex_type

logger = logging.getLogger(__name__)

BASE_URL = "https://api.openalex.org/works"
MAX_PER_PAGE = 100
MAX_ABSTRACT_CHARS = 20_000

# Tipos do OpenAlex que correspondem a cada tipo do sistema (para o filtro `type:`).
_OPENALEX_TYPES: dict[RecordType, tuple[str, ...]] = {
    RecordType.ARTICLE: ("article",),
    RecordType.THESIS: ("dissertation",),
    RecordType.PREPRINT: ("preprint",),
    RecordType.BOOK: ("book", "book-chapter"),
}


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    """Monta o resumo a partir do índice invertido (palavra → posições)."""
    if not inverted_index:
        return None
    positioned: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        positioned.extend((pos, word) for pos in positions if isinstance(pos, int))
    if not positioned:
        return None
    positioned.sort(key=lambda item: item[0])  # posições faltantes são simplesmente puladas
    text = " ".join(word for _, word in positioned)
    return text[:MAX_ABSTRACT_CHARS] or None


def _short_id(uri: str) -> str:
    return uri.rstrip("/").rsplit("/", 1)[-1]


def work_to_record(work: dict[str, Any]) -> RecordOut | None:
    """Converte um *work* do OpenAlex em `RecordOut`; `None` se não tiver título."""
    title = clean_text(work.get("title") or work.get("display_name"))
    uri = work.get("id")
    if not title or not uri:
        return None
    short_id = _short_id(uri)
    doi = normalize_doi(work.get("doi"))

    authors: list[AuthorOut] = []
    for authorship in work.get("authorships") or []:
        author = (authorship or {}).get("author") or {}
        name = author.get("display_name")
        if name and name.strip():
            authors.append(normalize_author(name, author.get("orcid")))

    primary = work.get("primary_location") or {}
    best_oa = work.get("best_oa_location") or {}
    open_access = work.get("open_access") or {}
    url = (
        safe_url(primary.get("landing_page_url"))
        or (safe_url(f"https://doi.org/{doi}") if doi else None)
        or safe_url(open_access.get("oa_url"))
    )
    pdf_url = safe_url(primary.get("pdf_url")) or safe_url(best_oa.get("pdf_url"))

    keywords = [
        clean_text(item.get("display_name"))
        for item in work.get("keywords") or []
        if item and clean_text(item.get("display_name"))
    ]
    year = work.get("publication_year")
    return RecordOut(
        id=build_record_id(doi, "openalex", short_id),
        title=title,
        authors=authors,
        abstract=clean_text(reconstruct_abstract(work.get("abstract_inverted_index"))) or None,
        year=year if isinstance(year, int) and 1000 <= year <= 2100 else None,
        doi=doi,
        url=url,
        pdf_url=pdf_url,
        type=map_openalex_type(work.get("type")),
        language=normalize_language(work.get("language")),
        keywords=keywords,
        sources=[SourceRef(source="openalex", source_id=short_id, url=safe_url(uri))],
    )


def build_filter(query: SourceQuery) -> tuple[str | None, bool]:
    """Monta o parâmetro `filter`. O booleano indica se é preciso filtrar o tipo localmente."""
    parts: list[str] = []
    if query.year_from is not None and query.year_to is not None:
        parts.append(f"publication_year:{query.year_from}-{query.year_to}")
    elif query.year_from is not None:
        parts.append(f"publication_year:>{query.year_from - 1}")
    elif query.year_to is not None:
        parts.append(f"publication_year:<{query.year_to + 1}")

    local_type_filter = False
    if query.types:
        if RecordType.OTHER in query.types:
            # "outros" não tem equivalente no filtro da fonte: filtra-se depois da resposta.
            local_type_filter = True
        else:
            names = [name for t in query.types for name in _OPENALEX_TYPES.get(t, ())]
            if names:
                parts.append("type:" + "|".join(names))
    return (",".join(parts) or None), local_type_filter


class OpenAlexConnector:
    slug = "openalex"
    name = "OpenAlex"
    kind = "api"
    supports_year_sort = True

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client

    def is_enabled(self) -> bool:
        return bool(self._settings.openalex_api_key)

    async def availability(self) -> tuple[bool, str | None]:
        return (True, None) if self.is_enabled() else (False, "Chave do OpenAlex não configurada.")

    async def search(self, query: SourceQuery) -> SourcePage:
        if not self.is_enabled():
            return SourcePage(
                status=SourceStatus.DISABLED, message="Chave do OpenAlex não configurada."
            )
        notes: list[str] = []
        per_page = query.page_size
        if per_page > MAX_PER_PAGE:
            per_page = MAX_PER_PAGE
            notes.append(f"Tamanho de página reduzido para {MAX_PER_PAGE} (limite da fonte).")

        filter_value, local_type_filter = build_filter(query)
        params: dict[str, Any] = {
            "search": query.q,
            "per-page": per_page,
            "page": query.page,
            "api_key": self._settings.openalex_api_key,
        }
        if filter_value:
            params["filter"] = filter_value
        if query.sort == "year_desc":
            params["sort"] = "publication_year:desc"

        try:
            if self._client is not None:
                data = await get_json(self._client, BASE_URL, params)
            else:
                async with make_client(self._settings) as client:
                    data = await get_json(client, BASE_URL, params)
            records = self._parse(data)
            total = int((data.get("meta") or {}).get("count") or 0)
        except Exception as exc:
            return failure_page(
                exc,
                source=self.slug,
                auth_message="Chave do OpenAlex inválida ou sem permissão.",
            )

        if local_type_filter:
            records = [r for r in records if r.type in query.types]
        return SourcePage(
            records=records,
            total=total,
            status=SourceStatus.OK,
            message=" ".join(notes) or None,
        )

    @staticmethod
    def _parse(data: Any) -> list[RecordOut]:
        records: list[RecordOut] = []
        for work in data["results"]:
            record = work_to_record(work)
            if record is not None:
                records.append(record)
        return records
