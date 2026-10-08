"""Engine e sessão assíncronas do SQLAlchemy (driver psycopg 3)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    """Cria o engine na primeira chamada (importar o módulo não abre conexão)."""
    return create_async_engine(
        get_settings().database_url, pool_pre_ping=True, connect_args={"connect_timeout": 5}
    )


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Fábrica de sessões; `expire_on_commit=False` evita recargas após o commit."""
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependência do FastAPI: commit se tudo correu bem, rollback em qualquer exceção."""
    async with get_sessionmaker()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_database() -> bool:
    """Executa `SELECT 1`; devolve `False` em qualquer falha (sem expor o motivo)."""
    try:
        async with get_engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        return False
    return True
