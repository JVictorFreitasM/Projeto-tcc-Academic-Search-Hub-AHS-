import pytest
from playwright.sync_api import Page, expect

from tests.e2e.fake_api import TOKEN, FakeApi, record

pytestmark = pytest.mark.e2e


@pytest.fixture
def api(page: Page) -> FakeApi:
    return FakeApi(page, logged_in=True)


def run_search(page: Page, text: str = "letramento") -> None:
    page.get_by_label("Buscar trabalhos").fill(text)
    page.get_by_role("button", name="Buscar", exact=True).click()
    expect(page.locator(".result")).to_have_count(3)


# ---------- botão de favorito na busca ----------


def test_toggle_favorite_from_the_results(page: Page, api: FakeApi) -> None:
    page.goto("/")
    run_search(page)
    button = page.locator(".favorite-button").first
    expect(button).to_have_text("Salvar nos favoritos")
    expect(button).to_have_attribute("aria-pressed", "false")
    button.click()
    expect(button).to_have_text("Remover dos favoritos")
    expect(button).to_have_attribute("aria-pressed", "true")
    expect(page.locator("#announcer")).to_have_text("Salvo nos favoritos.")
    saved = api.calls_to("POST", "/favorites")[0]
    assert saved["body"]["record"]["id"] == "doi:10.1234/r1" and saved["auth"] == f"Bearer {TOKEN}"
    assert len(api.favorites) == 1
    button.click()
    expect(button).to_have_text("Salvar nos favoritos")
    expect(page.locator("#announcer")).to_have_text("Removido dos favoritos.")
    assert api.favorites == []
    assert page.evaluate("document.activeElement.className").startswith("btn favorite-button")


def test_already_favorite_item_can_be_removed_without_known_id(page: Page, api: FakeApi) -> None:
    api.add_favorite(record(2))
    page.goto("/")
    run_search(page)
    button = page.locator(".favorite-button").nth(1)
    expect(button).to_have_text("Remover dos favoritos")
    expect(button).to_have_attribute("aria-pressed", "true")
    button.click()
    expect(button).to_have_text("Salvar nos favoritos")
    assert api.favorites == []


def test_favorite_error_is_announced(page: Page, api: FakeApi) -> None:
    api.fail["POST /favorites"] = (
        409,
        {
            "error": {
                "code": "favorites_limit_reached",
                "message": "Limite de 2000 favoritos atingido.",
            }
        },
    )
    page.goto("/")
    run_search(page)
    page.locator(".favorite-button").first.click()
    expect(page.locator("#announcer")).to_contain_text("Limite de 2000 favoritos atingido.")
    expect(page.locator(".favorite-button").first).to_have_attribute("aria-pressed", "false")


# ---------- seleção e exportação ----------


def test_select_results_and_export_selected(page: Page, api: FakeApi) -> None:
    page.goto("/")
    run_search(page)
    expect(page.locator("#contagem-selecao")).to_have_text("Nenhum trabalho selecionado.")
    expect(page.get_by_role("button", name="Exportar selecionados")).to_be_disabled()
    page.get_by_label("Selecionar para exportar").nth(0).check()
    page.get_by_label("Selecionar para exportar").nth(2).check()
    expect(page.locator("#contagem-selecao")).to_have_text("2 trabalhos selecionados.")
    page.locator("#formato-exportar").select_option("ris")
    with page.expect_download() as info:
        page.get_by_role("button", name="Exportar selecionados").click()
    download = info.value
    assert download.suggested_filename == "exportacao-20261009.ris"
    call = api.calls_to("POST", "/export")[0]
    assert call["body"]["format"] == "ris"
    assert [r["id"] for r in call["body"]["records"]] == ["doi:10.1234/r1", "doi:10.1234/r3"]
    assert call["auth"] is None  # exportar resultados não exige login
    with open(download.path(), encoding="utf-8") as handle:
        assert handle.read() == "EXPORT-ris-2\n"


@pytest.mark.parametrize("fmt", ["bibtex", "ris", "json", "csv"])
def test_all_four_formats_download_with_the_right_extension(
    page: Page, api: FakeApi, fmt: str
) -> None:
    page.goto("/")
    run_search(page)
    page.get_by_label("Selecionar para exportar").first.check()
    page.locator("#formato-exportar").select_option(fmt)
    with page.expect_download() as info:
        page.get_by_role("button", name="Exportar selecionados").click()
    assert info.value.suggested_filename.endswith(f".{fmt}")


def test_selection_survives_page_change_and_can_be_cleared(page: Page, api: FakeApi) -> None:
    api.search_total = 100
    page.goto("/")
    run_search(page)
    page.get_by_label("Selecionar para exportar").first.check()
    page.get_by_role("button", name="Próxima").click()
    expect(page.locator(".pagination-page")).to_have_text("Página 2")
    expect(page.locator("#contagem-selecao")).to_have_text("1 trabalho selecionado.")
    page.get_by_role("button", name="Limpar seleção").click()
    expect(page.locator("#contagem-selecao")).to_have_text("Nenhum trabalho selecionado.")
    expect(page.get_by_label("Selecionar para exportar").first).not_to_be_checked()


def test_export_bar_is_hidden_without_results(page: Page, api: FakeApi) -> None:
    api.search_results = []
    api.search_total = 0
    page.goto("/")
    page.get_by_label("Buscar trabalhos").fill("nada")
    page.get_by_role("button", name="Buscar", exact=True).click()
    expect(page.locator("#lista-resultados")).to_contain_text("Nenhum resultado")
    expect(page.locator("#barra-exportar")).to_be_hidden()


# ---------- página de favoritos ----------


def test_visitor_sees_login_notice_instead_of_favorites(page: Page) -> None:
    FakeApi(page, logged_in=False)
    page.goto("/favoritos.html")
    expect(page.locator("#aviso-login")).to_be_visible()
    expect(page.locator("#aviso-login a")).to_have_attribute(
        "href", "conta.html?voltar=%2Ffavoritos.html"
    )
    expect(page.locator("#area-favoritos")).to_be_hidden()
    expect(page.locator("#area-historico")).to_be_hidden()


def test_empty_favorites_message(page: Page, api: FakeApi) -> None:
    page.goto("/favoritos.html")
    expect(page.locator("#lista-favoritos")).to_contain_text(
        "Você ainda não salvou nenhum trabalho"
    )
    expect(page.get_by_role("button", name="Exportar todos")).to_be_disabled()


def test_favorites_are_listed_most_recent_first_with_notes(page: Page, api: FakeApi) -> None:
    api.add_favorite(record(1), "primeira nota")
    api.add_favorite(record(2))
    page.goto("/favoritos.html")
    cards = page.locator(".result")
    expect(cards).to_have_count(2)
    expect(cards.first).to_contain_text("número 2")
    expect(page.locator("#contagem-favoritos")).to_have_text("2 favoritos.")
    expect(page.get_by_label("Anotação").nth(1)).to_have_value("primeira nota")
    assert page.probe.errors == []  # type: ignore[attr-defined]


def test_edit_note_with_counter(page: Page, api: FakeApi) -> None:
    api.add_favorite(record(1))
    page.goto("/favoritos.html")
    area = page.get_by_label("Anotação")
    expect(page.locator(".note-editor .hint").first).to_have_text("0/1000")
    area.fill("ler o capítulo 3")
    expect(page.locator(".note-editor .hint").first).to_have_text("16/1000")
    page.get_by_role("button", name="Salvar anotação").click()
    expect(page.locator(".note-editor [role=status]")).to_have_text("Anotação salva.")
    patch = api.calls_to("PATCH", api.favorites[0]["id"])[0]
    assert (
        patch["body"] == {"note": "ler o capítulo 3"}
        and api.favorites[0]["note"] == "ler o capítulo 3"
    )
    assert area.get_attribute("maxlength") == "1000"


def test_remove_asks_for_confirmation(page: Page, api: FakeApi) -> None:
    api.add_favorite(record(1))
    page.goto("/favoritos.html")
    remove = page.get_by_role("button", name="Remover", exact=True)
    remove.click()
    dialog = page.get_by_role("dialog", name="Remover dos favoritos?")
    expect(dialog).to_be_visible()
    expect(
        dialog.get_by_role("button", name="Cancelar")
    ).to_be_focused()  # foco inicial na opção segura
    dialog.get_by_role("button", name="Cancelar").click()
    expect(dialog).to_have_count(0)
    assert len(api.favorites) == 1 and api.calls_to("DELETE", api.favorites[0]["id"]) == []
    expect(remove).to_be_focused()  # o foco volta a quem abriu o diálogo

    remove.click()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog")).to_have_count(0)
    assert len(api.favorites) == 1
    expect(remove).to_be_focused()

    remove.click()
    page.get_by_role("dialog").get_by_role("button", name="Remover").click()
    expect(page.locator("#lista-favoritos")).to_contain_text(
        "Você ainda não salvou nenhum trabalho"
    )
    assert api.favorites == []


def test_search_in_favorites_and_pagination(page: Page, api: FakeApi) -> None:
    for n in range(1, 13):
        api.add_favorite(record(n, title="Robótica na escola" if n == 5 else f"Trabalho comum {n}"))
    page.goto("/favoritos.html")
    expect(page.locator(".result")).to_have_count(10)
    expect(page.locator(".pagination-page")).to_have_text("Página 1 de 2")
    page.get_by_role("button", name="Próxima").click()
    expect(page.locator(".result")).to_have_count(2)
    page.locator("#busca-favoritos").fill("robótica")
    page.get_by_role("button", name="Buscar nos favoritos").click()
    expect(page.locator(".result")).to_have_count(1)
    expect(page.locator("#contagem-favoritos")).to_have_text("1 favorito encontrado.")
    assert any(c["params"].get("q") == "robótica" for c in api.calls_to("GET", "/favorites"))


def test_export_all_favorites_downloads_with_auth(page: Page, api: FakeApi) -> None:
    api.add_favorite(record(1))
    page.goto("/favoritos.html")
    page.locator("#formato-favoritos").select_option("csv")
    with page.expect_download() as info:
        page.get_by_role("button", name="Exportar todos").click()
    assert info.value.suggested_filename == "exportacao-20261009.csv"
    call = api.calls_to("GET", "/favorites/export")[0]
    assert call["params"] == {"format": "csv"} and call["auth"] == f"Bearer {TOKEN}"


# ---------- histórico ----------


def test_history_lists_repeats_and_removes(page: Page, api: FakeApi) -> None:
    api.add_history("educação inclusiva")
    api.add_history(
        "robótica",
        {
            "sources": ["core", "openalex"],
            "year_from": 2018,
            "year_to": 2022,
            "types": ["thesis"],
            "sort": "year_desc",
        },
        total=1234,
    )
    page.goto("/favoritos.html")
    items = page.locator(".history-item")
    expect(items).to_have_count(2)
    expect(items.first).to_contain_text("robótica")
    expect(items.first).to_contain_text("Ano: 2018–2022")
    expect(items.first).to_contain_text("Tipo: Tese ou dissertação")
    expect(items.first).to_contain_text("Ordem: mais recentes")
    expect(items.first).to_contain_text("cerca de 1.234 resultados (estimativa)")
    link = items.first.get_by_role("link", name="Repetir a busca")
    href = link.get_attribute("href")
    assert href.startswith("index.html?q=rob%C3%B3tica")
    for fragment in (
        "year_from=2018",
        "year_to=2022",
        "type=thesis",
        "sources=core%2Copenalex",
        "sort=year_desc",
    ):
        assert fragment in href
    items.nth(1).get_by_role("button", name="Remover a busca").click()
    expect(items).to_have_count(1)
    assert [h["query"] for h in api.history] == ["robótica"]


def test_repeat_search_goes_back_to_the_search_page_with_same_filters(
    page: Page, api: FakeApi
) -> None:
    api.add_history(
        "robótica",
        {
            "sources": None,
            "year_from": 2018,
            "year_to": None,
            "types": ["thesis"],
            "sort": "relevance",
        },
    )
    page.goto("/favoritos.html")
    page.get_by_role("link", name="Repetir a busca").click()
    expect(page.locator(".result")).to_have_count(3)
    last = api.calls_to("GET", "/search")[-1]["params"]
    assert last["q"] == "robótica" and last["year_from"] == "2018" and last["type"] == "thesis"
    expect(page.get_by_label("Buscar trabalhos")).to_have_value("robótica")


def test_clear_all_history_asks_confirmation(page: Page, api: FakeApi) -> None:
    api.add_history("a1")
    api.add_history("b2")
    page.goto("/favoritos.html")
    page.get_by_role("button", name="Limpar todo o histórico").click()
    dialog = page.get_by_role("dialog", name="Limpar todo o histórico?")
    dialog.get_by_role("button", name="Cancelar").click()
    assert len(api.history) == 2
    page.get_by_role("button", name="Limpar todo o histórico").click()
    page.get_by_role("dialog").get_by_role("button", name="Limpar tudo").click()
    expect(page.locator("#lista-historico")).to_contain_text("Seu histórico está vazio")
    assert api.history == []


# ---------- geral ----------


def test_pages_have_no_horizontal_scroll_on_small_screens(page: Page, api: FakeApi) -> None:
    for n in range(1, 4):
        api.add_favorite(record(n), "anotação " * 20)
    api.add_history("uma consulta bem longa " * 4)
    page.set_viewport_size({"width": 320, "height": 800})
    page.goto("/favoritos.html")
    expect(page.locator(".result")).to_have_count(3)
    assert page.evaluate("document.documentElement.scrollWidth") <= 320


def test_favorites_menu_item_and_current_page_marker(page: Page, api: FakeApi) -> None:
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto("/favoritos.html")
    expect(page.get_by_role("link", name="Favoritos", exact=True)).to_have_attribute(
        "aria-current", "page"
    )
    expect(page.get_by_role("heading", level=1)).to_have_text("Favoritos")


def test_expired_session_on_favorites_page_shows_login_notice(page: Page) -> None:
    FakeApi(page, logged_in=False)
    page.add_init_script("sessionStorage.setItem('ash.token', 'velho')")
    page.goto("/favoritos.html")
    expect(page.locator("#aviso-login")).to_be_visible()
    assert page.evaluate("sessionStorage.getItem('ash.token')") is None


def test_stored_xss_in_title_note_and_history_is_not_executed(page: Page, api: FakeApi) -> None:
    payload = '<img src=x onerror="window.__xss=1"><script>window.__xss=2</script>'
    api.add_favorite(
        record(1, title=payload, abstract=payload, authors=[{"name": payload, "orcid": None}]),
        payload,
    )
    api.add_history(payload)
    page.goto("/favoritos.html")
    expect(page.locator(".result")).to_have_count(1)
    page.wait_for_timeout(300)
    assert page.evaluate("window.__xss") is None
    for selector in (".result img", ".result script", ".history-item img", ".history-item script"):
        assert page.locator(selector).count() == 0, selector
    assert "<img src=x" in page.locator(".result-title").inner_text()
    assert page.get_by_label("Anotação").input_value() == payload  # no campo de texto, como texto
    assert "<script>" in page.locator(".history-query").inner_text()
