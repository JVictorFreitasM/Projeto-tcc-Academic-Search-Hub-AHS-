"""Mapeamento de um registro `oai_dc` para uma linha de `oai_records` (função pura)."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

from app.harvest.oai_client import OaiRecordRaw
from app.harvest.oai_sources import OaiSourceConfig
from app.services.normalize import (
    clean_text,
    normalize_author,
    normalize_doi,
    normalize_language,
    parse_year,
    safe_url,
)
from app.services.type_mapping import map_oai_type

_DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>]+")


def parse_datestamp(value: str | None) -> datetime | None:
    """`2021-05-03` ou `2021-05-03T10:20:30Z` para `datetime` com fuso UTC."""
    if not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _find_doi(values: list[str]) -> str | None:
    for value in values:
        match = _DOI_RE.search(value)
        if match:
            doi = normalize_doi(match.group(0))
            if doi:
                return doi
    return None


def _is_pdf(url: str) -> bool:
    path = urlsplit(url).path.lower()
    return path.endswith(".pdf") or "/bitstream/" in path


def _is_doi_url(url: str) -> bool:
    return urlsplit(url).netloc.lower().endswith("doi.org")


def parse_oai_dc(raw: OaiRecordRaw, source: OaiSourceConfig) -> dict[str, Any] | None:
    """Linha pronta para `oai_records`, ou `None` se o registro não tiver título."""
    dc = raw.dc or {}
    title = next((t for t in (clean_text(v) for v in dc.get("title", [])) if t), "")
    if not title:
        return None

    authors = []
    for creator in dc.get("creator", []):
        author = normalize_author(creator) if clean_text(creator) else None
        if author and author.name:
            authors.append(author.model_dump())

    descriptions = [clean_text(v) for v in dc.get("description", [])]
    abstract = max(descriptions, key=len, default="") or None

    year = next((y for y in (parse_year(v) for v in dc.get("date", [])) if y), None)

    links = dc.get("identifier", []) + dc.get("relation", [])
    doi = _find_doi(links)
    http_links = [u for u in (safe_url(v) for v in links) if u]
    pdf_url = next((u for u in http_links if _is_pdf(u)), None)
    url = next((u for u in http_links if not _is_pdf(u) and not _is_doi_url(u)), None)
    if url is None and doi:
        url = f"https://doi.org/{doi}"

    keywords: list[str] = []
    seen: set[str] = set()
    for subject in dc.get("subject", []):
        word = clean_text(subject)
        if word and word.lower() not in seen:
            seen.add(word.lower())
            keywords.append(word)

    raw_types = list(dc.get("type", []))
    return {
        "source": source.slug,
        "oai_identifier": raw.identifier,
        "datestamp": parse_datestamp(raw.datestamp),
        "deleted": False,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "year": year,
        "doi": doi,
        "url": url,
        "pdf_url": pdf_url,
        "type": map_oai_type(raw_types, source.type_map, source.default_type).value,
        "language": normalize_language(next(iter(dc.get("language", [])), None)),
        "keywords": keywords,
        "raw_types": raw_types,
    }
