"""Cadastro, login e conta atual."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.deps import CurrentUser, IpHashDep, SessionDep, SettingsDep
from app.core.rate_limit import auth_limit, limiter
from app.core.security import create_access_token
from app.schemas.common import ErrorResponse
from app.schemas.user import LoginIn, TokenOut, UserCreate, UserOut
from app.services import account_service, auth_service

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=201,
    summary="Cria uma conta (com consentimento da Política de Privacidade)",
    responses={
        409: {"model": ErrorResponse, "description": "Não foi possível concluir o cadastro"}
    },
)
@limiter.limit(auth_limit)
async def register(
    request: Request,
    data: UserCreate,
    session: SessionDep,
    settings: SettingsDep,
    ip_hash: IpHashDep,
) -> UserOut:
    user = await auth_service.register(session, data, settings, ip_hash)
    return UserOut.model_validate(user)


@router.post(
    "/login",
    response_model=TokenOut,
    summary="Entra com e-mail e senha e recebe um token JWT",
    responses={401: {"model": ErrorResponse, "description": "E-mail ou senha inválidos"}},
)
@limiter.limit(auth_limit)
async def login(
    request: Request,
    data: LoginIn,
    session: SessionDep,
    settings: SettingsDep,
    ip_hash: IpHashDep,
) -> TokenOut:
    user = await auth_service.authenticate(session, data, ip_hash)
    return TokenOut(
        access_token=create_access_token(user.id, settings),
        expires_in=settings.access_token_expire_minutes * 60,
        consent_required=account_service.consent_required(user, settings),
    )


@router.get(
    "/me",
    response_model=UserOut,
    summary="Dados da conta autenticada",
    responses={401: {"model": ErrorResponse, "description": "Token ausente ou inválido"}},
)
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
