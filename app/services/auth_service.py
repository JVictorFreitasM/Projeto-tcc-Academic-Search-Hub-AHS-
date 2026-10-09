"""Cadastro e autenticação de usuários."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import AuthError, ConflictError
from app.core.security import (
    dummy_password_hash,
    hash_password,
    needs_rehash,
    verify_password,
)
from app.models import User
from app.schemas.user import LoginIn, UserCreate
from app.services.security_events import record_event

logger = logging.getLogger(__name__)

REGISTER_FAILED = "Não foi possível concluir o cadastro."
LOGIN_FAILED = "E-mail ou senha inválidos."


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def register(
    session: AsyncSession, data: UserCreate, settings: Settings, ip_hash: str | None
) -> User:
    """Cria a conta, registrando o consentimento. E-mail repetido não é revelado (409 genérico)."""
    if await get_user_by_email(session, data.email) is not None:
        raise ConflictError(REGISTER_FAILED)
    user = User(
        email=data.email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        consent_at=datetime.now(UTC),
        consent_policy_version=settings.privacy_policy_version,
    )
    session.add(user)
    try:
        await session.flush()
    except IntegrityError:  # corrida entre dois cadastros do mesmo e-mail
        await session.rollback()
        raise ConflictError(REGISTER_FAILED) from None
    await record_event(session, "account_registered", user_id=user.id, ip_hash=ip_hash)
    await session.refresh(user)
    return user


async def authenticate(session: AsyncSession, data: LoginIn, ip_hash: str | None) -> User:
    """Confere e-mail e senha. Mensagem e tempo de resposta não revelam se o e-mail existe."""
    user = await get_user_by_email(session, data.email)
    # Sem usuário, verifica contra um hash falso para o custo ser semelhante.
    stored = user.password_hash if user else dummy_password_hash()
    valid = verify_password(stored, data.password)
    if user is None or not user.is_active or not valid:
        await record_event(session, "login_failed", user_id=None, ip_hash=ip_hash)
        await session.commit()  # o evento precisa sobreviver ao 401 (a sessão faria rollback)
        raise AuthError(LOGIN_FAILED)

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(data.password)
    user.last_login_at = datetime.now(UTC)
    await record_event(session, "login_success", user_id=user.id, ip_hash=ip_hash)
    return user
