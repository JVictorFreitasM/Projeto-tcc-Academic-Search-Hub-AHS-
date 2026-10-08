from collections.abc import Iterator

import psycopg
import pytest
from alembic import command
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import session as db_session
from tests.integration.conftest import alembic_config

pytestmark = pytest.mark.integration


@pytest.fixture
def fresh_engine_cache() -> Iterator[None]:
    """Limpa os caches de configuração e engine antes e depois do teste."""
    get_settings.cache_clear()
    db_session.get_engine.cache_clear()
    yield
    get_settings.cache_clear()
    db_session.get_engine.cache_clear()


async def test_connection(session: AsyncSession) -> None:
    assert (await session.execute(text("SELECT 1"))).scalar_one() == 1


async def test_immutable_unaccent(session: AsyncSession) -> None:
    result = await session.execute(text("SELECT immutable_unaccent('Ação')"))
    assert result.scalar_one() == "Acao"


async def test_immutable_unaccent_is_immutable(session: AsyncSession) -> None:
    result = await session.execute(
        text("SELECT provolatile FROM pg_proc WHERE proname = 'immutable_unaccent'")
    )
    assert result.scalar_one() == "i"


async def test_pt_unaccent_matches_without_accent(session: AsyncSession) -> None:
    result = await session.execute(
        text(
            "SELECT to_tsvector('pt_unaccent', 'Educação básica') "
            "@@ to_tsquery('pt_unaccent', 'educacao')"
        )
    )
    assert result.scalar_one() is True


async def test_pt_unaccent_matches_with_accent_in_query(session: AsyncSession) -> None:
    result = await session.execute(
        text(
            "SELECT to_tsvector('pt_unaccent', 'Educacao basica') "
            "@@ websearch_to_tsquery('pt_unaccent', 'educação')"
        )
    )
    assert result.scalar_one() is True


async def test_check_database_ok(
    migrated_db_url: str, monkeypatch: pytest.MonkeyPatch, fresh_engine_cache: None
) -> None:
    monkeypatch.setenv("DATABASE_URL", migrated_db_url)
    try:
        assert await db_session.check_database() is True
    finally:
        await db_session.get_engine().dispose()


async def test_check_database_false_when_unreachable(
    monkeypatch: pytest.MonkeyPatch, fresh_engine_cache: None
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://x:y@127.0.0.1:1/nada")
    try:
        assert await db_session.check_database() is False
    finally:
        await db_session.get_engine().dispose()


def test_migration_downgrade_and_upgrade(migrated_db_url: str) -> None:
    config = alembic_config(migrated_db_url)
    command.downgrade(config, "base")
    command.upgrade(config, "head")


def test_downgrade_removes_objects(migrated_db_url: str) -> None:
    config = alembic_config(migrated_db_url)
    sync_url = migrated_db_url.replace("postgresql+psycopg", "postgresql")
    command.downgrade(config, "base")
    try:
        with psycopg.connect(sync_url) as conn:
            row = conn.execute(
                "SELECT count(*) FROM pg_proc WHERE proname = 'immutable_unaccent'"
            ).fetchone()
            assert row is not None
            assert row[0] == 0
    finally:
        command.upgrade(config, "head")
