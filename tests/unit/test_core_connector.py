import json
from pathlib import Path

import httpx
import pytest
import respx

from app.connectors.base import SourceQuery, SourceStatus
from app.connectors.core_api import BASE_URL, CoreConnector, build_query_string, work_to_record
from app.core.config import Settings
from app.schemas.common import RecordType

pytestmark = pytest.mark.unit

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "core" / "search_ok.json"
KEY = "CHAVE-CORE-SECRETA"


def load_fixture() -> dict:  # type: ignore[type-arg]
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def connector(key: str = KEY) -> CoreConnector:
    return CoreConnector(Settings(_env_file=None, core_api_key=key))  # type: ignore[call-arg]


def test_fixture_is_marked_synthetic() -> None:
    assert load_fixture().get("_synthetic") is True


@respx.mock
async def test_search_returns_valid_records_total_and_ignored_count() -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=load_fixture()))
    page = await connector().search(SourceQuery(q="educação", page_size=4))
    assert page.status is SourceStatus.OK
    assert page.total == 4321
    assert len(page.records) == 3  # o sem título foi descartado
    assert page.message == "1 resultados sem título foram ignorados."

    full, thesis, book = page.records
    assert full.id == "doi:10.4321/formacao.2020.5"
    assert full.title == "Formação docente e tecnologias digitais"
    assert full.abstract == "Estudo sobre formação docente. & tecnologias."
    assert [a.name for a in full.authors] == ["Carlos Almeida", "Beatriz Nunes"]
    assert full.year == 2020
    assert full.type is RecordType.ARTICLE
    assert full.language == "pt"
    assert full.url == "https://core.ac.uk/works/100200300"  # link "display"
    assert full.pdf_url == "https://core.ac.uk/download/pdf/100200300.pdf"
    assert full.sources[0].model_dump() == {
        "source": "core",
        "source_id": "100200300",
        "url": "https://core.ac.uk/works/100200300",
    }

    assert thesis.id == "src:core:100200301"
    assert thesis.type is RecordType.THESIS
    assert thesis.year == 2018  # vem de publishedDate
    assert thesis.doi is None and thesis.abstract is None and thesis.language is None
    assert thesis.url == "https://core.ac.uk/works/100200301"  # cai para a página do CORE

    assert book.pdf_url is None  # javascript: descartado
    assert book.url == "https://core.ac.uk/works/100200303"
    assert book.language is None


@respx.mock
async def test_request_uses_bearer_header_and_pagination() -> None:
    route = respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=load_fixture()))
    await connector().search(
        SourceQuery(q="ensino médio", page=3, page_size=10, year_from=2018, year_to=2022)
    )
    request = route.calls.last.request
    assert request.headers["Authorization"] == f"Bearer {KEY}"
    assert request.url.params["limit"] == "10"
    assert request.url.params["offset"] == "20"
    assert (
        request.url.params["q"] == "(ensino médio) AND yearPublished>=2018 AND yearPublished<=2022"
    )
    assert KEY not in str(request.url)


def test_build_query_string_types() -> None:
    q, local = build_query_string(SourceQuery(q="x", types=(RecordType.THESIS,)))
    assert q == '(x) AND (documentType:"thesis")'
    assert local is False
    q, local = build_query_string(SourceQuery(q="x", types=(RecordType.ARTICLE,)))
    assert 'documentType:"research" OR documentType:"journal"' in q
    q, local = build_query_string(SourceQuery(q="x", types=(RecordType.THESIS, RecordType.OTHER)))
    assert q == "(x)" and local is True
    assert build_query_string(SourceQuery(q="  x\x00 "))[0] == "(x)"


@respx.mock
async def test_type_without_remote_equivalent_is_filtered_locally() -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=load_fixture()))
    page = await connector().search(SourceQuery(q="x", types=(RecordType.BOOK, RecordType.OTHER)))
    assert [r.type for r in page.records] == [RecordType.BOOK]


@respx.mock
async def test_limit_above_maximum_is_truncated_with_message() -> None:
    route = respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=load_fixture()))
    page = await connector().search(SourceQuery(q="x", page_size=500))
    assert route.calls.last.request.url.params["limit"] == "100"
    assert page.message is not None and "100" in page.message


@respx.mock
async def test_disabled_without_key() -> None:
    route = respx.get(BASE_URL).mock(return_value=httpx.Response(200, json={}))
    conn = connector(key="")
    assert conn.is_enabled() is False
    page = await conn.search(SourceQuery(q="x"))
    assert page.status is SourceStatus.DISABLED
    assert not route.called


@respx.mock
async def test_rate_limited_mentions_retry_after() -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(429, headers={"Retry-After": "10"}))
    page = await connector().search(SourceQuery(q="x"))
    assert page.status is SourceStatus.RATE_LIMITED
    assert page.message is not None and "10" in page.message


@respx.mock
async def test_timeout() -> None:
    respx.get(BASE_URL).mock(side_effect=httpx.ConnectTimeout("lento"))
    assert (await connector().search(SourceQuery(q="x"))).status is SourceStatus.TIMEOUT


@respx.mock
@pytest.mark.parametrize("status", [401, 403])
async def test_auth_error(status: int) -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(status))
    page = await connector().search(SourceQuery(q="x"))
    assert page.status is SourceStatus.ERROR
    assert page.message == "Chave do CORE inválida ou sem permissão."
    assert KEY not in (page.message or "")


@respx.mock
async def test_unexpected_body() -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json={"sem": "results"}))
    page = await connector().search(SourceQuery(q="x"))
    assert page.status is SourceStatus.ERROR


def test_work_edge_cases() -> None:
    assert work_to_record({"id": 1, "title": "   "}) is None
    assert work_to_record({"title": "Sem id"}) is None
    record = work_to_record({"id": 7, "title": "T", "language": "por", "yearPublished": 99999})
    assert record is not None
    assert record.language == "pt" and record.year is None
    # sem landing, usa o primeiro endereço de texto completo válido
    record = work_to_record(
        {"id": 8, "title": "T", "sourceFulltextUrls": ["ftp://x", "https://ok.org/a"]}
    )
    assert record is not None and record.url == "https://ok.org/a"


def test_build_query_string_by_author_uses_the_authors_field() -> None:
    """[VERIFICAR] sintaxe `authors:` do CORE v3: ainda sem chave real para confirmar."""
    q, local = build_query_string(SourceQuery(q="Paulo Freire", field="author"))
    assert q == 'authors:("Paulo" AND "Freire")' and local is False
    # vírgula e aspas do usuário não quebram a consulta; a ordem do nome não importa
    assert build_query_string(SourceQuery(q='Freire, "Paulo"', field="author"))[0] == (
        'authors:("Freire" AND "Paulo")'
    )
    q, _ = build_query_string(
        SourceQuery(q="Freire", field="author", year_from=2000, types=(RecordType.THESIS,))
    )
    assert q == 'authors:("Freire") AND yearPublished>=2000 AND (documentType:"thesis")'
    assert build_query_string(SourceQuery(q="Freire"))[0] == "(Freire)"  # tema: igual a antes
