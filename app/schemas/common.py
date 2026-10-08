"""Tipos compartilhados entre esquemas e modelos."""

from __future__ import annotations

from enum import StrEnum


class RecordType(StrEnum):
    """Tipo de publicação (6.3)."""

    ARTICLE = "article"
    THESIS = "thesis"
    PREPRINT = "preprint"
    BOOK = "book"
    OTHER = "other"


RECORD_TYPE_VALUES = tuple(item.value for item in RecordType)
