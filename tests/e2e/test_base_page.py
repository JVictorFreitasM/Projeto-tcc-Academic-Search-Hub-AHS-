import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def test_home_opens_without_console_or_csp_errors(page: Page) -> None:
    page.goto("/")
    expect(page.locator("html")).to_have_attribute("lang", "pt-BR")
    expect(page.locator("h1")).to_have_text("Busca de trabalhos acadêmicos")
    assert page.locator("h1").count() == 1
    page.wait_for_load_state("networkidle")
    assert page.probe.errors == []  # type: ignore[attr-defined]


def test_landmarks_and_title(page: Page) -> None:
    page.goto("/")
    for landmark in ("header", "main", "footer"):
        assert page.locator(landmark).count() == 1, landmark
    assert page.get_by_role("navigation", name="Principal").count() == 1
    assert page.title().startswith("Academic Search Hub")
    assert (
        page.get_attribute("meta[name=viewport]", "content")
        == "width=device-width, initial-scale=1"
    )
    assert page.locator("#announcer[aria-live]").count() == 1


def test_security_headers_are_served_with_the_page(page: Page) -> None:
    response = page.goto("/")
    assert response is not None
    headers = response.headers
    assert "script-src 'self'" in headers["content-security-policy"]
    assert headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize("width", [320, 768, 1280])
def test_no_horizontal_scroll(page: Page, width: int) -> None:
    page.set_viewport_size({"width": width, "height": 800})
    page.goto("/")
    page.wait_for_load_state("networkidle")
    scroll_width = page.evaluate("document.documentElement.scrollWidth")
    assert scroll_width <= width, f"rolagem horizontal a {width}px: {scroll_width}"


def test_no_horizontal_scroll_with_200_percent_zoom(page: Page) -> None:
    # 200% de zoom equivale a metade da largura útil: 640 px de viewport CSS vira 320
    page.set_viewport_size({"width": 320, "height": 640})
    page.goto("/")
    # via CSSOM: a CSP (style-src 'self') bloqueia <style> injetado, mas não a propriedade style
    page.evaluate("document.documentElement.style.fontSize = '200%'")
    assert page.evaluate("document.documentElement.scrollWidth") <= 320


def test_keyboard_order_and_visible_focus_on_desktop(page: Page) -> None:
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto("/")
    order = []
    for _ in range(3):
        page.keyboard.press("Tab")
        order.append(page.evaluate("document.activeElement.textContent.trim()"))
    assert order == ["Pular para o conteúdo", "Academic Search Hub", "Busca"]
    outline = page.evaluate(
        "(() => { const s = getComputedStyle(document.activeElement);"
        " return [s.outlineStyle, parseFloat(s.outlineWidth)]; })()"
    )
    assert outline[0] == "solid" and outline[1] >= 3


def test_skip_link_moves_focus_to_main(page: Page) -> None:
    page.goto("/")
    page.keyboard.press("Tab")
    page.keyboard.press("Enter")
    assert page.url.endswith("#conteudo")


def test_mobile_menu_button_toggles_and_escape_closes(page: Page) -> None:
    page.set_viewport_size({"width": 375, "height": 700})
    page.goto("/")
    button = page.get_by_role("button", name="Menu")
    nav = page.locator("#menu-principal")
    expect(button).to_have_attribute("aria-expanded", "false")
    expect(nav).to_be_hidden()
    button.click()
    expect(button).to_have_attribute("aria-expanded", "true")
    expect(nav).to_be_visible()
    page.keyboard.press("Escape")
    expect(button).to_have_attribute("aria-expanded", "false")
    expect(nav).to_be_hidden()


def test_menu_button_is_hidden_on_wide_screens(page: Page) -> None:
    page.set_viewport_size({"width": 1024, "height": 700})
    page.goto("/")
    expect(page.get_by_role("button", name="Menu")).to_be_hidden()
    expect(page.locator("#menu-principal")).to_be_visible()


def test_current_page_is_marked_in_the_menu(page: Page) -> None:
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto("/")
    expect(page.get_by_role("link", name="Busca", exact=True)).to_have_attribute(
        "aria-current", "page"
    )


def test_touch_targets_are_at_least_44px(page: Page) -> None:
    page.set_viewport_size({"width": 375, "height": 700})
    page.goto("/")
    page.get_by_role("button", name="Menu").click()
    for selector in (".brand", ".nav-toggle", ".site-nav a", ".site-footer a"):
        box = page.locator(selector).first.bounding_box()
        assert box is not None and box["height"] >= 43.5, (selector, box)


def test_unknown_page_returns_json_error_not_a_stack_trace(page: Page) -> None:
    response = page.goto("/nao-existe.html")
    assert response is not None and response.status == 404
    assert "Traceback" not in page.content()
