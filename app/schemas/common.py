"""Tipos compartilhados entre esquemas e modelos."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class RecordType(StrEnum):
    """Tipo de publicação (6.3)."""

    ARTICLE = "article"
    THESIS = "thesis"
    PREPRINT = "preprint"
    BOOK = "book"
    OTHER = "other"


RECORD_TYPE_VALUES = tuple(item.value for item in RecordType)


class ErrorDetail(BaseModel):
    field: str = Field(description="Campo ou fonte a que o problema se refere")
    issue: str = Field(description="Descrição do problema")


class ErrorBody(BaseModel):
    code: str = Field(description="Código em snake_case", examples=["validation_error"])
    message: str = Field(description="Mensagem em português para o usuário")
    details: list[ErrorDetail] | None = None


class ErrorResponse(BaseModel):
    """Formato padrão de erro (6.5)."""

    error: ErrorBody
