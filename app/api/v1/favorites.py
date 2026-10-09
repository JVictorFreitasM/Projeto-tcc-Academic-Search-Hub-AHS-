"""Favoritos do usuário autenticado."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Query, Response

from app.api.deps import CurrentUser, SessionDep, SettingsDep
from app.schemas.common import ErrorResponse
from app.schemas.favorite import FavoriteCreate, FavoriteOut, FavoritePage, FavoriteUpdate
from app.services import favorite_service

router = APIRouter(prefix="/favorites", tags=["Favoritos"])

AUTH_ERRORS: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "Token ausente ou inválido"}
}
NOT_FOUND: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse, "description": "Favorito não encontrado"}
}


@router.post(
    "",
    response_model=FavoriteOut,
    status_code=201,
    summary="Salva um trabalho nos favoritos (idempotente)",
    responses={
        200: {"model": FavoriteOut, "description": "O trabalho já estava salvo"},
        409: {"model": ErrorResponse, "description": "Limite de favoritos atingido"},
        **AUTH_ERRORS,
    },
)
async def create_favorite(
    data: FavoriteCreate, user: CurrentUser, session: SessionDep, response: Response
) -> FavoriteOut:
    favorite, created = await favorite_service.add(session, user.id, data)
    response.status_code = 201 if created else 200
    return favorite


@router.get(
    "",
    response_model=FavoritePage,
    summary="Lista os favoritos, do mais recente ao mais antigo",
    responses=AUTH_ERRORS,
)
async def list_favorites(
    user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    page: Annotated[int, Query(ge=1, description="Página (a partir de 1).")] = 1,
    page_size: Annotated[int | None, Query(ge=1, description="Itens por página.")] = None,
    q: Annotated[str | None, Query(description="Texto no título ou na anotação.")] = None,
) -> FavoritePage:
    size = min(page_size or settings.default_page_size, settings.max_page_size)
    return await favorite_service.list_favorites(session, user.id, page=page, page_size=size, q=q)


@router.patch(
    "/{favorite_id}",
    response_model=FavoriteOut,
    summary="Atualiza a anotação de um favorito",
    responses={**AUTH_ERRORS, **NOT_FOUND},
)
async def update_favorite(
    favorite_id: uuid.UUID, data: FavoriteUpdate, user: CurrentUser, session: SessionDep
) -> FavoriteOut:
    return await favorite_service.update_note(session, user.id, favorite_id, data.note)


@router.delete(
    "/{favorite_id}",
    status_code=204,
    summary="Remove um favorito",
    responses={**AUTH_ERRORS, **NOT_FOUND},
)
async def delete_favorite(
    favorite_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> Response:
    await favorite_service.remove(session, user.id, favorite_id)
    return Response(status_code=204)
