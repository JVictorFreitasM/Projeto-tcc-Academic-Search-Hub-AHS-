"""Reaproveita o servidor local e o navegador dos testes de interface (tests/e2e)."""

from tests.e2e.conftest import (  # noqa: F401
    LiveServer,
    browser,
    context,
    live_server,
    page,
    playwright_instance,
    playwright_pair,
)
