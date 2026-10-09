import httpx
import pytest
import respx

from app.connectors.base import SourcePage, SourceQuery
from app.core.config import Settings
from app.schemas.record import RecordOut, SourceRef
from app.schemas.search import SearchParams
from app.scraping.completion import complete_abstracts
from app.scraping.polite_scraper import PoliteScraper
from app.services.search_service import SearchService

pytestmark = pytest.mark.unit

HTML = {"Content-Type": "text/html"}
PAGE_WITH_ABSTRACT = '<meta name="citation_abstract" content="Resumo raspado.">'


def rec(n: int, *, abstract: str | None = None, url: str | None = "auto") -> RecordOut:
    return RecordOut(
        id=f"src:x:{n}",
        title=f"Trabalho de número {n} sem resumo na fonte original",
        abstract=abstract,
        url=f"https://repo.exemplo.org/p/{n}" if url == "auto" else url,
        sources=[SourceRef(source="x", source_id=str(n))],
    )


class FakeSource:
    slug = "openalex"
    name = "Fake"
    supports_year_sort = True

    def __init__(self, records: list[RecordOut]) -> None:
        self.records = records

    def is_enabled(self) -> bool:
        return True

    async def availability(self) -> tuple[bool, str | None]:
        return True, None

    async def search(self, query: SourceQuery) -> SourcePage:
        return SourcePage(records=[r.model_copy() for r in self.records], total=len(self.records))


async def no_sleep(seconds: float) -> None:
    return None


@pytest.fixture
async def scraper() -> PoliteScraper:
    async with httpx.AsyncClient() as client:
        yield PoliteScraper(client, sleep=no_sleep)  # type: ignore[misc]


def mock_site() -> respx.Route:
    respx.get("https://repo.exemplo.org/robots.txt").mock(return_value=httpx.Response(404))
    return respx.get(url__regex=r"https://repo\.exemplo\.org/p/\d+").mock(
        return_value=httpx.Response(200, headers=HTML, text=PAGE_WITH_ABSTRACT)
    )


@respx.mock
async def test_only_records_without_abstract_are_scraped(scraper: PoliteScraper) -> None:
    route = mock_site()
    records = [rec(1, abstract="Já tem resumo"), rec(2), rec(3, url=None)]
    result = await complete_abstracts(records, scraper)
    assert [r.abstract for r in result] == ["Já tem resumo", "Resumo raspado.", None]
    assert route.call_count == 1  # só o registro 2
    assert records[1].abstract is None  # a lista original não é alterada


@respx.mock
async def test_at_most_five_records_per_search(scraper: PoliteScraper) -> None:
    route = mock_site()
    result = await complete_abstracts([rec(i) for i in range(8)], scraper)
    assert route.call_count == 5
    assert sum(1 for r in result if r.abstract) == 5


@respx.mock
async def test_failures_are_silent(scraper: PoliteScraper) -> None:
    respx.get("https://repo.exemplo.org/robots.txt").mock(return_value=httpx.Response(404))
    respx.get(url__regex=r"https://repo\.exemplo\.org/p/\d+").mock(
        side_effect=httpx.ConnectError("sem rede")
    )
    result = await complete_abstracts([rec(1), rec(2)], scraper)
    assert [r.abstract for r in result] == [None, None]


@respx.mock
async def test_nothing_to_do_makes_no_request(scraper: PoliteScraper) -> None:
    route = mock_site()
    await complete_abstracts([rec(1, abstract="ok")], scraper)
    assert not route.called


@respx.mock
async def test_scraping_disabled_makes_no_call() -> None:
    route = mock_site()
    robots = respx.get("https://repo.exemplo.org/robots.txt")
    service = SearchService(
        [FakeSource([rec(1)])],
        Settings(_env_file=None, scraping_enabled=False),  # type: ignore[call-arg]
    )
    response = await service.search(SearchParams(q="educação"))
    assert response.results[0].abstract is None
    assert not route.called and not robots.called


@respx.mock
async def test_scraping_enabled_completes_abstract_without_touching_sources_status(
    scraper: PoliteScraper,
) -> None:
    route = mock_site()
    settings = Settings(_env_file=None, scraping_enabled=True)  # type: ignore[call-arg]
    service = SearchService([FakeSource([rec(1)])], settings, scraper=scraper)
    disabled = SearchService([FakeSource([rec(1)])], Settings(_env_file=None))  # type: ignore[call-arg]
    with_scraping = await service.search(SearchParams(q="educação"))
    without = await disabled.search(SearchParams(q="educação"))
    assert route.called
    assert with_scraping.results[0].abstract == "Resumo raspado."
    assert with_scraping.sources_status == without.sources_status
    await service.aclose()


@respx.mock
async def test_service_creates_and_closes_its_own_scraper_when_enabled() -> None:
    route = mock_site()
    settings = Settings(_env_file=None, scraping_enabled=True)  # type: ignore[call-arg]
    service = SearchService([FakeSource([rec(1)])], settings)
    response = await service.search(SearchParams(q="educação"))
    assert response.results[0].abstract == "Resumo raspado." and route.called
    await service.aclose()
    await service.aclose()  # idempotente
