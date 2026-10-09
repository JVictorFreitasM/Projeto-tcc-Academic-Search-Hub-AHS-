"""Dependências compartilhadas das rotas."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import AuthError
from app.core.rate_limit import client_ip_hash
from app.core.security import decode_access_token
from app.db.session import get_session
from app.models import User

bearer_scheme = HTTPBearer(scheme_name="bearerAuth", auto_error=False)


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]
CredentialsDep = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def get_ip_hash(request: Request, settings: SettingsDep) -> str:
    return client_ip_hash(request, settings)


IpHashDep = Annotated[str, Depends(get_ip_hash)]


async def get_optional_user(
    credentials: CredentialsDep, session: SessionDep, settings: SettingsDep
) -> User | None:
    """Usuário do token, ou `None` para visitante. Token inválido continua sendo erro 401."""
    if credentials is None:
        return None
    user_id = decode_access_token(credentials.credentials, settings)
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise AuthError("Sessão inválida ou expirada. Entre novamente.")
    return user


async def get_current_user(user: Annotated[User | None, Depends(get_optional_user)]) -> User:
    if user is None:
        raise AuthError("Autenticação necessária.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
