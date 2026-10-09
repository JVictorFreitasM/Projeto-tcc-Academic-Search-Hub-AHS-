"""Favoritos: retrato do registro + anotação, sempre restritos ao dono (controle por objeto)."""

from __future__ import annotations

import json
import uuid
from collections.abc import Awaitable, Callable, Iterable

from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.models import Favorite
from app.schemas.favorite import FavoriteCreate, FavoriteOut, FavoritePage
from app.schemas.record import RecordOut

FavoriteLookup = Callable[[uuid.UUID, list[str]], Awaitable[set[str]]]

MAX_FAVORITES_PER_USER = 2000
MAX_SNAPSHOT_BYTES = 20 * 1024


def to_out(favorite: Favorite) -> FavoriteOut:
    record = RecordOut.model_validate({**favorite.record_snapshot, "is_favorite": True})
    return FavoriteOut(
        id=favorite.id, record=record, note=favorite.note, created_at=favorite.created_at
    )


def _snapshot(record: RecordOut) -> dict[str, object]:
    data = record.model_copy(update={"is_favorite": False}).model_dump(mode="json")
    if len(json.dumps(data, ensure_ascii=False).encode()) > MAX_SNAPSHOT_BYTES:
        raise ValidationAppError(
            "O registro é grande demais para ser salvo nos favoritos.",
            details=[{"field": "record", "issue": "excede 20 KB"}],
        )
    return data


async def _get_owned(session: AsyncSession, user_id: uuid.UUID, favorite_id: uuid.UUID) -> Favorite:
    """Favorito do usuário ou 404 (nunca 403: não revela que o id existe para outra pessoa)."""
    result = await session.execute(
        select(Favorite).where(Favorite.id == favorite_id, Favorite.user_id == user_id)
    )
    favorite = result.scalar_one_or_none()
    if favorite is None:
        raise NotFoundError("Favorito não encontrado.")
    return favorite


async def _find_by_record(
    session: AsyncSession, user_id: uuid.UUID, record_id: str
) -> Favorite | None:
    result = await session.execute(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.record_id == record_id)
    )
    return result.scalar_one_or_none()


async def add(
    session: AsyncSession, user_id: uuid.UUID, data: FavoriteCreate
) -> tuple[FavoriteOut, bool]:
    """Salva o favorito. Idempotente: se já existe, devolve o existente (`created=False`)."""
    existing = await _find_by_record(session, user_id, data.record.id)
    if existing is not None:
        return to_out(existing), False

    count = (
        await session.execute(
            select(func.count()).select_from(Favorite).where(Favorite.user_id == user_id)
        )
    ).scalar_one()
    if count >= MAX_FAVORITES_PER_USER:
        raise ConflictError(
            f"Limite de {MAX_FAVORITES_PER_USER} favoritos atingido. "
            "Remova algum para salvar outro.",
            code="favorites_limit_reached",
        )
    favorite = Favorite(
        user_id=user_id,
        record_id=data.record.id,
        record_snapshot=_snapshot(data.record),
        note=data.note,
    )
    try:
        async with session.begin_nested():
            session.add(favorite)
            await session.flush()
    except IntegrityError:  # duas requisições simultâneas para o mesmo registro
        raced = await _find_by_record(session, user_id, data.record.id)
        if raced is None:
            raise
        return to_out(raced), False
    await session.refresh(favorite)
    return to_out(favorite), True


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def list_favorites(
    session: AsyncSession, user_id: uuid.UUID, *, page: int, page_size: int, q: str | None
) -> FavoritePage:
    conditions = [Favorite.user_id == user_id]
    if q and q.strip():
        pattern = f"%{_escape_like(q.strip())}%"
        conditions.append(
            or_(
                Favorite.record_snapshot["title"].astext.ilike(pattern, escape="\\"),
                Favorite.note.ilike(pattern, escape="\\"),
            )
        )
    total = (
        await session.execute(select(func.count()).select_from(Favorite).where(*conditions))
    ).scalar_one()
    rows = await session.execute(
        select(Favorite)
        .where(*conditions)
        .order_by(Favorite.created_at.desc(), Favorite.id)
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    return FavoritePage(
        items=[to_out(f) for f in rows.scalars()], page=page, page_size=page_size, total=total
    )


async def update_note(
    session: AsyncSession, user_id: uuid.UUID, favorite_id: uuid.UUID, note: str | None
) -> FavoriteOut:
    favorite = await _get_owned(session, user_id, favorite_id)
    favorite.note = note
    await session.flush()
    return to_out(favorite)


async def remove(session: AsyncSession, user_id: uuid.UUID, favorite_id: uuid.UUID) -> None:
    favorite = await _get_owned(session, user_id, favorite_id)
    await session.execute(delete(Favorite).where(Favorite.id == favorite.id))


async def favorite_ids_for(
    session: AsyncSession, user_id: uuid.UUID, record_ids: Iterable[str]
) -> set[str]:
    """Quais `record_id` da lista o usuário já favoritou (uma única consulta)."""
    ids = list(record_ids)
    if not ids:
        return set()
    rows = await session.execute(
        select(Favorite.record_id).where(Favorite.user_id == user_id, Favorite.record_id.in_(ids))
    )
    return set(rows.scalars())
