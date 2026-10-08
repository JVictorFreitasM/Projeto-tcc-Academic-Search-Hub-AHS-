"""Esquema unificado `Record` (6.2): a resposta pública de todos os conectores."""

from __future__ import annotations

from typing import Annotated
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import RecordType

MIN_YEAR = 1000
MAX_YEAR = 2100


def is_http_url(value: str) -> bool:
    """`True` só para endereços `http`/`https` com host, sem espaços ou controles."""
    if not value or any(ch.isspace() or ord(ch) < 32 for ch in value):
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


class AuthorOut(BaseModel):
    name: str = Field(min_length=1)
    orcid: str | None = None


class SourceRef(BaseModel):
    source: str = Field(min_length=1, description="Slug da fonte (openalex, core, bdtd...)")
    source_id: str = Field(min_length=1)
    url: str | None = None

    @field_validator("url")
    @classmethod
    def _http_only(cls, value: str | None) -> str | None:
        if value is not None and not is_http_url(value):
            raise ValueError("url deve usar http ou https")
        return value


class RecordOut(BaseModel):
    """Trabalho acadêmico em formato único, independente da fonte."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "doi:10.1000/exemplo",
                    "title": "Letramento digital na educação básica",
                    "authors": [{"name": "Maria Souza", "orcid": None}],
                    "abstract": "Resumo do trabalho.",
                    "year": 2021,
                    "doi": "10.1000/exemplo",
                    "url": "https://exemplo.org/trabalho/1",
                    "pdf_url": None,
                    "type": "article",
                    "language": "pt",
                    "keywords": ["educação", "tecnologia"],
                    "sources": [
                        {
                            "source": "openalex",
                            "source_id": "W123",
                            "url": "https://openalex.org/W123",
                        }
                    ],
                    "is_favorite": False,
                }
            ]
        }
    )

    id: str = Field(min_length=1, description="doi:<doi> ou src:<fonte>:<id na fonte>")
    title: str
    authors: list[AuthorOut] = Field(default_factory=list)
    abstract: str | None = None
    year: Annotated[int, Field(ge=MIN_YEAR, le=MAX_YEAR)] | None = None
    doi: str | None = None
    url: str | None = None
    pdf_url: str | None = None
    type: RecordType = RecordType.OTHER
    language: str | None = Field(default=None, pattern=r"^[a-z]{2}$")
    keywords: list[str] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)
    is_favorite: bool = False

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("title é obrigatório")
        return value

    @field_validator("url", "pdf_url")
    @classmethod
    def _http_only(cls, value: str | None) -> str | None:
        if value is not None and not is_http_url(value):
            raise ValueError("endereço deve usar http ou https")
        return value
