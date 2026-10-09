"""Histórico de buscas do usuário autenticado."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Query, Response

from app.api.deps import CurrentUser, SessionDep, SettingsDep
from app.schemas.common import ErrorResponse
from app.schemas.history import HistoryPage
from app.services import history_service

router = APIRouter(prefix="/history", tags=["Histórico"])

AUTH: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "Token ausente ou inválido"}
}


@router.get(
    "",
    response_model=HistoryPage,
    summary="Lista as últimas buscas (até 200), da mais recente à mais antiga",
    responses=AUTH,
)
async def list_history(
    user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    page: Annotated[int, Query(ge=1, description="Página (a partir de 1).")] = 1,
    page_size: Annotated[int | None, Query(ge=1, description="Itens por página.")] = None,
) -> HistoryPage:
    size = min(page_size or settings.default_page_size, settings.max_page_size)
    return await history_service.list_history(session, user.id, page=page, page_size=size)


@router.delete(
    "/{history_id}",
    status_code=204,
    summary="Remove um item do histórico",
    responses={
        **AUTH,
        404: {"model": ErrorResponse, "description": "Item não encontrado"},
    },
)
async def delete_history_item(
    history_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> Response:
    await history_service.delete_one(session, user.id, history_id)
    return Response(status_code=204)


@router.delete("", status_code=204, summary="Limpa todo o histórico", responses=AUTH)
async def clear_history(user: CurrentUser, session: SessionDep) -> Response:
    await history_service.clear_all(session, user.id)
    return Response(status_code=204)
