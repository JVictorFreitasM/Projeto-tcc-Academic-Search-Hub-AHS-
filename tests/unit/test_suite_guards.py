"""Garantias da própria suíte: marcadores, bloqueio de rede e fixtures sintéticas pendentes."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from tests.conftest import NetworkBlockedError

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]


def run_pytest(*args: str, strict: bool = False) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONUTF8": "1", "STRICT_FIXTURES": "1" if strict else ""}
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", "--no-cov", "-q", "-p", "no:cacheprovider", *args],
        cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", check=False,
    )  # fmt: skip


def test_every_test_has_the_marker_of_its_folder() -> None:
    result = run_pytest(
        "--collect-only", "-m", "not (unit or integration or contract or e2e or a11y)", "tests"
    )
    assert "no tests collected" in result.stdout or "0 tests collected" in result.stdout, (
        result.stdout[-600:]
    )


def test_marker_selection_separates_folders() -> None:
    unit = run_pytest("--collect-only", "-m", "unit", "tests")
    assert "tests/integration" not in unit.stdout.replace("\\", "/")
    assert "tests/e2e" not in unit.stdout.replace("\\", "/")


def test_real_socket_to_an_external_host_is_blocked() -> None:
    with pytest.raises(NetworkBlockedError, match="bloqueada"):
        socket.create_connection(("example.com", 80), timeout=2)
    with pytest.raises(NetworkBlockedError):
        socket.getaddrinfo("api.openalex.org", 443)


def test_connect_to_a_public_ip_is_blocked() -> None:
    sock = socket.socket()
    try:
        with pytest.raises(NetworkBlockedError):
            sock.connect(("93.184.216.34", 80))
        with pytest.raises(NetworkBlockedError):
            sock.connect_ex(("8.8.8.8", 53))
    finally:
        sock.close()


def test_httpx_to_an_external_host_is_blocked() -> None:
    """Prova pedida pela OS: um `httpx` real a um host externo é impedido (sem `respx`)."""
    with pytest.raises(httpx.ConnectError) as info:
        httpx.get("https://api.openalex.org/works", timeout=3)
    chain = []
    error: BaseException | None = info.value
    while error is not None:
        chain.append(type(error).__name__)
        error = error.__cause__ or error.__context__
    assert "NetworkBlockedError" in chain, chain


def test_loopback_is_still_allowed() -> None:
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    client = socket.create_connection(server.getsockname(), timeout=2)
    client.close()
    server.close()


def test_strict_fixtures_lists_the_pending_synthetic_ones() -> None:
    result = run_pytest("tests/contract", "-k", "no_synthetic_fixture_left", strict=True)
    assert result.returncode != 0
    output = result.stdout
    assert "Fixtures sintéticas pendentes" in output
    # OpenAlex (14/10) e CORE (15/10/2026) já têm resposta real: só as de OAI continuam pendentes
    assert "openalex/" not in output and "core/" not in output
    assert "oai/synthetic/list_records_page1.xml" in output


def test_strict_fixtures_is_skipped_by_default() -> None:
    result = run_pytest("tests/contract", "-k", "no_synthetic_fixture_left")
    assert result.returncode == 0 and "skipped" in result.stdout
