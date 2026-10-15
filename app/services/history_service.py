"""Histórico de buscas do usuário logado, com retenção limitada (LGPD: necessidade e eliminação)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.errors import NotFoundError
from app.db.session import get_sessionmaker
from app.models import SearchHistory
from app.schemas.history import HistoryOut, HistoryPage
from app.schemas.search import SearchParams

MAX_HISTORY_PER_USER = 200


def filters_of(params: SearchParams) -> dict[str, Any]:
    """Filtros da busca (sem texto e sem página): é o que define "a mesma consulta"."""
    return {
        "sources": sorted(params.sources) if params.sources else None,
        "year_from": params.year_from,
        "year_to": params.year_to,
        "types": sorted(t.value for t in params.types) if params.types else None,
        "sort": params.sort,
        "field": params.field,
    }


async def record_search(
    user_id: uuid.UUID,
    params: SearchParams,
    total_estimated: int,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> bool:
    """Grava a busca do usuário. Devolve `False` quando é repetição imediata da anterior.

    Roda depois da resposta, em sessão própria. Mantém só as 200 mais recentes.
    """
    factory = session_factory or get_sessionmaker()
    filters = filters_of(params)
    async with factory() as session:
        latest = (
            await session.execute(
                select(SearchHistory)
                .where(SearchHistory.user_id == user_id)
                .order_by(SearchHistory.created_at.desc(), SearchHistory.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if latest is not None and latest.query == params.q and latest.filters == filters:
            return False
        session.add(
            SearchHistory(
                user_id=user_id,
                query=params.q,
                filters=filters,
                result_count_estimated=total_estimated,
            )
        )
        await session.flush()
        newest = (
            select(SearchHistory.id)
            .where(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.created_at.desc(), SearchHistory.id.desc())
            .limit(MAX_HISTORY_PER_USER)
        )
        await session.execute(
            delete(SearchHistory).where(
                SearchHistory.user_id == user_id, SearchHistory.id.not_in(newest)
            )
        )
        await session.commit()
    return True


async def list_history(
    session: AsyncSession, user_id: uuid.UUID, *, page: int, page_size: int
) -> HistoryPage:
    total = (
        await session.execute(
            select(func.count()).select_from(SearchHistory).where(SearchHistory.user_id == user_id)
        )
    ).scalar_one()
    rows = await session.execute(
        select(SearchHistory)
        .where(SearchHistory.user_id == user_id)
        .order_by(SearchHistory.created_at.desc(), SearchHistory.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    return HistoryPage(
        items=[HistoryOut.model_validate(row) for row in rows.scalars()],
        page=page,
        page_size=page_size,
        total=total,
    )


async def delete_one(session: AsyncSession, user_id: uuid.UUID, history_id: uuid.UUID) -> None:
    result = await session.execute(
        delete(SearchHistory).where(
            SearchHistory.id == history_id, SearchHistory.user_id == user_id
        )
    )
    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise NotFoundError("Item do histórico não encontrado.")


async def clear_all(session: AsyncSession, user_id: uuid.UUID) -> None:
    await session.execute(delete(SearchHistory).where(SearchHistory.user_id == user_id))
