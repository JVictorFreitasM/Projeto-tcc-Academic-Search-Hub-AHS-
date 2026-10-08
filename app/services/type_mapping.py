"""Tabelas de constantes que traduzem o tipo de cada fonte para `RecordType` (6.3)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from app.schemas.common import RecordType
from app.services.normalize import strip_accents

OPENALEX_TYPE_MAP: dict[str, RecordType] = {
    "article": RecordType.ARTICLE,
    "dissertation": RecordType.THESIS,
    "preprint": RecordType.PREPRINT,
    "book": RecordType.BOOK,
    "book-chapter": RecordType.BOOK,
}

CORE_TYPE_MAP: dict[str, RecordType] = {
    "thesis": RecordType.THESIS,
    "research": RecordType.ARTICLE,
    "journal": RecordType.ARTICLE,
    "article": RecordType.ARTICLE,
    "book": RecordType.BOOK,
}

EU_REPO_PREFIX = "info:eu-repo/semantics/"

# Valores comuns de `dc:type` (já sem acento e em minúsculas). O `type_map` de cada fonte,
# em config/oai_sources.yml, tem precedência sobre esta tabela.
OAI_BUILTIN_TYPE_MAP: dict[str, RecordType] = {
    # vocabulário info:eu-repo/semantics
    "article": RecordType.ARTICLE,
    "doctoralthesis": RecordType.THESIS,
    "masterthesis": RecordType.THESIS,
    "bachelorthesis": RecordType.OTHER,  # monografia/TCC
    "book": RecordType.BOOK,
    "bookpart": RecordType.BOOK,
    "preprint": RecordType.PREPRINT,
    "report": RecordType.OTHER,
    "conferenceobject": RecordType.OTHER,
    # texto livre, em português e inglês
    "tese": RecordType.THESIS,
    "dissertacao": RecordType.THESIS,
    "thesis": RecordType.THESIS,
    "dissertation": RecordType.THESIS,
    "doctoral thesis": RecordType.THESIS,
    "master thesis": RecordType.THESIS,
    "artigo": RecordType.ARTICLE,
    "journal article": RecordType.ARTICLE,
    "artigo de periodico": RecordType.ARTICLE,
    "livro": RecordType.BOOK,
    "capitulo de livro": RecordType.BOOK,
    "book chapter": RecordType.BOOK,
    "monografia": RecordType.OTHER,
    "tcc": RecordType.OTHER,
    "trabalho de conclusao de curso": RecordType.OTHER,
}


def _key(value: str) -> str:
    """Compara sem acento, sem caixa e sem o prefixo `info:eu-repo/semantics/`."""
    text = strip_accents(value).strip().lower()
    text = text.removeprefix(EU_REPO_PREFIX.lower())
    return " ".join(text.split())


def map_openalex_type(value: str | None) -> RecordType:
    return OPENALEX_TYPE_MAP.get((value or "").strip().lower(), RecordType.OTHER)


def map_core_type(value: str | None) -> RecordType:
    return CORE_TYPE_MAP.get((value or "").strip().lower(), RecordType.OTHER)


def map_oai_type(
    raw_types: Iterable[str],
    type_map: Mapping[str, str | RecordType],
    default_type: str | RecordType,
) -> RecordType:
    """Tipo de um registro OAI a partir de todos os seus `dc:type`.

    Um tipo específico (artigo, tese, livro, preprint) vence um `other`; se nenhum valor for
    reconhecido (ou a lista for vazia), vale o `default_type` da fonte.
    """
    custom = {_key(k): RecordType(v) for k, v in type_map.items()}
    recognized: list[RecordType] = []
    for raw in raw_types:
        key = _key(raw)
        if not key:
            continue
        found = custom.get(key) or OAI_BUILTIN_TYPE_MAP.get(key)
        if found is not None:
            recognized.append(found)
    for item in recognized:
        if item is not RecordType.OTHER:
            return item
    if recognized:
        return RecordType.OTHER
    return RecordType(default_type)
