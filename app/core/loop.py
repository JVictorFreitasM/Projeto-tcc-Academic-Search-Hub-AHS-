"""Execução de corrotinas fora do servidor (CLI e scripts)."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Roda a corrotina até o fim.

    No Windows usa o `SelectorEventLoop`: o psycopg assíncrono não funciona com o
    `ProactorEventLoop`, que é o padrão da plataforma.
    """
    factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    with asyncio.Runner(loop_factory=factory) as runner:
        return runner.run(coro)
