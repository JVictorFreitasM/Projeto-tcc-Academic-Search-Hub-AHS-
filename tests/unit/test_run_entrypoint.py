from typing import Any

import pytest

from app import run

pytestmark = pytest.mark.unit


def test_run_builds_a_single_process_server_with_safe_proxy_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeServer:
        def __init__(self, config: Any) -> None:
            captured["config"] = config

        async def serve(self) -> None:
            captured["served"] = True

    monkeypatch.setattr(run.uvicorn, "Server", FakeServer)
    assert run.main() == 0
    config = captured["config"]
    assert captured["served"] is True
    assert config.host == "127.0.0.1" and config.port == 8000
    assert config.factory is True and config.app == "app.main:create_app"
    assert config.proxy_headers is True and config.forwarded_allow_ips == "127.0.0.1"
    assert (
        config.workers in (None, 1) and not config.reload
    )  # um único processo (limite em memória)
