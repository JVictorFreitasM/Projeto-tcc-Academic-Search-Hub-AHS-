"""Conta do usuário e direitos do titular (LGPD, art. 18): acesso, correção, eliminação."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ConflictError, ForbiddenError, ValidationAppError
from app.core.security import hash_password, verify_password
from app.models import Favorite, SearchHistory, User
from app.schemas.favorite import FavoriteOut
from app.schemas.history import HistoryOut
from app.schemas.user import MeUpdate, UserOut, check_password_rules
from app.services import favorite_service
from app.services.auth_service import get_user_by_email
from app.services.security_events import record_event

UPDATE_FAILED = "Não foi possível atualizar os dados."
WRONG_PASSWORD = "Senha atual incorreta."  # noqa: S105  # nosec B105 - mensagem de erro exibida ao usuário, não é uma senha


def _require_password(user: User, password: str | None) -> None:
    if not password or not verify_password(user.password_hash, password):
        raise ForbiddenError(WRONG_PASSWORD, code="invalid_password")


async def update_profile(session: AsyncSession, user: User, data: MeUpdate) -> User:
    """Corrige nome e/ou e-mail. E-mail novo exige a senha atual e não revela se já existe."""
    if data.email is not None and data.email != user.email:
        _require_password(user, data.current_password)
        if await get_user_by_email(session, data.email) is not None:
            raise ConflictError(UPDATE_FAILED)
        user.email = data.email
    if data.full_name is not None:
        user.full_name = data.full_name
    await session.flush()
    await session.refresh(user)
    return user


async def change_password(
    session: AsyncSession, user: User, current: str, new: str, ip_hash: str | None
) -> None:
    _require_password(user, current)
    try:
        check_password_rules(new, user.email)
    except ValueError as exc:
        raise ValidationAppError(
            "Senha nova inválida.", details=[{"field": "new_password", "issue": str(exc)}]
        ) from None
    user.password_hash = hash_password(new)
    await record_event(session, "password_changed", user_id=user.id, ip_hash=ip_hash)


async def accept_current_policy(session: AsyncSession, user: User, settings: Settings) -> User:
    user.consent_at = datetime.now(UTC)
    user.consent_policy_version = settings.privacy_policy_version
    await session.flush()
    await session.refresh(user)
    return user


def consent_required(user: User, settings: Settings) -> bool:
    """A política mudou desde o último aceite?"""
    return user.consent_policy_version != settings.privacy_policy_version


async def export_data(session: AsyncSession, user: User, ip_hash: str | None) -> dict[str, Any]:
    """Cópia dos dados do próprio titular: conta, favoritos e histórico (sem o hash da senha)."""
    favorites = (
        await session.execute(
            select(Favorite).where(Favorite.user_id == user.id).order_by(Favorite.created_at.desc())
        )
    ).scalars()
    history = (
        await session.execute(
            select(SearchHistory)
            .where(SearchHistory.user_id == user.id)
            .order_by(SearchHistory.created_at.desc())
        )
    ).scalars()
    await record_event(session, "data_exported", user_id=user.id, ip_hash=ip_hash)
    return {
        "exported_at": datetime.now(UTC).isoformat(),
        "account": UserOut.model_validate(user).model_dump(mode="json"),
        "favorites": [
            FavoriteOut.model_validate(favorite_service.to_out(f)).model_dump(mode="json")
            for f in favorites
        ],
        "search_history": [HistoryOut.model_validate(h).model_dump(mode="json") for h in history],
    }


async def delete_account(
    session: AsyncSession, user: User, password: str, ip_hash: str | None
) -> None:
    """Elimina conta, favoritos e histórico (cascata). O evento fica sem dados pessoais."""
    _require_password(user, password)
    # user_id fica nulo de propósito: o identificador seria um dado pessoal pseudonimizado.
    await record_event(session, "account_deleted", user_id=None, ip_hash=ip_hash)
    await session.execute(delete(User).where(User.id == user.id))
