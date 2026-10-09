"""Parâmetros e resposta da busca unificada (6.4)."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_serializer, model_validator

from app.connectors.base import SourceStatus
from app.core.config import get_settings
from app.schemas.common import RecordType
from app.schemas.record import RecordOut

MIN_QUERY_LENGTH = 2
MAX_QUERY_LENGTH = 200
MIN_YEAR_FILTER = 1900
SORT_VALUES = ("relevance", "year_desc")


class SearchParams(BaseModel):
    """Parâmetros validados da busca."""

    q: str
    sources: list[str] | None = None
    year_from: int | None = None
    year_to: int | None = None
    types: list[RecordType] | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1)
    sort: str = "relevance"

    @field_validator("q")
    @classmethod
    def _query_length(cls, value: str) -> str:
        value = value.strip()
        if not MIN_QUERY_LENGTH <= len(value) <= MAX_QUERY_LENGTH:
            raise ValueError(
                f"a consulta deve ter de {MIN_QUERY_LENGTH} a {MAX_QUERY_LENGTH} caracteres"
            )
        return value

    @field_validator("year_from", "year_to")
    @classmethod
    def _year_range(cls, value: int | None) -> int | None:
        max_year = date.today().year + 1
        if value is not None and not MIN_YEAR_FILTER <= value <= max_year:
            raise ValueError(f"o ano deve estar entre {MIN_YEAR_FILTER} e {max_year}")
        return value

    @field_validator("sort")
    @classmethod
    def _sort_value(cls, value: str) -> str:
        if value not in SORT_VALUES:
            raise ValueError("a ordenação deve ser: " + ", ".join(SORT_VALUES))
        return value

    @model_validator(mode="after")
    def _cross_checks(self) -> Self:
        if (
            self.year_from is not None
            and self.year_to is not None
            and self.year_from > self.year_to
        ):
            raise ValueError("year_from deve ser menor ou igual a year_to")
        max_size = get_settings().max_page_size
        if self.page_size > max_size:
            raise ValueError(f"page_size deve ser no máximo {max_size}")
        return self


class SourceInfo(BaseModel):
    """Estado público de uma fonte (rota /sources)."""

    slug: str
    name: str
    kind: Literal["api", "oai"]
    enabled: bool
    status: Literal["ok", "disabled"]
    message: str | None = None


class SourceStatusOut(BaseModel):
    status: SourceStatus
    count: int = 0
    total: int | None = 0
    message: str | None = None
    duration_ms: int | None = None

    @model_serializer(mode="wrap")
    def _drop_empty_duration(self, handler: Any) -> dict[str, Any]:
        data: dict[str, Any] = handler(self)
        if data.get("duration_ms") is None:
            data.pop("duration_ms", None)
        return data


class SearchResponse(BaseModel):
    query: str
    page: int
    page_size: int
    total_estimated: int
    total_is_estimate: bool = True
    results: list[RecordOut]
    sources_status: dict[str, SourceStatusOut]
