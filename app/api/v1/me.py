"""Conta do titular dos dados (LGPD, art. 18) e política de privacidade."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from app.api.deps import CurrentUser, IpHashDep, SessionDep, SettingsDep
from app.schemas.common import ErrorResponse
from app.schemas.user import AccountDelete, MeUpdate, PasswordChange, PrivacyPolicyOut, UserOut
from app.services import account_service

router = APIRouter(prefix="/me", tags=["Minha conta (LGPD)"])
privacy_router = APIRouter(tags=["Minha conta (LGPD)"])

POLICY_FILE = Path(__file__).resolve().parents[2] / "content" / "privacy_pt.md"
AUTH: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "Token ausente ou inválido"}
}
WRONG_PASSWORD: dict[int | str, dict[str, Any]] = {
    403: {"model": ErrorResponse, "description": "Senha atual incorreta (`invalid_password`)"}
}


@router.get("", response_model=UserOut, summary="Acesso: dados da conta", responses=AUTH)
async def get_me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.patch(
    "",
    response_model=UserOut,
    summary="Correção: altera nome e/ou e-mail (e-mail novo exige a senha atual)",
    responses={
        **AUTH,
        **WRONG_PASSWORD,
        409: {"model": ErrorResponse, "description": "Não foi possível atualizar os dados"},
    },
)
async def update_me(data: MeUpdate, user: CurrentUser, session: SessionDep) -> UserOut:
    updated = await account_service.update_profile(session, user, data)
    return UserOut.model_validate(updated)


@router.post(
    "/password",
    status_code=204,
    summary="Troca a senha (exige a senha atual)",
    responses={**AUTH, **WRONG_PASSWORD},
)
async def change_password(
    data: PasswordChange, user: CurrentUser, session: SessionDep, ip_hash: IpHashDep
) -> Response:
    await account_service.change_password(
        session, user, data.current_password, data.new_password, ip_hash
    )
    return Response(status_code=204)


@router.get(
    "/data-export",
    summary="Acesso e portabilidade: baixa conta, favoritos e histórico em JSON",
    response_class=JSONResponse,
    responses=AUTH,
)
async def data_export(user: CurrentUser, session: SessionDep, ip_hash: IpHashDep) -> JSONResponse:
    data = await account_service.export_data(session, user, ip_hash)
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    return JSONResponse(
        data,
        headers={"Content-Disposition": f'attachment; filename="meus-dados-{stamp}.json"'},
    )


@router.post(
    "/consent",
    response_model=UserOut,
    summary="Registra o aceite da versão atual da Política de Privacidade",
    responses=AUTH,
)
async def accept_consent(user: CurrentUser, session: SessionDep, settings: SettingsDep) -> UserOut:
    updated = await account_service.accept_current_policy(session, user, settings)
    return UserOut.model_validate(updated)


@router.delete(
    "",
    status_code=204,
    summary="Eliminação: apaga a conta, os favoritos e o histórico (exige a senha)",
    responses={**AUTH, **WRONG_PASSWORD},
)
async def delete_me(
    data: AccountDelete, user: CurrentUser, session: SessionDep, ip_hash: IpHashDep
) -> Response:
    await account_service.delete_account(session, user, data.password, ip_hash)
    return Response(status_code=204)


@privacy_router.get(
    "/privacy",
    response_model=PrivacyPolicyOut,
    summary="Texto da Política de Privacidade (público)",
)
async def privacy(settings: SettingsDep) -> PrivacyPolicyOut:
    return PrivacyPolicyOut(
        version=settings.privacy_policy_version,
        content=POLICY_FILE.read_text(encoding="utf-8"),
    )
