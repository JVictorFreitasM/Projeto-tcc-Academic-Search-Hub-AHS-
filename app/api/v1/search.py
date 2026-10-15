"""Busca unificada e listagem de fontes."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from pydantic import ValidationError

from app.api.deps import OptionalUser, SessionDep, SettingsDep
from app.core.errors import ValidationAppError
from app.core.rate_limit import limiter, search_limit
from app.schemas.common import RECORD_TYPE_VALUES, ErrorResponse, RecordType
from app.schemas.search import SearchParams, SearchResponse, SourceInfo
from app.services import history_service
from app.services.favorite_service import favorite_ids_for
from app.services.search_service import SearchService, build_default_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Busca"])

HistoryRecorder = Callable[[uuid.UUID, SearchParams, int], Awaitable[None]]
SEARCH_ERRORS: dict[int | str, dict[str, Any]] = {
    502: {"model": ErrorResponse, "description": "Todas as fontes falharam; veja `sources_status`"},
}


def get_search_service(request: Request) -> SearchService:
    """Serviço único da aplicação (criado na primeira busca; testes usam override)."""
    service: SearchService | None = getattr(request.app.state, "search_service", None)
    if service is None:
        service = build_default_service(request.app.state.settings)
        request.app.state.search_service = service
    return service


async def _record_history(user_id: uuid.UUID, params: SearchParams, total: int) -> None:
    await history_service.record_search(user_id, params, total)


def get_history_recorder(request: Request) -> HistoryRecorder:
    """Gravador do histórico (os testes podem trocá-lo em `app.state.history_recorder`)."""
    recorder: HistoryRecorder | None = getattr(request.app.state, "history_recorder", None)
    return recorder or _record_history


def _csv(value: str | None) -> list[str] | None:
    if value is None:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def _parse_types(value: str | None) -> list[RecordType] | None:
    items = _csv(value)
    if items is None:
        return None
    invalid = [item for item in items if item not in RECORD_TYPE_VALUES]
    if invalid:
        raise ValidationAppError(
            "Tipo inválido. Valores válidos: " + ", ".join(RECORD_TYPE_VALUES),
            details=[{"field": "type", "issue": f"tipo inválido: {item}"} for item in invalid],
        )
    return [RecordType(item) for item in items]


def _build_params(raw: dict[str, Any]) -> SearchParams:
    try:
        return SearchParams(**raw)
    except ValidationError as exc:
        details = []
        for error in exc.errors():
            location = ".".join(str(part) for part in error["loc"])
            # q, year_from... são parâmetros de consulta; "type" é o nome público de `types`.
            field = {"types": "type"}.get(location, location)
            details.append(
                {"field": field, "issue": str(error["msg"]).removeprefix("Value error, ")}
            )
        raise ValidationAppError("Parâmetros de busca inválidos.", details=details) from None


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Busca trabalhos acadêmicos em todas as fontes ativas",
    responses=SEARCH_ERRORS,
)
@limiter.limit(search_limit)
async def search(
    request: Request,
    background: BackgroundTasks,
    service: Annotated[SearchService, Depends(get_search_service)],
    recorder: Annotated[HistoryRecorder, Depends(get_history_recorder)],
    user: OptionalUser,
    session: SessionDep,
    settings: SettingsDep,
    q: Annotated[str, Query(description="Termos da busca (2 a 200 caracteres).")],
    sources: Annotated[
        str | None,
        Query(description="Fontes separadas por vírgula (padrão: todas as ativas)."),
    ] = None,
    year_from: Annotated[
        int | None, Query(description="Ano inicial (1900 até o ano atual + 1).")
    ] = None,
    year_to: Annotated[int | None, Query(description="Ano final.")] = None,
    type: Annotated[
        str | None,
        Query(description="Tipos separados por vírgula: article, thesis, preprint, book, other."),
    ] = None,
    page: Annotated[int, Query(ge=1, description="Página (a partir de 1).")] = 1,
    page_size: Annotated[
        int | None,
        Query(ge=1, description="Itens por página (padrão e máximo vêm da configuração)."),
    ] = None,
    sort: Annotated[
        Literal["relevance", "year_desc"], Query(description="Ordenação.")
    ] = "relevance",
    field: Annotated[
        Literal["all", "author"],
        Query(
            description=(
                "Onde procurar: `all` (padrão) busca o tema no título, no resumo e nas "
                "palavras-chave; `author` busca o nome (ou só o sobrenome) do autor."
            )
        ),
    ] = "all",
) -> SearchResponse:
    params = _build_params(
        {
            "q": q,
            "sources": _csv(sources),
            "year_from": year_from,
            "year_to": year_to,
            "types": _parse_types(type),
            "page": page,
            "page_size": page_size or settings.default_page_size,
            "sort": sort,
            "field": field,
        }
    )

    async def lookup(user_id: uuid.UUID, record_ids: list[str]) -> set[str]:
        return await favorite_ids_for(session, user_id, record_ids)

    response = await service.search(params, user.id if user else None, lookup)
    if user is not None:
        # Depois da resposta e sem atrasá-la; uma falha no histórico nunca quebra a busca.
        background.add_task(_safe_record, recorder, user.id, params, response.total_estimated)
    return response


async def _safe_record(
    recorder: HistoryRecorder, user_id: uuid.UUID, params: SearchParams, total: int
) -> None:
    try:
        await recorder(user_id, params, total)
    except Exception:
        logger.error("Não foi possível gravar o histórico de busca")


@router.get(
    "/sources",
    response_model=list[SourceInfo],
    summary="Lista as fontes de busca e se estão disponíveis",
)
async def list_sources(
    service: Annotated[SearchService, Depends(get_search_service)],
) -> list[SourceInfo]:
    """Não expõe endereços internos, chaves nem contagens de registros."""
    return await service.describe_sources()
