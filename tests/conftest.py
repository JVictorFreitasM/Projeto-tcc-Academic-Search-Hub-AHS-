"""Configuração comum da suíte."""

from __future__ import annotations

import asyncio
import sys
import warnings

import pytest

from app.core.config import get_settings

if sys.platform == "win32":
    # O psycopg assíncrono exige o SelectorEventLoop (o padrão do Windows é o Proactor).
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """URL do banco de testes; os testes de banco são pulados se ela não existir."""
    url = get_settings().test_database_url
    if not url:
        pytest.skip("TEST_DATABASE_URL não definida: testes de banco pulados")
    return url
