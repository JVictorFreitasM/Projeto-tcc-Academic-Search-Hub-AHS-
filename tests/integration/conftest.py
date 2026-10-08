"""Fixtures dos testes de integração (PostgreSQL de teste)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

ROOT = Path(__file__).resolve().parents[2]


def alembic_config(url: str) -> Config:
    """Configuração do Alembic apontando para o banco de teste."""
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    config.attributes["configure_logger"] = False
    return config


@pytest.fixture(scope="session")
def migrated_db_url(test_database_url: str) -> Iterator[str]:
    """Banco de teste recriado do zero e migrado até a última revisão."""
    config = alembic_config(test_database_url)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    yield test_database_url


@pytest.fixture
async def engine(migrated_db_url: str) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(migrated_db_url)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Sessão com rollback ao final: cada teste começa com as tabelas como estavam."""
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
        await session.rollback()
