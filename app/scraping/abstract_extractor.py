"""Extração do resumo de uma página HTML, em ordem de preferência (sem heurística de parágrafo)."""

from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup, Tag

from app.services.normalize import clean_text

MIN_OG_LENGTH = 200
MAX_ABSTRACT_CHARS = 10_000
_SCHOLARLY_TYPES = {"ScholarlyArticle"}


def _meta_values(soup: BeautifulSoup, attr: str, names: set[str]) -> list[str]:
    values: list[str] = []
    for tag in soup.find_all("meta"):
        if not isinstance(tag, Tag):
            continue
        key = tag.get(attr)
        content = tag.get("content")
        if isinstance(key, str) and key.strip().lower() in names and isinstance(content, str):
            text = clean_text(content)
            if text:
                values.append(text)
    return values


def _longest(values: list[str]) -> str | None:
    return max(values, key=len) if values else None


def _walk(node: Any) -> list[dict[str, Any]]:
    """Todos os objetos de um JSON-LD (inclusive dentro de listas e de `@graph`)."""
    found: list[dict[str, Any]] = []
    if isinstance(node, dict):
        found.append(node)
        for value in node.values():
            if isinstance(value, dict | list):
                found.extend(_walk(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_walk(item))
    return found


def _is_scholarly(obj: dict[str, Any]) -> bool:
    kind = obj.get("@type")
    kinds = kind if isinstance(kind, list) else [kind]
    return any(k in _SCHOLARLY_TYPES for k in kinds if isinstance(k, str))


def _from_json_ld(soup: BeautifulSoup) -> str | None:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.get_text())
        except ValueError:
            continue
        for obj in _walk(data):
            if not _is_scholarly(obj):
                continue
            for field in ("abstract", "description"):
                value = obj.get(field)
                if isinstance(value, str) and clean_text(value):
                    return clean_text(value)
    return None


def extract_abstract(html: str) -> str | None:
    """Resumo da página ou `None`.

    Ordem: `citation_abstract`; `DC.description`/`dc.description`; `og:description` (só com
    200+ caracteres); JSON-LD de um `ScholarlyArticle` (`abstract` ou `description`).
    """
    soup = BeautifulSoup(html, "html.parser")
    candidate = (
        _longest(_meta_values(soup, "name", {"citation_abstract"}))
        or _longest(_meta_values(soup, "name", {"dc.description", "dcterms.abstract"}))
        or next(
            (
                text
                for text in _meta_values(soup, "property", {"og:description"})
                if len(text) >= MIN_OG_LENGTH
            ),
            None,
        )
        or _from_json_ld(soup)
    )
    return candidate[:MAX_ABSTRACT_CHARS] if candidate else None
