from datetime import date

import httpx
import pytest
import respx

from app.harvest.oai_client import (
    BadResumptionTokenError,
    OaiClient,
    OaiError,
    OaiProtocolError,
    OaiXmlError,
)
from tests.oai_support import OAI_URL, oai_server, xml_response

pytestmark = pytest.mark.unit


class Sleeper:
    def __init__(self) -> None:
        self.calls: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


@pytest.fixture
def sleeper() -> Sleeper:
    return Sleeper()


@pytest.fixture
async def http() -> httpx.AsyncClient:
    async with httpx.AsyncClient() as client:
        yield client  # type: ignore[misc]


def make(http: httpx.AsyncClient, sleeper: Sleeper, delay: float = 1.0) -> OaiClient:
    return OaiClient(OAI_URL, http, delay_seconds=delay, sleep=sleeper)


@respx.mock
async def test_two_pages_following_resumption_token(
    http: httpx.AsyncClient, sleeper: Sleeper
) -> None:
    route = respx.get(OAI_URL).mock(side_effect=oai_server)
    records = [r async for r in make(http, sleeper).list_records()]
    assert [r.identifier for r in records] == [
        "oai:exemplo:1",
        "oai:exemplo:2",
        "oai:exemplo:3",
        "oai:exemplo:4",
    ]
    assert route.call_count == 2
    first, second = (call.request.url.params for call in route.calls)
    assert first["verb"] == "ListRecords" and first["metadataPrefix"] == "oai_dc"
    # a segunda página usa só o verbo e o token, como manda o protocolo
    assert dict(second) == {"verb": "ListRecords", "resumptionToken": "tok-2"}
    assert sleeper.calls == [1.0]  # pausa entre as duas requisições


@respx.mock
async def test_record_fields_are_parsed(http: httpx.AsyncClient, sleeper: Sleeper) -> None:
    respx.get(OAI_URL).mock(side_effect=oai_server)
    records = [r async for r in make(http, sleeper).list_records()]
    first = records[0]
    assert first.sets == ["teses"] and first.datestamp == "2026-09-30" and not first.deleted
    assert first.dc is not None
    assert first.dc["title"] == [
        "Educação digital no ensino médio",
        "Digital education in high school",
    ]
    assert first.dc["type"][0] == "info:eu-repo/semantics/masterThesis"


@respx.mock
async def test_request_parameters(http: httpx.AsyncClient, sleeper: Sleeper) -> None:
    route = respx.get(OAI_URL).mock(return_value=xml_response("no_records_match.xml"))
    client = make(http, sleeper)
    _ = [
        r
        async for r in client.list_records(
            "oai_dc", set_spec="teses", from_date=date(2026, 1, 2), until_date=date(2026, 3, 4)
        )
    ]
    params = route.calls.last.request.url.params
    assert dict(params) == {
        "verb": "ListRecords",
        "metadataPrefix": "oai_dc",
        "set": "teses",
        "from": "2026-01-02",
        "until": "2026-03-04",
    }


@respx.mock
async def test_no_records_match_is_not_an_error(http: httpx.AsyncClient, sleeper: Sleeper) -> None:
    respx.get(OAI_URL).mock(return_value=xml_response("no_records_match.xml"))
    assert [r async for r in make(http, sleeper).list_records()] == []


@respx.mock
async def test_bad_resumption_token_is_an_error(http: httpx.AsyncClient, sleeper: Sleeper) -> None:
    respx.get(OAI_URL).mock(return_value=xml_response("bad_resumption_token.xml"))
    with pytest.raises(BadResumptionTokenError):
        _ = [r async for r in make(http, sleeper).list_records()]


@respx.mock
async def test_other_protocol_error(http: httpx.AsyncClient, sleeper: Sleeper) -> None:
    body = b'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><error code="cannotDisseminateFormat">x</error></OAI-PMH>'
    respx.get(OAI_URL).mock(return_value=httpx.Response(200, content=body))
    with pytest.raises(OaiProtocolError) as info:
        _ = [r async for r in make(http, sleeper).list_records("marcxml")]
    assert info.value.code == "cannotDisseminateFormat"


@respx.mock
async def test_dtd_and_external_entities_are_refused(
    http: httpx.AsyncClient, sleeper: Sleeper
) -> None:
    respx.get(OAI_URL).mock(return_value=xml_response("malicious_dtd.xml"))
    with pytest.raises(OaiXmlError, match="recusado"):
        await make(http, sleeper).identify()


@respx.mock
async def test_malformed_xml(http: httpx.AsyncClient, sleeper: Sleeper) -> None:
    respx.get(OAI_URL).mock(return_value=httpx.Response(200, content=b"<OAI-PMH><quebrado>"))
    with pytest.raises(OaiXmlError, match="malformado"):
        await make(http, sleeper).identify()


@respx.mock
async def test_503_with_retry_after_waits_and_retries(
    http: httpx.AsyncClient, sleeper: Sleeper
) -> None:
    route = respx.get(OAI_URL).mock(
        side_effect=[
            httpx.Response(503, headers={"Retry-After": "7"}),
            xml_response("identify.xml"),
        ]
    )
    info = await make(http, sleeper).identify()
    assert info["repositoryName"] == "Repositório de Exemplo"
    assert route.call_count == 2
    assert sleeper.calls == [7.0]


@respx.mock
async def test_503_gives_up_after_three_retries(http: httpx.AsyncClient, sleeper: Sleeper) -> None:
    route = respx.get(OAI_URL).mock(return_value=httpx.Response(503))
    with pytest.raises(OaiError, match="503"):
        await make(http, sleeper).identify()
    assert route.call_count == 4  # 1 + 3 novas tentativas
    assert sleeper.calls == [5.0, 5.0, 5.0]


@respx.mock
async def test_http_error_and_network_error(http: httpx.AsyncClient, sleeper: Sleeper) -> None:
    respx.get(OAI_URL).mock(return_value=httpx.Response(404))
    with pytest.raises(OaiError, match="404"):
        await make(http, sleeper).identify()
    respx.get(OAI_URL).mock(side_effect=httpx.ConnectError("sem rede"))
    with pytest.raises(OaiError, match="rede"):
        await make(http, sleeper).identify()


@respx.mock
async def test_max_pages_guard(http: httpx.AsyncClient, sleeper: Sleeper) -> None:
    route = respx.get(OAI_URL).mock(side_effect=oai_server)
    records = [r async for r in make(http, sleeper).list_records(max_pages=1)]
    assert len(records) == 2 and route.call_count == 1


@respx.mock
async def test_identify_and_sets(http: httpx.AsyncClient, sleeper: Sleeper) -> None:
    respx.get(OAI_URL).mock(side_effect=oai_server)
    client = make(http, sleeper)
    info = await client.identify()
    assert info["protocolVersion"] == "2.0" and info["granularity"] == "YYYY-MM-DD"
    assert [s async for s in client.list_sets()] == [("teses", "Teses"), ("artigos", "Artigos")]


@respx.mock
async def test_set_hierarchy_absent_is_empty(http: httpx.AsyncClient, sleeper: Sleeper) -> None:
    body = b'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><error code="noSetHierarchy"/></OAI-PMH>'
    respx.get(OAI_URL).mock(return_value=httpx.Response(200, content=body))
    assert [s async for s in make(http, sleeper).list_sets()] == []


@respx.mock
async def test_no_pause_before_first_request_and_zero_delay(
    http: httpx.AsyncClient, sleeper: Sleeper
) -> None:
    respx.get(OAI_URL).mock(side_effect=oai_server)
    _ = [r async for r in make(http, sleeper, delay=0).list_records()]
    assert sleeper.calls == []
