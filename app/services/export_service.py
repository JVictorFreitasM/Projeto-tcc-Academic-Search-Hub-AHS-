"""Exportação em BibTeX, RIS, JSON e CSV (geradores próprios, sem biblioteca de bibliografia)."""

from __future__ import annotations

import csv
import io
import json
import re
from collections.abc import Callable
from dataclasses import dataclass

from app.schemas.common import RecordType
from app.schemas.record import RecordOut
from app.services.normalize import strip_accents

PARTICLES = frozenset({"de", "da", "do", "dos", "das", "e", "van", "von", "di", "del", "la", "le"})

_BIBTEX_ESCAPES = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "^": r"\^{}",
    "~": r"\~{}",
}
_BIBTEX_TYPES = {
    RecordType.ARTICLE: "article",
    RecordType.THESIS: "thesis",
    RecordType.BOOK: "book",
    RecordType.PREPRINT: "misc",
    RecordType.OTHER: "misc",
}
_RIS_TYPES = {
    RecordType.ARTICLE: "JOUR",
    RecordType.THESIS: "THES",
    RecordType.BOOK: "BOOK",
    RecordType.PREPRINT: "GEN",
    RecordType.OTHER: "GEN",
}
CSV_HEADER = [
    "id", "title", "authors", "year", "doi", "url", "pdf_url", "type", "language", "keywords",
    "sources",
]  # fmt: skip
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def bibtex_escape(text: str) -> str:
    """Escapa os caracteres especiais do BibTeX (`{ } \\ & % $ # _ ^ ~`)."""
    return "".join(_BIBTEX_ESCAPES.get(ch, ch) for ch in text)


def _bibtex_author(name: str) -> str:
    """ "Nome Sobrenome" vira "Sobrenome, Nome" (partículas como "de" ficam no sobrenome)."""
    name = " ".join(name.split())
    if "," in name or " " not in name:
        return bibtex_escape(name)
    tokens = name.split(" ")
    index = len(tokens) - 1
    while index > 1 and tokens[index - 1].lower() in PARTICLES:
        index -= 1
    given, family = " ".join(tokens[:index]), " ".join(tokens[index:])
    return bibtex_escape(f"{family}, {given}")


def _ascii_key_part(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", strip_accents(text).lower())


def _citation_key(record: RecordOut) -> str:
    surname = ""
    if record.authors:
        first = record.authors[0].name
        family = first.split(",", 1)[0] if "," in first else first.rsplit(" ", 1)[-1]
        surname = _ascii_key_part(family)
    first_word = next((w for w in map(_ascii_key_part, record.title.split()) if len(w) > 2), "")
    return f"{surname or 'anon'}{record.year or 'nd'}{first_word or 'sem'}"


def _unique_keys(records: list[RecordOut]) -> list[str]:
    seen: dict[str, int] = {}
    keys: list[str] = []
    for record in records:
        base = _citation_key(record)
        count = seen.get(base, 0)
        seen[base] = count + 1
        # 1ª ocorrência sem sufixo; depois a, b, c... (z, aa, ab... se passar de 26)
        keys.append(base if count == 0 else base + _letters(count))
    return keys


def _letters(n: int) -> str:
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(ord("a") + remainder) + result
    return result


def to_bibtex(records: list[RecordOut]) -> str:
    entries: list[str] = []
    for record, key in zip(records, _unique_keys(records), strict=True):
        fields: list[tuple[str, str]] = [("title", "{" + bibtex_escape(record.title) + "}")]
        if record.authors:
            fields.append(("author", " and ".join(_bibtex_author(a.name) for a in record.authors)))
        if record.year:
            fields.append(("year", str(record.year)))
        if record.doi:
            fields.append(("doi", bibtex_escape(record.doi)))
        if record.url:
            fields.append(("url", bibtex_escape(record.url)))
        if record.abstract:
            fields.append(("abstract", bibtex_escape(" ".join(record.abstract.split()))))
        if record.keywords:
            fields.append(("keywords", bibtex_escape(", ".join(record.keywords))))
        if record.language:
            fields.append(("language", record.language))
        body = ",\n".join(f"  {name} = {{{value}}}" for name, value in fields)
        entries.append(f"@{_BIBTEX_TYPES[record.type]}{{{key},\n{body}\n}}\n")
    return "\n".join(entries)


def _ris_value(text: str) -> str:
    return " ".join(text.split())


def to_ris(records: list[RecordOut]) -> str:
    lines: list[str] = []
    for record in records:
        lines.append(f"TY  - {_RIS_TYPES[record.type]}")
        lines.append(f"TI  - {_ris_value(record.title)}")
        lines.extend(f"AU  - {_ris_value(a.name)}" for a in record.authors)
        if record.year:
            lines.append(f"PY  - {record.year}")
        if record.doi:
            lines.append(f"DO  - {record.doi}")
        if record.url:
            lines.append(f"UR  - {record.url}")
        if record.abstract:
            lines.append(f"AB  - {_ris_value(record.abstract)}")
        lines.extend(f"KW  - {_ris_value(k)}" for k in record.keywords)
        if record.language:
            lines.append(f"LA  - {record.language}")
        lines.append("ER  - ")
        lines.append("")
    return "\n".join(lines)


def to_json(records: list[RecordOut]) -> str:
    return json.dumps([r.model_dump(mode="json") for r in records], indent=2, ensure_ascii=False)


def csv_safe(value: str) -> str:
    """Neutraliza injeção de fórmula: células que começam com = + - @ tab ou retorno ganham `'`."""
    return "'" + value if value.startswith(FORMULA_PREFIXES) else value


def to_csv(records: list[RecordOut]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=",", quotechar='"', lineterminator="\r\n")
    writer.writerow(CSV_HEADER)
    for r in records:
        row = [
            r.id,
            r.title,
            "; ".join(a.name for a in r.authors),
            "" if r.year is None else str(r.year),
            r.doi or "",
            r.url or "",
            r.pdf_url or "",
            r.type.value,
            r.language or "",
            "; ".join(r.keywords),
            "; ".join(f"{s.source}:{s.source_id}" for s in r.sources),
        ]
        writer.writerow([csv_safe(cell) for cell in row])
    return buffer.getvalue()


@dataclass(frozen=True)
class ExportFormat:
    name: str
    extension: str
    media_type: str
    render: Callable[[list[RecordOut]], str]


FORMATS: dict[str, ExportFormat] = {
    "bibtex": ExportFormat("bibtex", "bib", "application/x-bibtex", to_bibtex),
    "ris": ExportFormat("ris", "ris", "application/x-research-info-systems", to_ris),
    "json": ExportFormat("json", "json", "application/json", to_json),
    "csv": ExportFormat("csv", "csv", "text/csv; charset=utf-8", to_csv),
}
