"""Deduplicação de registros vindos de fontes diferentes (Zeng e Chan, 2006).

Duas chaves, nesta ordem: (1) DOI normalizado; (2) título normalizado + ano + sobrenome do
primeiro autor. Sem similaridade difusa. Complexidade linear (dicionários, sem comparar pares).
"""

from __future__ import annotations

from app.schemas.common import RecordType
from app.schemas.record import AuthorOut, RecordOut, SourceRef
from app.services.normalize import build_record_id, normalize_doi, normalize_title, surname

MIN_TITLE_LENGTH = 15


def doi_key(record: RecordOut) -> str | None:
    doi = normalize_doi(record.doi)
    return f"doi:{doi}" if doi else None


def title_key(record: RecordOut) -> str | None:
    """Chave 2. Só existe com título normalizado de 15+ caracteres, ano e primeiro autor."""
    title = normalize_title(record.title)
    if len(title) < MIN_TITLE_LENGTH or record.year is None or not record.authors:
        return None
    first = surname(record.authors[0].name)
    if not first:
        return None
    return f"title:{title}|{record.year}|{first}"


def _first(*values: str | int | None) -> str | int | None:
    return next((v for v in values if v is not None), None)


def _richer_authors(base: list[AuthorOut], other: list[AuthorOut]) -> list[AuthorOut]:
    if len(other) != len(base):
        return other if len(other) > len(base) else base
    with_orcid = sum(1 for a in other if a.orcid) > sum(1 for a in base if a.orcid)
    return other if with_orcid else base


def _union(first: list[str], second: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for item in [*first, *second]:
        key = item.casefold()
        if key not in seen:
            seen.add(key)
            merged.append(item)
    return merged


def _union_sources(first: list[SourceRef], second: list[SourceRef]) -> list[SourceRef]:
    seen: set[tuple[str, str]] = set()
    merged: list[SourceRef] = []
    for ref in [*first, *second]:
        key = (ref.source, ref.source_id)
        if key not in seen:
            seen.add(key)
            merged.append(ref)
    return merged


def merge(base: RecordOut, other: RecordOut) -> RecordOut:
    """Une `other` em `base` (a primeira ocorrência manda) conforme as regras da OS-011."""
    abstracts = [a for a in (base.abstract, other.abstract) if a]
    record_type = base.type
    if base.type is RecordType.OTHER and other.type is not RecordType.OTHER:
        record_type = other.type
    sources = _union_sources(base.sources, other.sources)
    doi = _first(base.doi, other.doi)
    merged = base.model_copy(
        update={
            "abstract": max(abstracts, key=len) if abstracts else None,
            "doi": doi,
            "year": _first(base.year, other.year),
            "language": _first(base.language, other.language),
            "url": _first(base.url, other.url),
            "pdf_url": _first(base.pdf_url, other.pdf_url),
            "authors": _richer_authors(base.authors, other.authors),
            "keywords": _union(base.keywords, other.keywords),
            "type": record_type,
            "sources": sources,
        }
    )
    if sources:
        merged.id = build_record_id(merged.doi, sources[0].source, sources[0].source_id)
    return merged


def _conflicting_dois(a: RecordOut, b: RecordOut) -> bool:
    first, second = normalize_doi(a.doi), normalize_doi(b.doi)
    return bool(first and second and first != second)


def deduplicate(records: list[RecordOut]) -> list[RecordOut]:
    """Reúne duplicatas mantendo a ordem da primeira ocorrência (estável e idempotente)."""
    groups: list[RecordOut] = []
    by_doi: dict[str, int] = {}
    by_title: dict[str, int] = {}

    for record in records:
        key_doi, key_title = doi_key(record), title_key(record)
        target = by_doi.get(key_doi) if key_doi else None
        if target is None and key_title is not None:
            candidate = by_title.get(key_title)
            # DOIs diferentes são trabalhos diferentes, mesmo com o mesmo título.
            if candidate is not None and not _conflicting_dois(groups[candidate], record):
                target = candidate

        if target is None:
            groups.append(record)
            target = len(groups) - 1
        else:
            groups[target] = merge(groups[target], record)

        current = groups[target]
        if (key := doi_key(current)) is not None:
            by_doi.setdefault(key, target)
        if (key := title_key(current)) is not None:
            by_title.setdefault(key, target)
    return groups
