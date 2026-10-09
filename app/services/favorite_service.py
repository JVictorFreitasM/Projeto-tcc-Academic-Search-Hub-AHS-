"""Serviço de favoritos. A OS-017 acrescenta salvar, listar, anotar e remover."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable, Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Favorite

FavoriteLookup = Callable[[uuid.UUID, list[str]], Awaitable[set[str]]]


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
