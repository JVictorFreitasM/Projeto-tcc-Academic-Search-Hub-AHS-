import json
import logging

import httpx
import pytest
import respx

from app import __version__
from app.connectors.http import (
    MAX_RESPONSE_BYTES,
    ResponseTooLargeError,
    UpstreamHttpError,
    UpstreamTimeoutError,
    get_json,
    make_client,
)
from app.core.config import Settings
from app.core.errors import RateLimitedError, UpstreamError
from app.core.logging import configure_logging

pytestmark = pytest.mark.unit

URL = "https://api.exemplo.org/works"


class Sleeper:
    """Substitui `asyncio.sleep` e guarda as esperas pedidas."""

    def __init__(self) -> None:
        self.calls: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


@pytest.fixture
def sleeper() -> Sleeper:
    return Sleeper()


@pytest.fixture
async def client() -> httpx.AsyncClient:
    settings = Settings(_env_file=None, contact_email="eu@exemplo.com")  # type: ignore[call-arg]
    async with make_client(settings) as client:
        yield client  # type: ignore[misc]


@respx.mock
async def test_success(client: httpx.AsyncClient, sleeper: Sleeper) -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(200, json={"ok": True}))
    assert await get_json(client, URL, {"q": "x"}, sleep=sleeper) == {"ok": True}
    assert route.call_count == 1
    assert sleeper.calls == []


@respx.mock
async def test_timeout_retries_then_raises(client: httpx.AsyncClient, sleeper: Sleeper) -> None:
    route = respx.get(URL).mock(side_effect=httpx.ConnectTimeout("lento"))
    with pytest.raises(UpstreamTimeoutError):
        await get_json(client, URL, sleep=sleeper)
    assert route.call_count == 3  # 1 chamada + 2 novas tentativas
    assert sleeper.calls == [0.3, 0.6]  # espera exponencial curta


@respx.mock
async def test_503_then_200_uses_one_extra_attempt(
    client: httpx.AsyncClient, sleeper: Sleeper
) -> None:
    route = respx.get(URL).mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json={"n": 1})]
    )
    assert await get_json(client, URL, sleep=sleeper) == {"n": 1}
    assert route.call_count == 2
    assert len(sleeper.calls) == 1


@respx.mock
@pytest.mark.parametrize("status", [502, 503, 504])
async def test_persistent_5xx_raises_after_retries(
    client: httpx.AsyncClient, sleeper: Sleeper, status: int
) -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(status))
    with pytest.raises(UpstreamHttpError) as info:
        await get_json(client, URL, sleep=sleeper)
    assert info.value.upstream_status == status
    assert route.call_count == 3


@respx.mock
@pytest.mark.parametrize("status", [400, 401, 403, 404])
async def test_4xx_is_not_retried(client: httpx.AsyncClient, sleeper: Sleeper, status: int) -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(status))
    with pytest.raises(UpstreamHttpError) as info:
        await get_json(client, URL, sleep=sleeper)
    assert info.value.upstream_status == status
    assert route.call_count == 1
    assert sleeper.calls == []


@respx.mock
async def test_500_is_not_retried(client: httpx.AsyncClient, sleeper: Sleeper) -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(500))
    with pytest.raises(UpstreamHttpError):
        await get_json(client, URL, sleep=sleeper)
    assert route.call_count == 1


@respx.mock
async def test_429_with_retry_after(client: httpx.AsyncClient, sleeper: Sleeper) -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(429, headers={"Retry-After": "7"}))
    with pytest.raises(RateLimitedError) as info:
        await get_json(client, URL, sleep=sleeper)
    assert info.value.retry_after == 7
    assert route.call_count == 1


@respx.mock
async def test_429_without_retry_after(client: httpx.AsyncClient, sleeper: Sleeper) -> None:
    respx.get(URL).mock(return_value=httpx.Response(429))
    with pytest.raises(RateLimitedError) as info:
        await get_json(client, URL, sleep=sleeper)
    assert info.value.retry_after is None


@respx.mock
async def test_response_larger_than_limit(client: httpx.AsyncClient, sleeper: Sleeper) -> None:
    big = b'{"x": "' + b"a" * (MAX_RESPONSE_BYTES + 10) + b'"}'
    respx.get(URL).mock(return_value=httpx.Response(200, content=big))
    with pytest.raises(ResponseTooLargeError):
        await get_json(client, URL, sleep=sleeper)


@respx.mock
async def test_declared_content_length_over_limit(
    client: httpx.AsyncClient, sleeper: Sleeper
) -> None:
    respx.get(URL).mock(
        return_value=httpx.Response(
            200, content=b"{}", headers={"Content-Length": str(MAX_RESPONSE_BYTES + 1)}
        )
    )
    with pytest.raises((ResponseTooLargeError, UpstreamError)):
        await get_json(client, URL, sleep=sleeper)


@respx.mock
async def test_invalid_json(client: httpx.AsyncClient, sleeper: Sleeper) -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, content=b"<html>"))
    with pytest.raises(UpstreamError, match="inválida"):
        await get_json(client, URL, sleep=sleeper)


@respx.mock
async def test_network_error_retries(client: httpx.AsyncClient, sleeper: Sleeper) -> None:
    route = respx.get(URL).mock(side_effect=httpx.ConnectError("sem rede"))
    with pytest.raises(UpstreamError, match="rede"):
        await get_json(client, URL, sleep=sleeper)
    assert route.call_count == 3


@respx.mock
async def test_too_many_redirects(client: httpx.AsyncClient, sleeper: Sleeper) -> None:
    respx.get(URL).mock(return_value=httpx.Response(302, headers={"Location": URL + "?outra=1"}))
    with pytest.raises(UpstreamError, match="redirecionou"):
        await get_json(client, URL, sleep=sleeper)


@respx.mock
async def test_production_log_never_contains_api_key(
    client: httpx.AsyncClient, sleeper: Sleeper, capsys: pytest.CaptureFixture[str]
) -> None:
    """Com o logging configurado como em produção, a chave não aparece em nenhuma linha."""
    root = logging.getLogger()
    saved = (root.handlers[:], root.level)
    configure_logging("DEBUG")
    try:
        respx.get(URL).mock(return_value=httpx.Response(200, json={}))
        await get_json(client, URL, {"api_key": "SEGREDO", "q": "x"}, sleep=sleeper)
    finally:
        root.handlers[:], root.level = saved[0], saved[1]
        logging.getLogger("httpx").setLevel(logging.NOTSET)
        logging.getLogger("httpcore").setLevel(logging.NOTSET)
    output = capsys.readouterr().out
    assert "SEGREDO" not in output
    line = next(json.loads(row) for row in output.splitlines() if "Chamada externa" in row)
    assert line["url"] == URL
    assert line["status"] == 200
    assert "duration_ms" in line


@respx.mock
async def test_app_log_record_never_contains_api_key(
    client: httpx.AsyncClient, sleeper: Sleeper, caplog: pytest.LogCaptureFixture
) -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, json={}))
    with caplog.at_level(logging.INFO, logger="app.connectors.http"):
        await get_json(client, URL, {"api_key": "SEGREDO", "q": "x"}, sleep=sleeper)
    records = [r for r in caplog.records if r.name == "app.connectors.http"]
    assert records
    assert "SEGREDO" not in json.dumps([r.__dict__ for r in records], default=str)


@respx.mock
async def test_log_never_contains_api_key_in_failures(
    client: httpx.AsyncClient, sleeper: Sleeper, caplog: pytest.LogCaptureFixture
) -> None:
    respx.get(URL).mock(side_effect=httpx.ConnectError("falha em ?api_key=SEGREDO"))
    with caplog.at_level(logging.DEBUG), pytest.raises(UpstreamError) as info:
        await get_json(client, URL, {"api_key": "SEGREDO"}, sleep=sleeper)
    assert "SEGREDO" not in str(info.value)
    assert "SEGREDO" not in json.dumps([r.getMessage() for r in caplog.records])


async def test_client_identification_and_limits() -> None:
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None, contact_email="eu@exemplo.com", source_timeout_seconds=7
    )
    async with make_client(settings) as client:
        assert client.headers["User-Agent"] == (
            f"AcademicSearchHub/{__version__} (+contato: eu@exemplo.com)"
        )
        assert client.timeout.read == 7
        assert client.follow_redirects is True
        assert client.max_redirects == 3


async def test_client_without_contact() -> None:
    async with make_client(Settings(_env_file=None)) as client:  # type: ignore[call-arg]
        assert "nao-informado" in client.headers["User-Agent"]
