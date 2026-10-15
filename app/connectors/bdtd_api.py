"""Conector da BDTD (API REST pública do VuFind, consultada ao vivo, sem chave).

O OAI-PMH da BDTD não está disponível (404 em 15/10/2026), mas a API de busca do VuFind
responde com tema, autor, ano, tipo, ordenação por ano e paginação (testado na mesma data).
"""

from __future__ import annotations

import logging
import re
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
    normalize_language,
    parse_year,
    safe_url,
)
from app.services.type_mapping import map_bdtd_type

logger = logging.getLogger(__name__)

BASE_URL = "https://bdtd.ibict.br/vufind/api/v1/search"
RECORD_PAGE = "https://bdtd.ibict.br/vufind/Record/{id}"
MAX_LIMIT = 100  # limite padrão do VuFind; só foram testados valores até 5
MAX_KEYWORDS = 10
_INSTITUTION_TAG_RE = re.compile(r"\s*\[[^\]]*\]")  # "Almeida, Regiceli Bento [UNESP]"
FIELDS = (
    "id",
    "title",
    "primaryAuthors",
    "publicationDates",
    "summary",
    "languages",
    "formats",
    "urls",
    "subjects",
)


def build_params(query: SourceQuery, limit: int) -> list[tuple[str, str]]:
    """Parâmetros da busca. A BDTD só tem teses e dissertações: o tipo não vira filtro na fonte."""
    q = "".join(ch for ch in query.q if ch.isprintable()).strip()
    params: list[tuple[str, str]] = [
        ("lookfor", q),
        ("type", "Author" if query.field == "author" else "AllFields"),
        ("limit", str(limit)),
        ("page", str(query.page)),
    ]
    if query.year_from is not None or query.year_to is not None:
        start = query.year_from if query.year_from is not None else "*"
        end = query.year_to if query.year_to is not None else "*"
        params.append(("filter[]", f"publishDate:[{start} TO {end}]"))
    if query.sort == "year_desc":
        params.append(("sort", "year"))  # no VuFind, `year` é do mais novo para o mais antigo
    params.extend(("field[]", name) for name in FIELDS)
    return params


def _author_name(raw: str) -> str:
    """Tira a sigla da instituição entre colchetes; nome todo em maiúsculas vira só iniciais."""
    name = _INSTITUTION_TAG_RE.sub("", raw).strip()
    return name.title() if name.isupper() else name


def _keywords(subjects: object) -> list[str]:
    found: list[str] = []
    for item in subjects if isinstance(subjects, list) else []:
        for value in item if isinstance(item, list) else [item]:
            text = clean_text(value if isinstance(value, str) else None)
            # "CNPQ::CIENCIAS HUMANAS::..." é a área do CNPq, não uma palavra-chave
            if text and "::" not in text and text not in found:
                found.append(text)
    return found[:MAX_KEYWORDS]


def record_to_out(item: dict[str, Any]) -> RecordOut | None:
    """Converte um registro do VuFind em `RecordOut`; `None` se não tiver título ou id."""
    title = clean_text(item.get("title"))
    bdtd_id = item.get("id")
    if not title or not bdtd_id:
        return None
    bdtd_id = str(bdtd_id)
    page = safe_url(RECORD_PAGE.format(id=bdtd_id))

    authors: list[AuthorOut] = [
        normalize_author(_author_name(name))
        for name in item.get("primaryAuthors") or []
        if isinstance(name, str) and _author_name(name)
    ]
    summaries = [clean_text(s) for s in item.get("summary") or [] if isinstance(s, str)]
    landing = next(
        (u for u in (safe_url((link or {}).get("url")) for link in item.get("urls") or []) if u),
        None,
    )
    languages = item.get("languages") or []
    formats = item.get("formats") or []

    return RecordOut(
        id=build_record_id(None, "bdtd", bdtd_id),
        title=title,
        authors=authors,
        abstract=next((s for s in summaries if s), None),
        year=parse_year(next(iter(item.get("publicationDates") or []), None)),
        doi=None,
        url=landing or page,
        pdf_url=None,
        type=map_bdtd_type(formats[0] if formats else None),
        language=normalize_language(languages[0] if languages else None),
        keywords=_keywords(item.get("subjects")),
        sources=[SourceRef(source="bdtd", source_id=bdtd_id, url=page)],
    )


class BdtdConnector:
    slug = "bdtd"
    name = "BDTD (IBICT)"
    kind = "api"
    supports_year_sort = True

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client

    def is_enabled(self) -> bool:
        return self._settings.bdtd_enabled

    async def availability(self) -> tuple[bool, str | None]:
        return (True, None) if self.is_enabled() else (False, "Fonte desligada na configuração.")

    async def search(self, query: SourceQuery) -> SourcePage:
        if not self.is_enabled():
            return SourcePage(
                status=SourceStatus.DISABLED, message="Fonte desligada na configuração."
            )
        if query.types and RecordType.THESIS not in query.types:
            # A BDTD só tem teses e dissertações: outro tipo nunca dá resultado.
            return SourcePage(records=[], total=0, status=SourceStatus.OK)
        notes: list[str] = []
        limit = query.page_size
        if limit > MAX_LIMIT:
            limit = MAX_LIMIT
            notes.append(f"Tamanho de página reduzido para {MAX_LIMIT} (limite da fonte).")
        params = httpx.QueryParams(tuple(build_params(query, limit)))  # `field[]` se repete

        try:
            if self._client is not None:
                data = await get_json(self._client, BASE_URL, params, {})
            else:
                async with make_client(self._settings) as client:
                    data = await get_json(client, BASE_URL, params, {})
            if data.get("status") != "OK":
                raise ValueError("status da BDTD diferente de OK")
            records: list[RecordOut] = []
            ignored = 0
            for item in data.get("records") or []:  # sem resultado, a chave `records` não vem
                record = record_to_out(item)
                if record is None:
                    ignored += 1
                else:
                    records.append(record)
            total = int(data.get("resultCount") or 0)
        except Exception as exc:
            return failure_page(
                exc, source=self.slug, auth_message="A BDTD recusou o acesso à API."
            )

        if ignored:
            notes.append(f"{ignored} resultados sem título foram ignorados.")
        return SourcePage(
            records=records, total=total, status=SourceStatus.OK, message=" ".join(notes) or None
        )
