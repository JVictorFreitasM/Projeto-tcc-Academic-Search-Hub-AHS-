"""Infraestrutura dos testes de interface: servidor local real + Chromium (Playwright)."""

from __future__ import annotations

import asyncio
import contextlib
import socket
import sys
import threading
import time
import warnings
from collections.abc import Iterator
from typing import Any

import pytest
import uvicorn
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from app.core.config import Settings
from app.main import create_app


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class LiveServer:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url


@pytest.fixture(scope="session")
def live_server() -> Iterator[LiveServer]:
    """Aplicação real (arquivos estáticos + API) numa porta livre, em outra thread."""
    port = _free_port()
    settings = Settings(_env_file=None, allowed_origins=f"http://127.0.0.1:{port}")  # type: ignore[call-arg]
    config = uvicorn.Config(
        create_app(settings), host="127.0.0.1", port=port, log_config=None, lifespan="on"
    )
    server = uvicorn.Server(config)

    def serve() -> None:
        # O servidor usa o SelectorEventLoop (exigido pelo psycopg no Windows), independente do
        # loop do Playwright.
        factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
        with asyncio.Runner(loop_factory=factory) as runner:
            runner.run(server.serve())

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    deadline = time.time() + 15
    while not server.started and time.time() < deadline:
        time.sleep(0.05)
    assert server.started, "o servidor de teste não iniciou"
    yield LiveServer(f"http://127.0.0.1:{port}")
    server.should_exit = True
    thread.join(timeout=10)


def _start_playwright() -> Playwright:
    """O Playwright precisa de subprocessos (ProactorEventLoop no Windows); a suíte usa Selector."""
    previous = asyncio.get_event_loop_policy()
    if sys.platform == "win32":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    try:
        return sync_playwright().start()
    finally:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            asyncio.set_event_loop_policy(previous)


def _start_browser(attempts: int = 3) -> tuple[Playwright, Browser]:
    """Inicia Playwright e Chromium. O driver às vezes cai ao iniciar sob carga: tenta de novo."""
    last_error: Exception | None = None
    for attempt in range(attempts):
        manager = _start_playwright()
        try:
            return manager, manager.chromium.launch()
        except Exception as exc:
            last_error = exc
            with contextlib.suppress(Exception):
                manager.stop()
            time.sleep(1 + attempt)
    raise RuntimeError(f"não foi possível iniciar o navegador: {last_error}")


@pytest.fixture(scope="module")
def playwright_pair() -> Iterator[tuple[Playwright, Browser]]:
    """Escopo de módulo: o Playwright síncrono mantém um loop ativo na thread principal e precisa
    ser encerrado antes dos testes assíncronos que vêm depois."""
    manager, chromium = _start_browser()
    yield manager, chromium
    with contextlib.suppress(Exception):
        chromium.close()
    manager.stop()


@pytest.fixture(scope="module")
def playwright_instance(playwright_pair: tuple[Playwright, Browser]) -> Playwright:
    return playwright_pair[0]


@pytest.fixture(scope="module")
def browser(playwright_pair: tuple[Playwright, Browser]) -> Browser:
    return playwright_pair[1]


@pytest.fixture
def context(browser: Browser, live_server: LiveServer) -> Iterator[BrowserContext]:
    ctx = browser.new_context(base_url=live_server.base_url, locale="pt-BR")
    yield ctx
    ctx.close()


class PageProbe:
    """Coleta erros de console e violações de CSP enquanto a página é usada."""

    def __init__(self, page: Page) -> None:
        self.errors: list[str] = []
        page.on("console", self._on_console)
        page.on("pageerror", lambda exc: self.errors.append(f"pageerror: {exc}"))
        page.on("requestfailed", lambda req: self.errors.append(f"requestfailed: {req.url}"))

    def _on_console(self, message: Any) -> None:
        if message.type in ("error", "warning"):
            self.errors.append(f"{message.type}: {message.text}")


@pytest.fixture
def page(context: BrowserContext) -> Page:
    page = context.new_page()
    page.probe = PageProbe(page)  # type: ignore[attr-defined]
    return page
