import pytest
from playwright.sync_api import Page, expect

from tests.e2e.test_search_page import Api, record, response_body, search

pytestmark = pytest.mark.e2e


@pytest.fixture
def api(page: Page) -> Api:
    instance = Api(page)
    instance.handler = lambda p: (200, response_body([record(1), record(2)]))
    return instance


def open_panel(page: Page) -> None:
    page.get_by_role("button", name="Filtros").click()
    expect(page.locator("#painel-filtros")).to_be_visible()


def test_panel_toggles_with_aria_expanded(page: Page, api: Api) -> None:
    page.goto("/")
    button = page.locator("#botao-filtros")
    expect(button).to_have_attribute("aria-expanded", "false")
    expect(page.locator("#painel-filtros")).to_be_hidden()
    button.click()
    expect(button).to_have_attribute("aria-expanded", "true")
    expect(page.locator("#painel-filtros")).to_be_visible()
    button.click()
    expect(page.locator("#painel-filtros")).to_be_hidden()


def test_apply_filters_goes_to_url_request_and_active_tags(page: Page, api: Api) -> None:
    page.goto("/")
    page.get_by_label("Buscar trabalhos").fill("letramento")
    open_panel(page)
    page.get_by_label("De", exact=True).fill("2018")
    page.get_by_label("Até", exact=True).fill("2022")
    page.get_by_role("checkbox", name="Tese ou dissertação").check()
    page.get_by_role("checkbox", name="Artigo", exact=True).check()
    page.get_by_role("radio", name="Mais recentes").check()
    page.get_by_role("button", name="Aplicar").click()

    expect(page.locator(".result")).to_have_count(2)
    params = api.searches[-1]
    assert params["q"] == "letramento" and params["page"] == "1"
    assert (params["year_from"], params["year_to"]) == ("2018", "2022")
    assert set(params["type"].split(",")) == {"article", "thesis"}
    assert params["sort"] == "year_desc"
    for fragment in ("year_from=2018", "year_to=2022", "sort=year_desc", "q=letramento"):
        assert fragment in page.url
    tags = page.locator("#filtros-ativos")
    expect(tags).to_contain_text("Ano: 2018–2022")
    expect(tags).to_contain_text("Tipo:")
    expect(tags).to_contain_text("Ordem: Mais recentes")
    expect(page.locator("#botao-filtros")).to_have_text("Filtros (3)")
    expect(page.locator("#painel-filtros")).to_be_hidden()  # fecha ao aplicar
    assert page.evaluate("document.activeElement.id") == "titulo-resultados"


def test_applying_goes_back_to_page_one(page: Page, api: Api) -> None:
    api.handler = lambda p: (
        200,
        response_body([record(1)], page=int(p.get("page", "1")), total=100),
    )
    page.goto("/?q=letramento&page=3")
    expect(page.locator(".result")).to_have_count(1)
    open_panel(page)
    page.get_by_role("checkbox", name="Livro").check()
    page.get_by_role("button", name="Aplicar").click()
    expect(page.locator(".result")).to_have_count(1)
    assert api.searches[-1]["page"] == "1" and "page=" not in page.url


def test_invalid_year_range_blocks_submission_with_accessible_message(page: Page, api: Api) -> None:
    page.goto("/")
    page.get_by_label("Buscar trabalhos").fill("letramento")
    open_panel(page)
    page.get_by_label("De", exact=True).fill("2022")
    page.get_by_label("Até", exact=True).fill("2018")
    page.get_by_role("button", name="Aplicar").click()
    error = page.locator("#erro-anos")
    expect(error).to_have_text("O ano inicial não pode ser maior que o ano final.")
    for label in ("De", "Até"):
        field = page.get_by_label(label, exact=True)
        expect(field).to_have_attribute("aria-invalid", "true")
        assert "erro-anos" in (field.get_attribute("aria-describedby") or "")
    assert api.searches == []
    assert page.evaluate("document.activeElement.id") == "ano-de"
    page.get_by_label("De", exact=True).fill("2010")
    page.get_by_role("button", name="Aplicar").click()
    expect(page.locator("#erro-anos")).to_be_hidden()
    expect(page.locator(".result")).to_have_count(2)


@pytest.mark.parametrize("year", ["1800", "9999"])
def test_year_out_of_bounds_is_rejected(page: Page, api: Api, year: str) -> None:
    page.goto("/")
    page.get_by_label("Buscar trabalhos").fill("letramento")
    open_panel(page)
    page.get_by_label("De", exact=True).fill(year)
    page.get_by_role("button", name="Aplicar").click()
    expect(page.locator("#erro-anos")).to_contain_text("Informe anos entre 1900 e")
    assert api.searches == []


def test_clear_removes_everything_and_repeats_the_search(page: Page, api: Api) -> None:
    page.goto("/?q=letramento&year_from=2018&type=thesis&sort=year_desc")
    expect(page.locator(".result")).to_have_count(2)
    expect(page.locator("#botao-filtros")).to_have_text("Filtros (3)")
    open_panel(page)
    page.get_by_role("button", name="Limpar").click()
    expect(page.locator("#filtros-ativos")).to_be_hidden()
    assert set(api.searches[-1]) == {"q", "page"}
    assert page.url.endswith("?q=letramento")
    expect(page.get_by_label("De", exact=True)).to_have_value("")
    expect(page.get_by_role("checkbox", name="Tese ou dissertação")).not_to_be_checked()
    expect(page.get_by_role("radio", name="Relevância")).to_be_checked()


def test_removing_one_active_filter_keeps_the_others(page: Page, api: Api) -> None:
    page.goto("/?q=letramento&year_from=2018&year_to=2020&type=thesis")
    expect(page.locator(".result")).to_have_count(2)
    page.get_by_role("button", name="Remover filtro Ano: 2018–2020").click()
    expect(page.locator("#filtros-ativos")).not_to_contain_text("Ano:")
    expect(page.locator("#filtros-ativos")).to_contain_text("Tipo: Tese ou dissertação")
    last = api.searches[-1]
    assert "year_from" not in last and last["type"] == "thesis"


def test_shared_link_fills_the_panel(page: Page, api: Api) -> None:
    page.goto("/?q=robotica&year_from=2015&type=article,book&sources=core&sort=year_desc")
    expect(page.locator(".result")).to_have_count(2)
    open_panel(page)
    expect(page.get_by_label("De", exact=True)).to_have_value("2015")
    expect(page.get_by_role("checkbox", name="Artigo", exact=True)).to_be_checked()
    expect(page.get_by_role("checkbox", name="Livro")).to_be_checked()
    expect(page.get_by_role("checkbox", name="Tese ou dissertação")).not_to_be_checked()
    expect(page.get_by_role("checkbox", name="CORE")).to_be_checked()
    expect(page.get_by_role("radio", name="Mais recentes")).to_be_checked()
    last = api.searches[0]
    assert (
        last["sources"] == "core" and last["type"] == "article,book" and last["sort"] == "year_desc"
    )


def test_sources_are_dynamic_and_unavailable_ones_are_disabled_with_reason(
    page: Page, api: Api
) -> None:
    page.goto("/")
    open_panel(page)
    boxes = page.locator("#filtro-fontes input[type=checkbox]")
    assert boxes.count() == 3
    expect(page.get_by_role("checkbox", name="OpenAlex")).to_be_enabled()
    bdtd = page.get_by_role("checkbox", name="BDTD (IBICT)")
    expect(bdtd).to_be_disabled()
    reason_id = bdtd.get_attribute("aria-describedby")
    assert reason_id and "Fonte ainda não colhida" in page.locator(f"#{reason_id}").inner_text()


def test_choosing_sources_sends_them(page: Page, api: Api) -> None:
    page.goto("/")
    page.get_by_label("Buscar trabalhos").fill("letramento")
    open_panel(page)
    page.get_by_role("checkbox", name="OpenAlex").check()
    page.get_by_role("checkbox", name="CORE").check()
    page.get_by_role("button", name="Aplicar").click()
    expect(page.locator(".result")).to_have_count(2)
    assert api.searches[-1]["sources"] == "openalex,core"
    expect(page.locator("#filtros-ativos")).to_contain_text("Fontes: OpenAlex, CORE")


def test_notice_about_records_without_year_is_visible(page: Page, api: Api) -> None:
    page.goto("/")
    open_panel(page)
    expect(page.locator("#painel-filtros")).to_contain_text(
        "Registros sem ano são ocultados quando há filtro de ano"
    )


def test_enter_in_year_field_submits_with_the_filters(page: Page, api: Api) -> None:
    page.goto("/")
    page.get_by_label("Buscar trabalhos").fill("letramento")
    open_panel(page)
    page.get_by_label("De", exact=True).fill("2019")
    page.keyboard.press("Enter")
    expect(page.locator(".result")).to_have_count(2)
    assert api.searches[-1]["year_from"] == "2019"


def test_keyboard_only_flow(page: Page, api: Api) -> None:
    page.goto("/")
    page.get_by_label("Buscar trabalhos").fill("letramento")
    page.get_by_role("button", name="Filtros").focus()
    page.keyboard.press("Space")
    expect(page.locator("#painel-filtros")).to_be_visible()
    page.get_by_role("checkbox", name="Preprint").focus()
    page.keyboard.press("Space")
    expect(page.get_by_role("checkbox", name="Preprint")).to_be_checked()
    page.get_by_role("button", name="Aplicar").focus()
    page.keyboard.press("Enter")
    expect(page.locator(".result")).to_have_count(2)
    assert api.searches[-1]["type"] == "preprint"


def test_legends_and_labels_exist_for_all_controls(page: Page, api: Api) -> None:
    page.goto("/")
    open_panel(page)
    legends = [t.strip() for t in page.locator("#painel-filtros legend").all_inner_texts()]
    assert legends == ["Ano de publicação", "Tipo de publicação", "Fontes", "Ordenação"]
    unlabeled = page.evaluate(
        """() => [...document.querySelectorAll('#painel-filtros input')]
            .filter(i => !i.labels || i.labels.length === 0).map(i => i.id)"""
    )
    assert unlabeled == []


@pytest.mark.parametrize("width", [320, 768, 1280])
def test_open_panel_has_no_horizontal_scroll(page: Page, api: Api, width: int) -> None:
    page.set_viewport_size({"width": width, "height": 900})
    page.goto("/")
    open_panel(page)
    assert page.evaluate("document.documentElement.scrollWidth") <= width


def test_touch_targets_in_the_panel(page: Page, api: Api) -> None:
    page.set_viewport_size({"width": 375, "height": 800})
    page.goto("/")
    open_panel(page)
    for selector in (
        "#botao-filtros",
        "#aplicar-filtros",
        "#limpar-filtros",
        "#ano-de",
        "#tipo-article + label",
    ):
        box = page.locator(selector).first.bounding_box()
        assert box is not None and box["height"] >= 24, (selector, box)
    check = page.locator("#painel-filtros .check").first.bounding_box()
    assert check is not None and check["height"] >= 43.5


def test_back_button_restores_filters_in_panel_and_tags(page: Page, api: Api) -> None:
    page.goto("/")
    search(page, "letramento")
    expect(page.locator(".result")).to_have_count(2)
    open_panel(page)
    page.get_by_role("checkbox", name="Livro").check()
    page.get_by_role("button", name="Aplicar").click()
    expect(page.locator("#filtros-ativos")).to_contain_text("Tipo: Livro")
    page.go_back()
    expect(page.locator("#filtros-ativos")).to_be_hidden()
    open_panel(page)
    expect(page.get_by_role("checkbox", name="Livro")).not_to_be_checked()
