"""Agrega os roteadores da API v1."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, favorites, health, search
from app.schemas.common import ErrorResponse

ERROR_RESPONSES: dict[int | str, dict[str, object]] = {
    422: {"model": ErrorResponse, "description": "Dados inválidos"},
    429: {"model": ErrorResponse, "description": "Limite de requisições atingido"},
    500: {"model": ErrorResponse, "description": "Erro interno"},
}

api_router = APIRouter(responses=ERROR_RESPONSES)
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(search.router)
api_router.include_router(favorites.router)
