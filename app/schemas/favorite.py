"""Esquemas de favoritos."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.record import RecordOut

MAX_NOTE_LENGTH = 1000


def _clean_note(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


class FavoriteCreate(BaseModel):
    record: RecordOut
    note: str | None = Field(default=None, max_length=MAX_NOTE_LENGTH)

    _note = field_validator("note")(_clean_note)


class FavoriteUpdate(BaseModel):
    note: str | None = Field(default=None, max_length=MAX_NOTE_LENGTH)

    _note = field_validator("note")(_clean_note)


class FavoriteOut(BaseModel):
    id: uuid.UUID
    record: RecordOut
    note: str | None
    created_at: datetime


class FavoritePage(BaseModel):
    items: list[FavoriteOut]
    page: int
    page_size: int
    total: int
