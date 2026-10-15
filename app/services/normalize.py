"""Funções puras de normalização compartilhadas por todos os conectores."""

from __future__ import annotations

import html
import re
import unicodedata

from app.schemas.record import MAX_YEAR, MIN_YEAR, AuthorOut, is_http_url

_DOI_PREFIX_RE = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.IGNORECASE)
_TAG_RE = re.compile(r"</?[A-Za-z][^<>]*>|<!--.*?-->", re.DOTALL)
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_YEAR_RE = re.compile(r"(?<!\d)(\d{4})(?!\d)")
_ORCID_PREFIX_RE = re.compile(r"^https?://orcid\.org/", re.IGNORECASE)

# ISO 639-3 -> ISO 639-1 para os idiomas esperados nas fontes.
_LANG_3_TO_2 = {
    "por": "pt",
    "eng": "en",
    "spa": "es",
    "fra": "fr",
    "fre": "fr",
    "deu": "de",
    "ger": "de",
    "ita": "it",
    "lat": "la",
    "nld": "nl",
    "dut": "nl",
    "rus": "ru",
    "zho": "zh",
    "chi": "zh",
    "jpn": "ja",
}
_KNOWN_LANG_2 = frozenset(_LANG_3_TO_2.values()) | {"ca", "pl", "sv", "tr", "ar", "ko", "el"}


def normalize_doi(value: str | None) -> str | None:
    """DOI em minúsculas, sem prefixo de URL nem `doi:`; `None` se não for um DOI."""
    if not value:
        return None
    text = _DOI_PREFIX_RE.sub("", value.strip()).strip().rstrip(".,;")
    text = text.lower()
    if not text.startswith("10.") or "/" not in text or any(ch.isspace() for ch in text):
        return None
    return text


def clean_text(value: str | None) -> str:
    """Remove tags HTML, decodifica entidades e colapsa espaços e quebras de linha."""
    if not value:
        return ""
    text = _TAG_RE.sub(" ", value)
    text = html.unescape(text)
    text = _TAG_RE.sub(" ", text)  # tags que vieram codificadas como entidades
    text = _CONTROL_RE.sub(" ", text)
    return " ".join(text.split())


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize_title(value: str | None) -> str:
    """Título para comparação: minúsculas, sem acento, sem pontuação, espaços únicos."""
    text = strip_accents(clean_text(value)).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def parse_year(value: object) -> int | None:
    """Ano entre 1000 e 2100 a partir de número ou texto (`2021-05-03`, `[2019]`...)."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if MIN_YEAR <= value <= MAX_YEAR else None
    for match in _YEAR_RE.finditer(str(value)):
        year = int(match.group(1))
        if MIN_YEAR <= year <= MAX_YEAR:
            return year
    return None


def _normalize_orcid(value: str | None) -> str | None:
    if not value:
        return None
    text = _ORCID_PREFIX_RE.sub("", value.strip()).strip()
    return text or None


def normalize_author(name: str | None, orcid: str | None = None) -> AuthorOut:
    """ "Sobrenome, Nome" vira "Nome Sobrenome"; formas ambíguas ficam como vieram."""
    text = " ".join(clean_text(name).split())
    if text.count(",") == 1:
        family, given = (part.strip() for part in text.split(","))
        if family and given:
            if family.isupper():
                family = family.title()
            text = f"{given} {family}"
    return AuthorOut(name=text, orcid=_normalize_orcid(orcid))


def surname(author_name: str | None) -> str:
    """Sobrenome normalizado (minúsculo, sem acento) para a regra de deduplicação."""
    text = " ".join(clean_text(author_name).split())
    if not text:
        return ""
    family = text.split(",", 1)[0] if "," in text else text.rsplit(" ", 1)[-1]
    return normalize_title(family)


def normalize_language(value: str | None) -> str | None:
    """Código ISO 639-1 em minúsculas (`por` -> `pt`, `pt-BR` -> `pt`); desconhecido -> `None`."""
    if not value:
        return None
    code = re.split(r"[-_]", value.strip().lower())[0]
    code = _LANG_3_TO_2.get(code, code)
    return code if code in _KNOWN_LANG_2 else None


def safe_url(value: str | None) -> str | None:
    """Só `http`/`https`; descarta `javascript:`, `data:` e similares."""
    if not value:
        return None
    # Algumas fontes devolvem o endereço com `&amp;` escapado como HTML (visto no OpenAlex em
    # 15/10/2026: `...sci_arttext&amp;pid=...`), o que quebraria o parâmetro `pid`.
    text = value.strip().replace("&amp;", "&")
    return text if is_http_url(text) else None


def build_record_id(doi: str | None, source: str, source_id: str) -> str:
    """`doi:<doi>` quando há DOI válido; senão `src:<fonte>:<id na fonte>`."""
    normalized = normalize_doi(doi)
    if normalized:
        return f"doi:{normalized}"
    return f"src:{source}:{source_id}"
