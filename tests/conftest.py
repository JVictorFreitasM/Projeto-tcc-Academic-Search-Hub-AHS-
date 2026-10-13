"""Configuração comum da suíte: loop de eventos, marcadores por pasta e bloqueio de rede."""

from __future__ import annotations

import asyncio
import ipaddress
import socket
import sys
import warnings
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from app.core.config import get_settings

if sys.platform == "win32":
    # O psycopg assíncrono exige o SelectorEventLoop (o padrão do Windows é o Proactor).
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TESTS_DIR = Path(__file__).resolve().parent
FOLDER_MARKERS = ("unit", "integration", "contract", "e2e", "a11y")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Todo teste recebe o marcador da sua pasta (unit, integration, contract, e2e ou a11y)."""
    for item in items:
        try:
            folder = Path(str(item.fspath)).resolve().relative_to(TESTS_DIR).parts[0]
        except (ValueError, IndexError):
            continue
        if folder in FOLDER_MARKERS and item.get_closest_marker(folder) is None:
            item.add_marker(getattr(pytest.mark, folder))


# ---------- nenhum teste usa a internet ----------


class NetworkBlockedError(OSError):
    """Tentativa de acesso à rede externa durante os testes (regra 9 das OS)."""


def _is_local_host(host: Any) -> bool:
    """Só o próprio computador (banco local, servidor de teste do Playwright) é permitido."""
    if host in (None, "", "localhost", "0.0.0.0"):  # noqa: S104 (comparação, não é bind)
        return True
    if isinstance(host, bytes):
        host = host.decode()
    try:
        return ipaddress.ip_address(str(host).split("%")[0]).is_loopback
    except ValueError:
        return False


@pytest.fixture(scope="session", autouse=True)
def _block_external_network() -> Iterator[None]:
    """Bloqueia conexões e resoluções de nome para qualquer endereço que não seja local."""
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex
    real_getaddrinfo = socket.getaddrinfo

    def guard(address: Any) -> None:
        if isinstance(address, tuple) and address and not _is_local_host(address[0]):
            raise NetworkBlockedError(f"rede externa bloqueada nos testes: {address[0]}")

    def connect(self: socket.socket, address: Any) -> Any:
        guard(address)
        return real_connect(self, address)

    def connect_ex(self: socket.socket, address: Any) -> Any:
        guard(address)
        return real_connect_ex(self, address)

    def getaddrinfo(host: Any, *args: Any, **kwargs: Any) -> Any:
        if not _is_local_host(host):
            raise NetworkBlockedError(f"resolução de nome bloqueada nos testes: {host}")
        return real_getaddrinfo(host, *args, **kwargs)

    socket.socket.connect = connect  # type: ignore[method-assign,assignment]
    socket.socket.connect_ex = connect_ex  # type: ignore[method-assign,assignment]
    socket.getaddrinfo = getaddrinfo  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.socket.connect = real_connect  # type: ignore[method-assign]
        socket.socket.connect_ex = real_connect_ex  # type: ignore[method-assign]
        socket.getaddrinfo = real_getaddrinfo


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """URL do banco de testes; os testes de banco são pulados se ela não existir."""
    url = get_settings().test_database_url
    if not url:
        pytest.skip("TEST_DATABASE_URL não definida: testes de banco pulados")
    return url
