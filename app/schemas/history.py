"""Esquemas do histórico de buscas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    query: str
    filters: dict[str, Any]
    result_count_estimated: int | None
    created_at: datetime


class HistoryPage(BaseModel):
    items: list[HistoryOut]
    page: int
    page_size: int
    total: int
