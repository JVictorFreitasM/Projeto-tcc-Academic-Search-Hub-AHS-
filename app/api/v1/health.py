"""Verificação de saúde."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app import __version__
from app.db.session import check_database

router = APIRouter(tags=["Saúde"])


class HealthOut(BaseModel):
    status: Literal["ok"] = "ok"
    database: Literal["ok", "error"]
    version: str


@router.get(
    "/health",
    response_model=HealthOut,
    summary="Verifica se a API e o banco de dados estão respondendo",
)
async def health() -> HealthOut:
    """Responde 200 mesmo com o banco fora do ar (`database: error`), sem detalhes do erro."""
    if await check_database():
        return HealthOut(database="ok", version=__version__)
    return HealthOut(database="error", version=__version__)
