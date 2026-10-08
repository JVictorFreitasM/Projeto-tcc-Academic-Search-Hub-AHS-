"""Ambiente do Alembic em modo assíncrono, lendo a URL de `Settings`."""

from __future__ import annotations

import asyncio
import logging
import sys

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import app.models  # noqa: F401  (registra os modelos em Base.metadata)
from app.core.config import get_settings
from app.db.base import Base

config = context.config
target_metadata = Base.metadata

# Na linha de comando, mostra "Running upgrade ..."; os testes desligam isso.
_alembic_logger = logging.getLogger("alembic")
if config.attributes.get("configure_logger", True) and not _alembic_logger.handlers:
    _alembic_logger.setLevel(logging.INFO)
    _alembic_logger.addHandler(logging.StreamHandler(sys.stdout))
    _alembic_logger.propagate = False

# Os testes injetam outra URL com `config.set_main_option`; senão vale DATABASE_URL.
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", get_settings().database_url.replace("%", "%%"))


def run_migrations_offline() -> None:
    """Gera o SQL sem conectar ao banco."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    # O psycopg assíncrono não funciona com o ProactorEventLoop do Windows.
    if sys.platform == "win32":
        with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
            runner.run(run_async_migrations())
    else:
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
