import json
from pathlib import Path

import httpx
import pytest
import respx

from app.connectors.base import SourceQuery, SourceStatus
from app.connectors.bdtd_api import BASE_URL, BdtdConnector, build_params, record_to_out
from app.core.config import Settings
from app.schemas.common import RecordType

pytestmark = pytest.mark.unit

REAL = Path(__file__).resolve().parents[1] / "fixtures" / "bdtd" / "search_ok.json"


def load_real() -> dict:  # type: ignore[type-arg]
    """Resposta REAL da API do VuFind da BDTD (15/10/2026, "educação inclusiva")."""
    return json.loads(REAL.read_text(encoding="utf-8"))


def connector(enabled: bool = True) -> BdtdConnector:
    return BdtdConnector(Settings(_env_file=None, bdtd_enabled=enabled))  # type: ignore[call-arg]


def values(params: list[tuple[str, str]], key: str) -> list[str]:
    return [v for k, v in params if k == key]


def test_real_response_maps_every_record() -> None:
    data = load_real()
    records = [record_to_out(item) for item in data["records"]]
    assert len(records) == 5 and all(r is not None for r in records)
    first = records[0]
    assert first is not None
    assert first.title == "O direito à educação e educação inclusiva"
    assert first.year == 2022 and first.type is RecordType.THESIS and first.language == "pt"
    assert first.authors[0].name == "Gilberto Ghiuro Junior"  # "Sobrenome, Nome" invertido
    assert first.abstract and first.url == "https://repositorio.pucsp.br/jspui/handle/handle/25961"
    assert first.sources[0].source == "bdtd"
    assert first.sources[0].url.startswith("https://bdtd.ibict.br/vufind/Record/")
    assert first.id == "src:bdtd:" + data["records"][0]["id"]
    assert "Educação inclusiva" in first.keywords
    assert not any("::" in k for k in first.keywords)  # área do CNPq fica de fora
    assert {r.type for r in records if r} == {RecordType.THESIS}


def test_author_names_lose_the_institution_tag_and_the_all_caps() -> None:
    record = record_to_out(
        {
            "id": "1",
            "title": "T",
            "primaryAuthors": [
                "Almeida, Regiceli Bento [UNESP]",
                "SÁ, PAULO CÉSAR FREIRE",
                " [X] ",
            ],
        }
    )
    assert record is not None
    assert [a.name for a in record.authors] == ["Regiceli Bento Almeida", "Paulo César Freire Sá"]


def test_record_without_title_or_id_is_ignored() -> None:
    assert record_to_out({"id": "x", "title": "  "}) is None
    assert record_to_out({"title": "Sem id"}) is None


def test_minimal_record_falls_back_to_the_bdtd_page() -> None:
    record = record_to_out({"id": "ABC-1", "title": "Mínimo"})
    assert record is not None
    assert record.url == "https://bdtd.ibict.br/vufind/Record/ABC-1"
    assert record.year is None and record.abstract is None and record.type is RecordType.OTHER


def test_params_for_theme_author_year_and_sort() -> None:
    theme = build_params(SourceQuery(q="educação", page=2), 20)
    assert values(theme, "type") == ["AllFields"] and values(theme, "page") == ["2"]
    assert values(theme, "filter[]") == [] and values(theme, "sort") == []
    assert "summary" in values(theme, "field[]")
    author = build_params(SourceQuery(q="Paulo Freire", field="author"), 20)
    assert values(author, "type") == ["Author"] and values(author, "lookfor") == ["Paulo Freire"]
    years = build_params(SourceQuery(q="x", year_from=2018, year_to=2022, sort="year_desc"), 5)
    assert values(years, "filter[]") == ["publishDate:[2018 TO 2022]"]
    assert values(years, "sort") == ["year"]
    assert values(build_params(SourceQuery(q="x", year_from=2020), 5), "filter[]") == [
        "publishDate:[2020 TO *]"
    ]
    assert values(build_params(SourceQuery(q="x", year_to=2005), 5), "filter[]") == [
        "publishDate:[* TO 2005]"
    ]


@respx.mock
async def test_search_returns_records_and_total() -> None:
    route = respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=load_real()))
    page = await connector().search(SourceQuery(q="educação inclusiva", page_size=5))
    assert page.status is SourceStatus.OK and page.total == 9364 and len(page.records) == 5
    assert route.calls.last.request.url.params.get_list("field[]")[0] == "id"


@respx.mock
async def test_empty_result_has_no_records_key() -> None:
    respx.get(BASE_URL).mock(
        return_value=httpx.Response(200, json={"resultCount": 0, "status": "OK"})
    )
    page = await connector().search(SourceQuery(q="xyzqwkjhzzzq"))
    assert page.status is SourceStatus.OK and page.total == 0 and page.records == []


@respx.mock
async def test_type_other_than_thesis_skips_the_call() -> None:
    route = respx.get(BASE_URL)
    page = await connector().search(SourceQuery(q="x", types=(RecordType.ARTICLE,)))
    assert page.total == 0 and page.records == [] and not route.called
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=load_real()))
    page = await connector().search(
        SourceQuery(q="x", types=(RecordType.ARTICLE, RecordType.THESIS))
    )
    assert len(page.records) == 5


@respx.mock
async def test_page_size_is_capped() -> None:
    route = respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=load_real()))
    page = await connector().search(SourceQuery(q="x", page_size=500))
    assert route.calls.last.request.url.params["limit"] == "100"
    assert page.message and "100" in page.message


async def test_disabled_makes_no_call() -> None:
    conn = connector(enabled=False)
    assert not conn.is_enabled()
    assert await conn.availability() == (False, "Fonte desligada na configuração.")
    page = await conn.search(SourceQuery(q="x"))
    assert page.status is SourceStatus.DISABLED


@respx.mock
async def test_failures_become_status() -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json={"status": "ERROR"}))
    assert (await connector().search(SourceQuery(q="x"))).status is SourceStatus.ERROR
    respx.get(BASE_URL).mock(return_value=httpx.Response(429, headers={"Retry-After": "7"}))
    assert (await connector().search(SourceQuery(q="x"))).status is SourceStatus.RATE_LIMITED
    respx.get(BASE_URL).mock(side_effect=httpx.ReadTimeout("lenta"))
    assert (await connector().search(SourceQuery(q="x"))).status is SourceStatus.TIMEOUT
