import json
from typing import Any

import pytest
from playwright.sync_api import Page, Route, expect

pytestmark = pytest.mark.e2e

SOURCES = [
    {
        "slug": "openalex",
        "name": "OpenAlex",
        "kind": "api",
        "enabled": True,
        "status": "ok",
        "message": None,
    },
    {
        "slug": "core",
        "name": "CORE",
        "kind": "api",
        "enabled": True,
        "status": "ok",
        "message": None,
    },
    {
        "slug": "bdtd",
        "name": "BDTD (IBICT)",
        "kind": "oai",
        "enabled": False,
        "status": "disabled",
        "message": "Fonte ainda não colhida",
    },
]


def record(n: int, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": f"doi:10.1234/r{n}",
        "title": f"Letramento digital na escola número {n}",
        "authors": [{"name": f"Autor {n}", "orcid": None}, {"name": "Maria Souza", "orcid": None}],
        "abstract": "Resumo curto do trabalho.",
        "year": 2020 + n,
        "doi": f"10.1234/r{n}",
        "url": f"https://exemplo.org/trabalho/{n}",
        "pdf_url": f"https://exemplo.org/trabalho/{n}.pdf" if n == 1 else None,
        "type": "article" if n % 2 else "thesis",
        "language": "pt",
        "keywords": [],
        "sources": [{"source": "openalex", "source_id": f"W{n}", "url": None}],
        "is_favorite": False,
    }
    return {**data, **overrides}


def status(**overrides: Any) -> dict[str, Any]:
    data = {
        "openalex": {"status": "ok", "count": 2, "total": 1200, "message": None},
        "core": {"status": "ok", "count": 2, "total": 300, "message": None},
        "bdtd": {
            "status": "disabled",
            "count": 0,
            "total": 0,
            "message": "Fonte ainda não colhida",
        },
    }
    return {**data, **overrides}


def response_body(
    results: list[dict[str, Any]], page: int = 1, total: int = 1500, **kw: Any
) -> dict[str, Any]:
    return {
        "query": "letramento",
        "page": page,
        "page_size": 20,
        "total_estimated": total,
        "total_is_estimate": True,
        "results": results,
        "sources_status": status(**kw),
    }


class Api:
    """Intercepta /api/v1 no navegador e guarda as consultas feitas."""

    def __init__(self, page: Page) -> None:
        self.searches: list[dict[str, str]] = []
        self.handler = lambda params: (200, response_body([record(1), record(2)]))
        page.route("**/api/v1/sources", lambda r: r.fulfill(status=200, json=SOURCES))
        page.route("**/api/v1/search?*", self._search)

    def _search(self, route: Route) -> None:
        from urllib.parse import parse_qsl, urlsplit

        params = dict(parse_qsl(urlsplit(route.request.url).query))
        self.searches.append(params)
        status_code, body = self.handler(params)
        route.fulfill(status=status_code, content_type="application/json", body=json.dumps(body))


@pytest.fixture
def api(page: Page) -> Api:
    return Api(page)


def search(page: Page, text: str = "letramento") -> None:
    page.get_by_label("Buscar trabalhos").fill(text)
    page.get_by_role("button", name="Buscar").click()


def test_empty_search_page(page: Page, api: Api) -> None:
    page.goto("/")
    expect(page.get_by_role("search")).to_be_visible()
    expect(page.get_by_label("Buscar trabalhos")).to_be_visible()
    expect(page.locator("#area-resultados")).to_be_hidden()
    assert api.searches == []
    assert "aspas" in page.locator("#ajuda-busca").inner_text()


def test_results_are_rendered_as_cards(page: Page, api: Api) -> None:
    page.goto("/")
    search(page)
    expect(page.locator(".result")).to_have_count(2)
    first = page.locator(".result").first
    link = first.get_by_role("link", name="Letramento digital na escola número 1")
    expect(link).to_have_attribute("href", "https://exemplo.org/trabalho/1")
    expect(link).to_have_attribute("target", "_blank")
    expect(link).to_have_attribute("rel", "noopener noreferrer")
    expect(first).to_contain_text("Autor 1, Maria Souza")
    expect(first).to_contain_text("2021")
    expect(first).to_contain_text("Artigo")
    expect(first).to_contain_text("Português")
    expect(first.locator(".badge")).to_have_text("OpenAlex")
    expect(first.get_by_role("link", name="Texto completo (PDF)")).to_have_attribute(
        "href", "https://exemplo.org/trabalho/1.pdf"
    )
    expect(page.locator("#resumo-busca")).to_contain_text("Cerca de 1.500 resultados (estimativa)")
    expect(page.locator("#resumo-busca")).to_contain_text("2 de 2 fontes responderam")
    assert api.searches[0]["q"] == "letramento"
    assert page.url.endswith("?q=letramento")
    assert page.probe.errors == []  # type: ignore[attr-defined]


def test_favorite_control_for_visitors_leads_to_login_keeping_the_search(
    page: Page, api: Api
) -> None:
    page.goto("/")
    search(page)
    control = page.locator(".favorite-button").first
    expect(control).to_have_text("Entre para salvar")
    expect(control).to_have_attribute("href", "conta.html?voltar=%2F%3Fq%3Dletramento")


def test_authors_are_limited_to_five_with_remaining_count(page: Page, api: Api) -> None:
    authors = [{"name": f"Pessoa {i}", "orcid": None} for i in range(1, 9)]
    api.handler = lambda p: (200, response_body([record(1, authors=authors)]))
    page.goto("/")
    search(page)
    text = page.locator(".result-authors").inner_text()
    assert text == "Pessoa 1, Pessoa 2, Pessoa 3, Pessoa 4, Pessoa 5 e mais 3"


def test_long_abstract_expands_and_collapses(page: Page, api: Api) -> None:
    long_text = ("palavra " * 80).strip()
    api.handler = lambda p: (200, response_body([record(1, abstract=long_text)]))
    page.goto("/")
    search(page)
    toggle = page.get_by_role("button", name="Ler mais")
    expect(toggle).to_have_attribute("aria-expanded", "false")
    short = page.locator(".result-abstract").inner_text()
    assert short.endswith("…") and len(short) < len(long_text)
    toggle.click()
    expect(page.get_by_role("button", name="Ler menos")).to_have_attribute("aria-expanded", "true")
    assert page.locator(".result-abstract").inner_text() == long_text
    page.get_by_role("button", name="Ler menos").click()
    assert page.locator(".result-abstract").inner_text() == short


def test_malicious_title_is_shown_as_text_and_never_executed(page: Page, api: Api) -> None:
    payload = '<img src=x onerror="window.__xss=1"><script>window.__xss=2</script>'
    api.handler = lambda p: (
        200,
        response_body(
            [record(1, title=payload, abstract=payload, authors=[{"name": payload, "orcid": None}])]
        ),
    )
    page.goto("/")
    search(page)
    expect(page.locator(".result")).to_have_count(1)
    page.wait_for_timeout(300)
    assert page.evaluate("window.__xss") is None
    assert page.locator(".result img").count() == 0 and page.locator(".result script").count() == 0
    assert "<img src=x" in page.locator(".result-title").inner_text()


def test_unsafe_urls_do_not_become_links(page: Page, api: Api) -> None:
    api.handler = lambda p: (
        200,
        response_body([record(1, url="javascript:alert(1)", pdf_url="data:text/html,x")]),
    )
    page.goto("/")
    search(page)
    expect(page.locator(".result")).to_have_count(1)
    assert page.locator(".result a:not(.favorite-button)").count() == 0  # só sobra o link de login


def test_partial_failure_shows_warning_listing_failed_sources(page: Page, api: Api) -> None:
    api.handler = lambda p: (
        200,
        response_body(
            [record(1)],
            core={
                "status": "timeout",
                "count": 0,
                "total": 0,
                "message": "A fonte demorou para responder.",
            },
        ),
    )
    page.goto("/")
    search(page)
    alert = page.locator("#avisos-busca .alert-warning")
    expect(alert).to_contain_text("Aviso:")
    expect(alert).to_contain_text("CORE: demorou demais para responder")
    expect(page.locator("#resumo-busca")).to_contain_text("1 de 2 fontes responderam")


def test_disabled_sources_appear_as_discreet_note(page: Page, api: Api) -> None:
    page.goto("/")
    search(page)
    note = page.locator("#fontes-busca")
    expect(note).to_contain_text("BDTD (IBICT): Fonte ainda não colhida")
    expect(page.locator(".alert-error")).to_have_count(0)


def test_no_results_message(page: Page, api: Api) -> None:
    api.handler = lambda p: (200, response_body([], total=0))
    page.goto("/")
    search(page, "asdfgh")
    expect(page.locator("#lista-resultados")).to_contain_text(
        "Nenhum resultado. Tente outros termos ou remova filtros."
    )
    expect(page.locator("#paginacao")).to_be_hidden()


def test_all_sources_failed_shows_error_with_state_per_source(page: Page, api: Api) -> None:
    body = {
        "error": {
            "code": "upstream_error",
            "message": "Todas as fontes falharam ou estão indisponíveis.",
            "details": [],
        },
        "sources_status": {
            "openalex": {"status": "timeout", "count": 0, "total": 0, "message": "x"},
            "core": {"status": "error", "count": 0, "total": 0, "message": "y"},
        },
    }
    api.handler = lambda p: (502, body)
    page.goto("/")
    search(page)
    alert = page.locator("#lista-resultados .alert-error")
    expect(alert).to_have_attribute("role", "alert")
    expect(alert).to_contain_text("Erro: Todas as fontes falharam")
    expect(alert).to_contain_text("OpenAlex: demorou demais para responder")
    expect(alert).to_contain_text("CORE: falhou")


@pytest.mark.parametrize(
    ("code", "status_code", "fragment"),
    [
        ("rate_limited", 429, "Muitas buscas em pouco tempo"),
        ("validation_error", 422, "Consulta inválida"),
        ("internal_error", 500, "Erro interno"),
    ],
)
def test_error_responses_have_friendly_messages(
    page: Page, api: Api, code: str, status_code: int, fragment: str
) -> None:
    detail = (
        [{"field": "q", "issue": "a consulta deve ter de 2 a 200 caracteres"}]
        if status_code == 422
        else []
    )
    body = {
        "error": {"code": code, "message": "Erro interno. Tente mais tarde.", "details": detail}
    }
    api.handler = lambda p: (status_code, body)
    page.goto("/")
    search(page)
    expect(page.locator("#lista-resultados .alert-error")).to_contain_text(fragment)


def test_short_query_is_blocked_with_accessible_message_and_no_request(
    page: Page, api: Api
) -> None:
    page.goto("/")
    search(page, "a")
    field = page.get_by_label("Buscar trabalhos")
    expect(field).to_have_attribute("aria-invalid", "true")
    expect(page.locator("#erro-busca")).to_have_text("Digite ao menos 2 caracteres para buscar.")
    assert "erro-busca" in (field.get_attribute("aria-describedby") or "")
    assert api.searches == []
    assert page.evaluate("document.activeElement.id") == "campo-busca"


def test_loading_state_shows_skeleton_and_announces(page: Page, api: Api) -> None:
    def slow(route: Route) -> None:
        page.wait_for_timeout(600)
        route.fulfill(status=200, json=response_body([record(1)]))

    page.unroute("**/api/v1/search?*")
    page.route("**/api/v1/search?*", slow)
    page.goto("/")
    search(page)
    expect(page.locator("#resumo-busca")).to_have_text("Buscando…")
    expect(page.locator("#lista-resultados")).to_have_attribute("aria-busy", "true")
    assert page.locator(".skeleton").count() >= 3
    expect(page.locator("#announcer")).to_have_text("Buscando…")
    expect(page.locator(".result")).to_have_count(1)
    expect(page.locator("#lista-resultados")).to_have_attribute("aria-busy", "false")


def test_pagination_updates_request_url_and_focus(page: Page, api: Api) -> None:
    api.handler = lambda p: (
        200,
        response_body([record(1), record(2)], page=int(p.get("page", "1")), total=100),
    )
    page.goto("/")
    search(page)
    expect(page.get_by_role("button", name="Anterior")).to_be_disabled()
    page.get_by_role("button", name="Próxima").click()
    expect(page.locator(".pagination-page")).to_have_text("Página 2")
    assert api.searches[-1]["page"] == "2"
    assert page.url.endswith("?q=letramento&page=2")
    assert page.evaluate("document.activeElement.id") == "titulo-resultados"
    expect(page.get_by_role("button", name="Anterior")).to_be_enabled()


def test_browser_back_restores_previous_search(page: Page, api: Api) -> None:
    api.handler = lambda p: (
        200,
        response_body([record(1)], total=100 if p["q"] == "letramento" else 5),
    )
    page.goto("/")
    search(page, "letramento")
    expect(page.locator("#resumo-busca")).to_contain_text("Cerca de 100")
    search(page, "robótica")
    expect(page.locator("#resumo-busca")).to_contain_text("Cerca de 5 ")
    page.go_back()
    expect(page.get_by_label("Buscar trabalhos")).to_have_value("letramento")
    expect(page.locator("#resumo-busca")).to_contain_text("Cerca de 100")
    assert page.url.endswith("?q=letramento")
    page.go_back()
    expect(page.locator("#area-resultados")).to_be_hidden()


def test_opening_a_shared_link_runs_the_search(page: Page, api: Api) -> None:
    page.goto("/?q=educa%C3%A7%C3%A3o+inclusiva&page=3")
    expect(page.locator(".result")).to_have_count(2)
    assert api.searches[0]["q"] == "educação inclusiva" and api.searches[0]["page"] == "3"
    expect(page.get_by_label("Buscar trabalhos")).to_have_value("educação inclusiva")


def test_enter_key_submits_and_keyboard_reaches_results(page: Page, api: Api) -> None:
    page.goto("/")
    page.get_by_label("Buscar trabalhos").fill("letramento")
    page.keyboard.press("Enter")
    expect(page.locator(".result")).to_have_count(2)
    page.get_by_label("Buscar trabalhos").focus()
    visited = []
    for _ in range(6):
        page.keyboard.press("Tab")
        visited.append(page.evaluate("document.activeElement.textContent.trim().slice(0, 25)"))
    assert visited[0] == "Buscar"
    assert visited[1] == "Filtros"
    assert any(
        text.startswith("Letramento digital") for text in visited[2:]
    )  # chega ao primeiro resultado


def test_new_search_cancels_the_previous_one(page: Page, api: Api) -> None:
    calls: list[str] = []

    def handler(route: Route) -> None:
        from urllib.parse import parse_qsl, urlsplit

        q = dict(parse_qsl(urlsplit(route.request.url).query))["q"]
        calls.append(q)
        if q == "lenta":
            page.wait_for_timeout(800)
        route.fulfill(status=200, json=response_body([record(1, title=f"Resultado de {q}")]))

    page.unroute("**/api/v1/search?*")
    page.route("**/api/v1/search?*", handler)
    page.goto("/")
    search(page, "lenta")
    search(page, "rapida")
    expect(page.locator(".result-title")).to_have_text("Resultado de rapida")
    page.wait_for_timeout(1000)
    expect(page.locator(".result-title")).to_have_text(
        "Resultado de rapida"
    )  # a antiga não sobrescreve


def test_text_typed_while_sources_load_is_not_erased(page: Page, api: Api) -> None:
    """Regressão (OS-032): ao terminar de carregar as fontes, a página apagava o que já fora digitado."""
    held: list[Route] = []
    page.route("**/api/v1/sources", lambda route: held.append(route))  # segura a resposta
    page.goto("/")
    page.get_by_label("Buscar trabalhos").fill("letramento")
    page.wait_for_timeout(200)
    assert held, "a página deveria ter pedido as fontes"
    held[0].fulfill(status=200, json=SOURCES)
    page.wait_for_timeout(300)
    expect(page.get_by_label("Buscar trabalhos")).to_have_value("letramento")


# ---------- busca por tema ou por autor ----------


def choose_author(page: Page) -> None:
    page.get_by_label("Buscar por").select_option("author")


def test_theme_is_the_default_and_sends_no_field(page: Page, api: Api) -> None:
    page.goto("/")
    select = page.get_by_label("Buscar por")
    expect(select).to_have_value("all")
    expect(page.get_by_label("Buscar trabalhos")).to_have_attribute(
        "placeholder", "Ex.: letramento digital"
    )
    search(page)
    expect(page.locator(".result")).to_have_count(2)
    assert "field" not in api.searches[-1] and "field=" not in page.url


def test_choosing_author_changes_the_label_and_sends_field_author(page: Page, api: Api) -> None:
    page.goto("/")
    choose_author(page)
    field = page.get_by_label("Nome do autor")
    expect(field).to_have_attribute("placeholder", "Ex.: Paulo Freire")
    expect(page.get_by_label("Buscar trabalhos")).to_have_count(0)  # o rótulo trocou
    field.fill("Paulo Freire")
    page.get_by_role("button", name="Buscar", exact=True).click()
    expect(page.locator(".result")).to_have_count(2)
    assert api.searches[-1]["q"] == "Paulo Freire" and api.searches[-1]["field"] == "author"
    assert "field=author" in page.url


def test_url_with_field_author_restores_the_selector_and_searches_by_author(
    page: Page, api: Api
) -> None:
    page.goto("/?q=Freire&field=author")
    expect(page.locator(".result")).to_have_count(2)
    expect(page.get_by_label("Buscar por")).to_have_value("author")
    expect(page.get_by_label("Nome do autor")).to_have_value("Freire")
    assert api.searches[-1]["field"] == "author"


def test_field_survives_pagination_filters_and_the_back_button(page: Page, api: Api) -> None:
    api.handler = lambda p: (
        200,
        response_body([record(1), record(2)], page=int(p.get("page", "1")), total=100),
    )
    page.goto("/")
    choose_author(page)
    page.get_by_label("Nome do autor").fill("Freire")
    page.get_by_role("button", name="Buscar", exact=True).click()
    expect(page.locator(".result")).to_have_count(2)
    page.get_by_role("button", name="Próxima").click()
    expect(page.locator(".pagination-page")).to_have_text("Página 2")
    assert api.searches[-1]["page"] == "2" and api.searches[-1]["field"] == "author"
    page.get_by_role("button", name="Filtros").click()
    page.get_by_label("De", exact=True).fill("2018")
    page.get_by_role("button", name="Aplicar").click()
    expect(page.locator(".pagination-page")).to_have_text("Página 1")
    assert api.searches[-1]["field"] == "author" and api.searches[-1]["year_from"] == "2018"
    page.go_back()
    expect(page.get_by_label("Buscar por")).to_have_value(
        "author"
    )  # a busca anterior era por autor


def test_going_back_to_theme_stops_sending_the_field(page: Page, api: Api) -> None:
    page.goto("/")
    choose_author(page)
    page.get_by_label("Nome do autor").fill("Freire")
    page.get_by_role("button", name="Buscar", exact=True).click()
    expect(page.locator(".result")).to_have_count(2)
    page.get_by_label("Buscar por").select_option("all")
    expect(page.get_by_label("Buscar trabalhos")).to_have_value("Freire")  # o texto fica
    page.get_by_role("button", name="Buscar", exact=True).click()
    expect(page.get_by_label("Buscar por")).to_have_value("all")
    page.wait_for_function("!location.search.includes('field=')")
    assert "field" not in api.searches[-1]


def test_field_chosen_while_sources_load_is_not_reset(page: Page, api: Api) -> None:
    """Mesma classe do defeito da OS-032: terminar de carregar as fontes não desfaz a escolha."""
    held: list[Route] = []
    page.route("**/api/v1/sources", lambda route: held.append(route))
    page.goto("/")
    choose_author(page)
    page.get_by_label("Nome do autor").fill("Freire")
    page.wait_for_timeout(200)
    assert held, "a página deveria ter pedido as fontes"
    held[0].fulfill(status=200, json=SOURCES)
    page.wait_for_timeout(300)
    expect(page.get_by_label("Buscar por")).to_have_value("author")
    expect(page.get_by_label("Nome do autor")).to_have_value("Freire")


def test_author_search_error_for_a_one_character_name_is_the_same_message(
    page: Page, api: Api
) -> None:
    page.goto("/")
    choose_author(page)
    page.get_by_label("Nome do autor").fill("a")
    page.get_by_role("button", name="Buscar", exact=True).click()
    expect(page.locator("#erro-busca")).to_have_text("Digite ao menos 2 caracteres para buscar.")
    assert api.searches == []


def test_merged_record_from_the_same_source_shows_one_badge(page: Page, api: Api) -> None:
    sources = [
        {"source": "core", "source_id": "1", "url": None},
        {"source": "core", "source_id": "2", "url": None},
        {"source": "openalex", "source_id": "W1", "url": None},
    ]
    api.handler = lambda params: (200, response_body([record(1, sources=sources)]))
    page.goto("/")
    search(page)
    expect(page.locator(".result").first.locator(".badge")).to_have_text(["CORE", "OpenAlex"])
