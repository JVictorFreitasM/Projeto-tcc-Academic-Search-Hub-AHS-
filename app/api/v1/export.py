"""Exportação de favoritos e de resultados de busca."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Query, Response
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, IpHashDep, SessionDep
from app.schemas.common import ErrorResponse
from app.schemas.record import RecordOut
from app.services import favorite_service
from app.services.export_service import FORMATS, ExportFormat
from app.services.security_events import record_event

router = APIRouter(tags=["Exportação"])

ExportName = Literal["bibtex", "ris", "json", "csv"]
MAX_EXPORT_RECORDS = 100

FILE_RESPONSE: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Arquivo para download",
        "content": {fmt.media_type: {"schema": {"type": "string"}} for fmt in FORMATS.values()},
    }
}


class ExportRequest(BaseModel):
    format: ExportName
    records: list[RecordOut] = Field(max_length=MAX_EXPORT_RECORDS, description="Até 100 registros")


def _file_response(fmt: ExportFormat, records: list[RecordOut]) -> Response:
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    return Response(
        content=fmt.render(records).encode("utf-8"),
        media_type=fmt.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="exportacao-{stamp}.{fmt.extension}"'
        },
    )


@router.get(
    "/favorites/export",
    summary="Exporta todos os favoritos do usuário",
    response_class=Response,
    responses={
        **FILE_RESPONSE,
        401: {"model": ErrorResponse, "description": "Token ausente ou inválido"},
    },
)
async def export_favorites(
    user: CurrentUser,
    session: SessionDep,
    ip_hash: IpHashDep,
    format: Annotated[ExportName, Query(description="bibtex, ris, json ou csv")],
) -> Response:
    # Declarada antes de qualquer rota /favorites/{id}, para "export" não ser lido como id.
    page = await favorite_service.list_favorites(
        session, user.id, page=1, page_size=favorite_service.MAX_FAVORITES_PER_USER, q=None
    )
    await record_event(session, "data_exported", user_id=user.id, ip_hash=ip_hash)
    return _file_response(FORMATS[format], [item.record for item in page.items])


@router.post(
    "/export",
    summary="Exporta registros de uma busca (sem exigir login)",
    response_class=Response,
    responses=FILE_RESPONSE,
)
async def export_records(data: ExportRequest) -> Response:
    return _file_response(FORMATS[data.format], data.records)
