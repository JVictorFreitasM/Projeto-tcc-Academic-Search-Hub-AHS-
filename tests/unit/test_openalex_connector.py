import json
from pathlib import Path

import httpx
import pytest
import respx

from app.connectors.base import SourceQuery, SourceStatus
from app.connectors.openalex import (
    BASE_URL,
    OpenAlexConnector,
    build_filter,
    reconstruct_abstract,
    work_to_record,
)
from app.core.config import Settings
from app.schemas.common import RecordType
from app.schemas.record import RecordOut

pytestmark = pytest.mark.unit

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "openalex" / "search_ok.json"
KEY = "CHAVE-SECRETA-123"


def load_fixture() -> dict:  # type: ignore[type-arg]
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def connector(key: str = KEY) -> OpenAlexConnector:
    return OpenAlexConnector(Settings(_env_file=None, openalex_api_key=key))  # type: ignore[call-arg]


def test_fixture_is_marked_synthetic() -> None:
    """Enquanto a fixture for sintética, a pendência fica visível (DECISOES.md e OS-030)."""
    assert load_fixture().get("_synthetic") is True


def test_reconstruct_abstract_example_from_spec() -> None:
    assert reconstruct_abstract({"A": [0], "casa": [1, 3], "bonita": [2]}) == "A casa bonita casa"


def test_reconstruct_abstract_edge_cases() -> None:
    assert reconstruct_abstract(None) is None
    assert reconstruct_abstract({}) is None
    assert reconstruct_abstract({"a": []}) is None
    assert reconstruct_abstract({"depois": [5], "antes": [1]}) == "antes depois"  # lacunas
    long = reconstruct_abstract({"x" * 100: list(range(0, 400))})
    assert long is not None and len(long) <= 20_000


@respx.mock
async def test_search_returns_valid_records_and_total() -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=load_fixture()))
    page = await connector().search(SourceQuery(q="educação", page_size=3))
    assert page.status is SourceStatus.OK
    assert page.total == 12345
    assert len(page.records) == 3
    assert all(isinstance(r, RecordOut) for r in page.records)

    full, minimal, thesis = page.records
    assert full.id == "doi:10.1234/exemplo.2021.001"
    assert full.title == "Letramento digital na educação básica"
    assert full.doi == "10.1234/exemplo.2021.001"
    assert full.year == 2021
    assert full.type is RecordType.ARTICLE
    assert full.language == "pt"
    assert [a.name for a in full.authors] == ["Maria Souza", "João Pereira"]  # autor sem nome sai
    assert full.authors[0].orcid == "0000-0002-1825-0097"
    assert full.abstract == "Este estudo analisa o letramento digital o uso de tecnologias."
    assert full.url == "https://revista.exemplo.org/artigo/1"
    assert full.pdf_url == "https://revista.exemplo.org/artigo/1.pdf"
    assert full.keywords == ["Digital literacy", "Education"]
    assert full.sources[0].model_dump() == {
        "source": "openalex",
        "source_id": "W1000000001",
        "url": "https://openalex.org/W1000000001",
    }

    # obra mínima: sem DOI, sem resumo, sem autores
    assert minimal.id == "src:openalex:W1000000002"
    assert minimal.doi is None and minimal.abstract is None and minimal.authors == []
    assert minimal.year is None and minimal.url is None
    assert minimal.type is RecordType.OTHER

    # endereços fora de http/https são descartados; a URL cai para o DOI
    assert thesis.type is RecordType.THESIS
    assert thesis.url == "https://doi.org/10.5555/tese.2019.7"
    assert thesis.pdf_url is None


@respx.mock
async def test_no_record_has_unsafe_url() -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=load_fixture()))
    page = await connector().search(SourceQuery(q="x"))
    for record in page.records:
        for value in (record.url, record.pdf_url, *(s.url for s in record.sources)):
            assert value is None or value.startswith(("http://", "https://"))


@respx.mock
async def test_request_parameters() -> None:
    route = respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=load_fixture()))
    await connector().search(
        SourceQuery(
            q="educação básica",
            page=3,
            page_size=7,
            year_from=2018,
            year_to=2022,
            types=(RecordType.ARTICLE, RecordType.BOOK),
            sort="year_desc",
        )
    )
    params = route.calls.last.request.url.params
    assert params["search"] == "educação básica"
    assert params["per-page"] == "7"
    assert params["page"] == "3"
    assert params["api_key"] == KEY
    assert params["filter"] == "publication_year:2018-2022,type:article|book|book-chapter"
    assert params["sort"] == "publication_year:desc"


def test_build_filter_variants() -> None:
    assert build_filter(SourceQuery(q="x")) == (None, False)
    assert build_filter(SourceQuery(q="x", year_from=2020)) == ("publication_year:>2019", False)
    assert build_filter(SourceQuery(q="x", year_to=2020)) == ("publication_year:<2021", False)
    assert build_filter(SourceQuery(q="x", types=(RecordType.THESIS,))) == (
        "type:dissertation",
        False,
    )
    assert build_filter(SourceQuery(q="x", types=(RecordType.OTHER, RecordType.BOOK))) == (
        None,
        True,
    )


@respx.mock
async def test_type_other_is_filtered_locally() -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=load_fixture()))
    page = await connector().search(SourceQuery(q="x", types=(RecordType.OTHER,)))
    assert [r.type for r in page.records] == [RecordType.OTHER]


@respx.mock
async def test_page_size_above_limit_is_truncated_with_message() -> None:
    route = respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=load_fixture()))
    page = await connector().search(SourceQuery(q="x", page_size=250))
    assert route.calls.last.request.url.params["per-page"] == "100"
    assert page.message is not None and "100" in page.message


@respx.mock
async def test_disabled_without_key_makes_no_request() -> None:
    route = respx.get(BASE_URL).mock(return_value=httpx.Response(200, json={}))
    conn = connector(key="")
    assert conn.is_enabled() is False
    page = await conn.search(SourceQuery(q="x"))
    assert page.status is SourceStatus.DISABLED
    assert not route.called


@respx.mock
async def test_rate_limited() -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(429, headers={"Retry-After": "30"}))
    page = await connector().search(SourceQuery(q="x"))
    assert page.status is SourceStatus.RATE_LIMITED
    assert page.message is not None and "30" in page.message


@respx.mock
async def test_timeout() -> None:
    respx.get(BASE_URL).mock(side_effect=httpx.ReadTimeout("lento"))
    page = await connector().search(SourceQuery(q="x"))
    assert page.status is SourceStatus.TIMEOUT


@respx.mock
@pytest.mark.parametrize("status", [401, 403])
async def test_invalid_key_message_does_not_expose_key(status: int) -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(status))
    page = await connector().search(SourceQuery(q="x"))
    assert page.status is SourceStatus.ERROR
    assert page.message == "Chave do OpenAlex inválida ou sem permissão."
    assert KEY not in (page.message or "")


@respx.mock
async def test_other_http_error_and_unexpected_body() -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(500))
    assert (await connector().search(SourceQuery(q="x"))).status is SourceStatus.ERROR
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json={"sem": "results"}))
    page = await connector().search(SourceQuery(q="x"))
    assert page.status is SourceStatus.ERROR
    assert page.message == "Resposta inesperada da fonte."


def test_work_without_title_or_id_is_ignored() -> None:
    assert work_to_record({"id": "https://openalex.org/W1", "title": None}) is None
    assert work_to_record({"title": "Sem id"}) is None


def test_work_with_invalid_year_keeps_record() -> None:
    record = work_to_record(
        {"id": "https://openalex.org/W9", "title": "T", "publication_year": 99999}
    )
    assert record is not None and record.year is None
