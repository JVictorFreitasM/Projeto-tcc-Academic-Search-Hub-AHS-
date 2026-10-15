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

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "core"
REAL = (
    FIXTURES / "search_ok.json"
)  # resposta REAL da API (15/10/2026, `q=educação`), sem `fullText`
FIXTURE = (
    FIXTURES / "edge_cases.json"
)  # sintética e permanente: casos de borda que o real não cobre
KEY = "CHAVE-CORE-SECRETA"


def load_fixture() -> dict:  # type: ignore[type-arg]
    """Casos de borda (sintética): os testes detalhados de mapeamento usam esta."""
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def load_real() -> dict:  # type: ignore[type-arg]
    return json.loads(REAL.read_text(encoding="utf-8"))


def connector(key: str = KEY) -> CoreConnector:
    return CoreConnector(Settings(_env_file=None, core_api_key=key))  # type: ignore[call-arg]


def test_edge_case_fixture_is_synthetic_and_permanent_but_the_main_one_is_real() -> None:
    edge = load_fixture()
    assert edge.get("_synthetic") is True and edge.get("_permanent") is True
    assert "_synthetic" not in load_real()


@respx.mock
async def test_real_core_response_maps_to_valid_records() -> None:
    """Resposta REAL do CORE (15/10/2026): todo trabalho vira um registro válido."""
    real = load_real()
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=real))
    page = await connector().search(SourceQuery(q="educação", page_size=5))
    assert page.status is SourceStatus.OK and page.message is None
    assert page.total == real["totalHits"] == 995_013
    assert len(page.records) == len(real["results"]) == 5
    first, _, article, *_ = page.records
    assert (
        first.id == "src:core:303833472"
        and first.title == "Educação profissional, educação para o futuro"
    )
    assert (first.year, first.language) == (2022, "pt")
    assert [a.name for a in first.authors] == ["L. Capucha"]
    assert first.type is RecordType.OTHER  # `documentType` ausente na maioria dos registros reais
    assert first.url == "https://core.ac.uk/works/303833472"
    assert first.pdf_url == "https://core.ac.uk/download/672945974.pdf"
    assert first.abstract is not None and first.abstract.startswith("A European Political Strategy")
    # "research article" é o valor real de `documentType` para artigos (antes caía em "outro")
    assert article.id == "src:core:398173363" and article.type is RecordType.ARTICLE
    assert [a.name for a in article.authors][:2] == ["Belmiro Cabrito", "Angela Lara"]


def test_real_response_has_no_secret_and_no_full_text() -> None:
    text = REAL.read_text(encoding="utf-8")
    assert "Bearer" not in text and "api_key" not in text.lower()
    assert all("fullText" not in work for work in load_real()["results"])  # enorme e não usado


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
    assert request.url.params["exclude"] == "fullText"  # o texto completo não é usado e pesa muito
    assert (
        request.url.params["q"] == "(ensino médio) AND yearPublished>=2018 AND yearPublished<=2022"
    )
    assert KEY not in str(request.url)


def test_build_query_string_types() -> None:
    q, local = build_query_string(SourceQuery(q="x", types=(RecordType.THESIS,)))
    assert q == '(x) AND (documentType:"thesis")'
    assert local is False
    q, local = build_query_string(SourceQuery(q="x", types=(RecordType.ARTICLE,)))
    assert q == '(x) AND (documentType:"research article" OR documentType:"journal article")'
    q, _ = build_query_string(SourceQuery(q="x", types=(RecordType.BOOK,)))
    assert q == '(x) AND (documentType:"book")'
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
    """Sintaxe confirmada com chave real em 15/10/2026: `authors:A AND authors:B`. A forma
    `authors:(A AND B)` (AND dentro de parênteses) faz o CORE responder 500."""
    q, local = build_query_string(SourceQuery(q="Paulo Freire", field="author"))
    assert q == "authors:Paulo AND authors:Freire" and local is False
    assert "(" not in q  # parênteses com AND quebram a consulta no CORE
    # vírgula e aspas do usuário não quebram a consulta; a ordem do nome não importa
    assert build_query_string(SourceQuery(q='Freire, "Paulo"', field="author"))[0] == (
        "authors:Freire AND authors:Paulo"
    )
    assert build_query_string(SourceQuery(q="Saviani", field="author"))[0] == "authors:Saviani"
    assert build_query_string(SourceQuery(q="Jean-Paul O'Neil", field="author"))[0] == (
        "authors:Jean-Paul AND authors:O'Neil"
    )
    # símbolos de busca do usuário (parênteses, dois pontos, curinga) não chegam à consulta
    assert build_query_string(SourceQuery(q="(a) b:c *", field="author"))[0] == (
        "authors:a AND authors:b AND authors:c"
    )
    q, _ = build_query_string(
        SourceQuery(q="Freire", field="author", year_from=2000, types=(RecordType.THESIS,))
    )
    assert q == 'authors:Freire AND yearPublished>=2000 AND (documentType:"thesis")'
    assert build_query_string(SourceQuery(q="Freire"))[0] == "(Freire)"  # tema: igual a antes


@respx.mock
async def test_core_timeout_is_longer_than_the_default_because_the_api_is_slow() -> None:
    """Medido em 15/10/2026: 3 a 10 s por busca; o padrão de 10 s estouraria."""
    captured: dict[str, float] = {}
    real_client = httpx.AsyncClient

    def spy(*args: object, **kwargs: object) -> httpx.AsyncClient:
        captured["read"] = kwargs["timeout"].read  # type: ignore[union-attr, attr-defined]
        return real_client(*args, **kwargs)  # type: ignore[arg-type]

    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=load_real()))
    import app.connectors.http as http_module

    original = http_module.httpx.AsyncClient
    http_module.httpx.AsyncClient = spy  # type: ignore[misc, assignment]
    try:
        await connector().search(SourceQuery(q="educação"))
    finally:
        http_module.httpx.AsyncClient = original  # type: ignore[misc]
    assert captured["read"] >= 25.0
