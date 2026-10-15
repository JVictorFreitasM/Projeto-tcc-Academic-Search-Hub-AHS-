import httpx
import pytest
import respx

from app import __version__
from app.connectors.http import make_client
from app.core.config import Settings
from app.scraping.polite_scraper import MAX_PAGE_BYTES, PoliteScraper

pytestmark = pytest.mark.unit

HTML = {"Content-Type": "text/html; charset=utf-8"}
PAGE = "https://repo.exemplo.org/handle/1/1"
ROBOTS = "https://repo.exemplo.org/robots.txt"


class FakeTime:
    """Relógio simulado: dormir avança o tempo, sem espera real."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


@pytest.fixture
def fake() -> FakeTime:
    return FakeTime()


@pytest.fixture
async def scraper(fake: FakeTime) -> PoliteScraper:
    settings = Settings(_env_file=None, contact_email="dev@exemplo.com")  # type: ignore[call-arg]
    async with make_client(settings) as client:
        yield PoliteScraper(client, clock=fake.clock, sleep=fake.sleep)  # type: ignore[misc]


@respx.mock
async def test_disallow_all_never_requests_the_page(scraper: PoliteScraper) -> None:
    respx.get(ROBOTS).mock(return_value=httpx.Response(200, text="User-agent: *\nDisallow: /\n"))
    page = respx.get(PAGE).mock(return_value=httpx.Response(200, headers=HTML, text="<p>x</p>"))
    assert await scraper.fetch(PAGE) is None
    assert not page.called


@respx.mock
async def test_specific_disallow_path_only(scraper: PoliteScraper) -> None:
    respx.get(ROBOTS).mock(
        return_value=httpx.Response(200, text="User-agent: *\nDisallow: /privado/\n")
    )
    respx.get("https://repo.exemplo.org/privado/1").mock(return_value=httpx.Response(200))
    respx.get(PAGE).mock(return_value=httpx.Response(200, headers=HTML, text="<p>ok</p>"))
    assert await scraper.fetch("https://repo.exemplo.org/privado/1") is None
    assert await scraper.fetch(PAGE) == "<p>ok</p>"


@respx.mock
async def test_agent_specific_rule_for_our_user_agent(scraper: PoliteScraper) -> None:
    respx.get(ROBOTS).mock(
        return_value=httpx.Response(200, text="User-agent: AcademicSearchHub\nDisallow: /\n")
    )
    page = respx.get(PAGE).mock(return_value=httpx.Response(200, headers=HTML, text="x"))
    assert await scraper.fetch(PAGE) is None and not page.called


@respx.mock
async def test_missing_robots_txt_means_allowed(scraper: PoliteScraper) -> None:
    respx.get(ROBOTS).mock(return_value=httpx.Response(404))
    respx.get(PAGE).mock(return_value=httpx.Response(200, headers=HTML, text="<p>ok</p>"))
    assert await scraper.fetch(PAGE) == "<p>ok</p>"


@respx.mock
async def test_robots_server_error_is_treated_as_forbidden(scraper: PoliteScraper) -> None:
    respx.get(ROBOTS).mock(return_value=httpx.Response(503))
    page = respx.get(PAGE).mock(return_value=httpx.Response(200, headers=HTML, text="x"))
    assert await scraper.fetch(PAGE) is None and not page.called


@respx.mock
async def test_robots_network_error_is_treated_as_forbidden(scraper: PoliteScraper) -> None:
    respx.get(ROBOTS).mock(side_effect=httpx.ConnectError("sem rede"))
    page = respx.get(PAGE).mock(return_value=httpx.Response(200, headers=HTML, text="x"))
    assert await scraper.fetch(PAGE) is None and not page.called


@respx.mock
async def test_robots_is_cached_per_domain(scraper: PoliteScraper) -> None:
    robots = respx.get(ROBOTS).mock(return_value=httpx.Response(404))
    respx.get(url__startswith="https://repo.exemplo.org/handle/").mock(
        return_value=httpx.Response(200, headers=HTML, text="x")
    )
    await scraper.fetch(PAGE)
    await scraper.fetch("https://repo.exemplo.org/handle/1/2")
    assert robots.call_count == 1


@respx.mock
async def test_minimum_pause_per_domain_is_respected(
    scraper: PoliteScraper, fake: FakeTime
) -> None:
    respx.get(ROBOTS).mock(return_value=httpx.Response(404))
    respx.get(url__startswith="https://repo.exemplo.org/handle/").mock(
        return_value=httpx.Response(200, headers=HTML, text="x")
    )
    await scraper.fetch(PAGE)
    await scraper.fetch("https://repo.exemplo.org/handle/1/2")
    # robots.txt, página 1 e página 2 são 3 requisições ao mesmo domínio: 2 esperas de 2 s
    assert fake.sleeps == [2.0, 2.0]


@respx.mock
async def test_no_pause_between_different_domains(scraper: PoliteScraper, fake: FakeTime) -> None:
    respx.get(url__regex=r"https://(a|b)\.exemplo\.org/robots\.txt").mock(
        return_value=httpx.Response(404)
    )
    respx.get(url__regex=r"https://(a|b)\.exemplo\.org/p").mock(
        return_value=httpx.Response(200, headers=HTML, text="x")
    )
    await scraper.fetch("https://a.exemplo.org/p")
    sleeps_after_first = len(fake.sleeps)
    await scraper.fetch("https://b.exemplo.org/p")
    assert len(fake.sleeps) == sleeps_after_first + 1  # só a pausa interna de b (robots -> página)


@respx.mock
async def test_pause_not_needed_when_enough_time_has_passed(
    scraper: PoliteScraper, fake: FakeTime
) -> None:
    respx.get(ROBOTS).mock(return_value=httpx.Response(404))
    respx.get(url__startswith="https://repo.exemplo.org/handle/").mock(
        return_value=httpx.Response(200, headers=HTML, text="x")
    )
    await scraper.fetch(PAGE)
    fake.sleeps.clear()
    fake.now += 60
    await scraper.fetch("https://repo.exemplo.org/handle/1/2")
    assert fake.sleeps == []


@respx.mock
async def test_non_html_content_type_is_not_returned(scraper: PoliteScraper) -> None:
    respx.get(ROBOTS).mock(return_value=httpx.Response(404))
    respx.get(PAGE).mock(
        return_value=httpx.Response(
            200, headers={"Content-Type": "application/pdf"}, content=b"%PDF"
        )
    )
    assert await scraper.fetch(PAGE) is None


@respx.mock
@pytest.mark.parametrize("status", [401, 403, 404, 500])
async def test_pages_that_need_login_or_fail_are_skipped(
    scraper: PoliteScraper, status: int
) -> None:
    respx.get(ROBOTS).mock(return_value=httpx.Response(404))
    respx.get(PAGE).mock(return_value=httpx.Response(status, headers=HTML, text="x"))
    assert await scraper.fetch(PAGE) is None


@respx.mock
async def test_page_larger_than_one_megabyte_is_skipped(scraper: PoliteScraper) -> None:
    respx.get(ROBOTS).mock(return_value=httpx.Response(404))
    respx.get(PAGE).mock(
        return_value=httpx.Response(200, headers=HTML, content=b"a" * (MAX_PAGE_BYTES + 1))
    )
    assert await scraper.fetch(PAGE) is None


@respx.mock
async def test_redirect_to_forbidden_domain_is_not_followed(scraper: PoliteScraper) -> None:
    respx.get(ROBOTS).mock(return_value=httpx.Response(404))
    respx.get(PAGE).mock(
        return_value=httpx.Response(302, headers={"Location": "https://outro.exemplo.org/x"})
    )
    respx.get("https://outro.exemplo.org/robots.txt").mock(
        return_value=httpx.Response(200, text="User-agent: *\nDisallow: /\n")
    )
    target = respx.get("https://outro.exemplo.org/x").mock(
        return_value=httpx.Response(200, headers=HTML, text="x")
    )
    assert await scraper.fetch(PAGE) is None and not target.called


@respx.mock
async def test_redirect_to_allowed_page_is_followed(scraper: PoliteScraper) -> None:
    respx.get(ROBOTS).mock(return_value=httpx.Response(404))
    respx.get(PAGE).mock(return_value=httpx.Response(301, headers={"Location": "/novo"}))
    respx.get("https://repo.exemplo.org/novo").mock(
        return_value=httpx.Response(200, headers=HTML, text="<p>novo</p>")
    )
    assert await scraper.fetch(PAGE) == "<p>novo</p>"


@respx.mock
async def test_redirect_loop_gives_up(scraper: PoliteScraper) -> None:
    respx.get(ROBOTS).mock(return_value=httpx.Response(404))
    respx.get(PAGE).mock(return_value=httpx.Response(302, headers={"Location": PAGE}))
    assert await scraper.fetch(PAGE) is None


@pytest.mark.parametrize("url", ["javascript:alert(1)", "ftp://x.org/a", "", "sem-esquema"])
async def test_unsafe_urls_make_no_request(scraper: PoliteScraper, url: str) -> None:
    assert await scraper.fetch(url) is None
    assert scraper.requests_made == 0


@respx.mock
async def test_user_agent_identifies_the_project(scraper: PoliteScraper) -> None:
    robots = respx.get(ROBOTS).mock(return_value=httpx.Response(404))
    respx.get(PAGE).mock(return_value=httpx.Response(200, headers=HTML, text="x"))
    await scraper.fetch(PAGE)
    agent = robots.calls[0].request.headers["User-Agent"]
    assert agent == f"AcademicSearchHub/{__version__} (+contato: dev@exemplo.com)"
    assert "Mozilla" not in agent


@respx.mock
async def test_network_error_on_page_returns_none(scraper: PoliteScraper) -> None:
    respx.get(ROBOTS).mock(return_value=httpx.Response(404))
    respx.get(PAGE).mock(side_effect=httpx.ReadTimeout("lento"))
    assert await scraper.fetch(PAGE) is None


# ---------- motivos das recusas (achado na medição real de 15/10/2026) ----------


@respx.mock
async def test_each_refusal_records_its_reason_and_never_the_address(
    scraper: PoliteScraper,
) -> None:
    respx.get(ROBOTS).mock(
        return_value=httpx.Response(200, text="User-agent: *\nDisallow: /privado/\n")
    )
    respx.get("https://repo.exemplo.org/privado/1")
    respx.get(PAGE).mock(return_value=httpx.Response(404, headers=HTML, text="x"))
    respx.get("https://repo.exemplo.org/doc.pdf").mock(
        return_value=httpx.Response(
            200, headers={"Content-Type": "application/pdf"}, content=b"%PDF"
        )
    )
    respx.get("https://repo.exemplo.org/grande").mock(
        return_value=httpx.Response(200, headers=HTML, content=b"x" * (MAX_PAGE_BYTES + 1))
    )
    assert await scraper.fetch("https://repo.exemplo.org/privado/1") is None
    assert await scraper.fetch(PAGE) is None
    assert await scraper.fetch("https://repo.exemplo.org/doc.pdf") is None
    assert await scraper.fetch("https://repo.exemplo.org/grande") is None
    assert await scraper.fetch("ftp://repo.exemplo.org/x") is None
    assert dict(scraper.refusals) == {
        "robots_txt": 1,
        "http_404": 1,
        "nao_html": 1,
        "pagina_grande": 1,
        "endereco_invalido": 1,
    }
    assert not any("repo.exemplo.org" in reason for reason in scraper.refusals)  # só o motivo


@respx.mock
async def test_network_error_and_robots_unavailable_have_their_own_reasons(
    scraper: PoliteScraper,
) -> None:
    respx.get(ROBOTS).mock(return_value=httpx.Response(200, text=""))
    respx.get(PAGE).mock(side_effect=httpx.ConnectError("sem rede"))
    assert await scraper.fetch(PAGE) is None
    assert scraper.refusals["erro_de_rede"] == 1
    respx.get("https://fora.exemplo.org/robots.txt").mock(return_value=httpx.Response(503))
    assert await scraper.fetch("https://fora.exemplo.org/a") is None
    assert scraper.refusals["robots_txt"] == 1  # robots.txt com erro 5xx: por prudência, não raspa


@respx.mock
async def test_successful_fetch_records_no_refusal(scraper: PoliteScraper) -> None:
    respx.get(ROBOTS).mock(return_value=httpx.Response(200, text=""))
    respx.get(PAGE).mock(return_value=httpx.Response(200, headers=HTML, text="<p>ok</p>"))
    assert await scraper.fetch(PAGE) == "<p>ok</p>"
    assert not scraper.refusals
