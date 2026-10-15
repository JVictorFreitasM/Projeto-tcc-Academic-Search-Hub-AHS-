"""Verificação automática de acessibilidade com axe-core (OS-031).

Percorre as telas e estados principais em duas larguras (celular e computador). Falha em
violações `serious` e `critical`; as demais (`minor`, `moderate`) são registradas no relatório
`docs/evidencias/os-031-axe.txt`, sem reprovar. Ferramenta automática detecta só parte dos
problemas: ver docs/ACESSIBILIDADE.md ("Limites da avaliação").
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Page, expect

from tests.e2e.fake_api import FakeApi, record

pytestmark = pytest.mark.a11y

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs" / "evidencias" / "os-031-axe.txt"
VIEWPORTS = {"celular": {"width": 360, "height": 740}, "computador": {"width": 1280, "height": 800}}
BLOCKING = {"serious", "critical"}
OPTIONS = {"resultTypes": ["violations"]}

_findings: list[str] = []
_checked: list[str] = []
_axe = Axe()


def search(page: Page) -> None:
    page.get_by_label("Buscar trabalhos").fill("letramento")
    page.get_by_role("button", name="Buscar", exact=True).click()
    expect(page.locator(".result").first).to_be_visible()


def state_search_empty(page: Page, api: FakeApi) -> None:
    page.goto("/")


def state_search_results(page: Page, api: FakeApi) -> None:
    page.goto("/")
    search(page)


def state_search_by_author(page: Page, api: FakeApi) -> None:
    page.goto("/")
    page.get_by_label("Buscar por").select_option("author")
    page.get_by_label("Nome do autor").fill("Paulo Freire")
    page.get_by_role("button", name="Buscar", exact=True).click()
    expect(page.locator(".result").first).to_be_visible()
    expect(page.get_by_label("Buscar por")).to_have_value("author")


def state_search_no_results(page: Page, api: FakeApi) -> None:
    api.search_results = []
    api.search_total = 0
    page.goto("/")
    page.get_by_label("Buscar trabalhos").fill("asdfgh")
    page.get_by_role("button", name="Buscar", exact=True).click()
    expect(page.locator("#lista-resultados")).to_contain_text("Nenhum resultado")


def state_search_partial_error(page: Page, api: FakeApi) -> None:
    original = api.search_body

    def partial(params: dict[str, str]) -> dict[str, Any]:
        body = original(params)
        body["sources_status"]["core"] = {
            "status": "timeout",
            "count": 0,
            "total": 0,
            "message": "A fonte demorou para responder.",
        }
        return body

    api.search_body = partial  # type: ignore[method-assign]
    page.goto("/")
    search(page)
    expect(page.locator("#avisos-busca .alert-warning")).to_be_visible()


def state_filters_open(page: Page, api: FakeApi) -> None:
    page.goto("/")
    search(page)
    page.get_by_role("button", name="Filtros").click()
    expect(page.locator("#painel-filtros")).to_be_visible()


def state_filters_active(page: Page, api: FakeApi) -> None:
    state_filters_open(page, api)
    page.get_by_label("De", exact=True).fill("2018")
    page.get_by_role("checkbox", name="Artigo", exact=True).check()
    page.get_by_role("button", name="Aplicar").click()
    expect(page.locator(".result").first).to_be_visible()


def state_export_selection(page: Page, api: FakeApi) -> None:
    state_search_results(page, api)
    page.locator(".result input[type=checkbox]").first.check()


def state_favorites(page: Page, api: FakeApi) -> None:
    api.add_favorite(record(1), "Ler com atenção")
    api.add_favorite(record(2))
    api.add_history("letramento digital")
    page.goto("/favoritos.html")
    expect(page.locator("main")).to_be_visible()


def state_favorites_empty(page: Page, api: FakeApi) -> None:
    page.goto("/favoritos.html")
    expect(page.locator("main")).to_be_visible()


def state_dialog_remove_favorite(page: Page, api: FakeApi) -> None:
    api.add_favorite(record(1))
    page.goto("/favoritos.html")
    page.get_by_role("button", name="Remover", exact=True).first.click()
    expect(page.get_by_role("dialog")).to_be_visible()


def state_login(page: Page, api: FakeApi) -> None:
    page.goto("/conta.html")
    expect(page.locator("#form-login")).to_be_visible()


def state_login_validation_errors(page: Page, api: FakeApi) -> None:
    state_login(page, api)
    page.locator("#form-login").get_by_role("button", name="Entrar").click()
    expect(page.locator("#form-login [aria-invalid=true]").first).to_be_visible()


def state_signup(page: Page, api: FakeApi) -> None:
    page.goto("/conta.html")
    expect(page.locator("#form-cadastro")).to_be_visible()


def state_account(page: Page, api: FakeApi) -> None:
    page.goto("/conta.html")
    expect(page.get_by_role("button", name="Excluir minha conta")).to_be_visible()


def state_dialog_delete_account(page: Page, api: FakeApi) -> None:
    state_account(page, api)
    page.get_by_role("button", name="Excluir minha conta").click()
    expect(page.get_by_role("dialog")).to_be_visible()


def state_privacy(page: Page, api: FakeApi) -> None:
    page.goto("/privacidade.html")
    expect(page.get_by_role("heading", level=1)).to_be_visible()


# (nome, estado, logado)
STATES: list[tuple[str, Callable[[Page, FakeApi], None], bool]] = [
    ("busca-vazia", state_search_empty, False),
    ("busca-resultados", state_search_results, False),
    ("busca-por-autor", state_search_by_author, False),
    ("busca-sem-resultados", state_search_no_results, False),
    ("busca-erro-parcial", state_search_partial_error, False),
    ("filtros-abertos", state_filters_open, False),
    ("filtros-ativos", state_filters_active, False),
    ("exportar-selecao", state_export_selection, False),
    ("favoritos", state_favorites, True),
    ("favoritos-vazio", state_favorites_empty, True),
    ("dialogo-remover-favorito", state_dialog_remove_favorite, True),
    ("entrar", state_login, False),
    ("entrar-erros-de-validacao", state_login_validation_errors, False),
    ("criar-conta", state_signup, False),
    ("minha-conta", state_account, True),
    ("dialogo-excluir-conta", state_dialog_delete_account, True),
    ("privacidade", state_privacy, False),
]


def test_axe_detects_known_defects_so_zero_violations_is_meaningful(page: Page) -> None:
    """Sanidade do instrumento: defeitos injetados de propósito precisam ser achados."""
    FakeApi(page, logged_in=False)
    page.goto("/")
    page.evaluate(
        """() => {
            const img = document.createElement('img'); img.src = 'data:image/gif;base64,R0lGODlhAQABAAAAACw=';
            const input = document.createElement('input'); input.type = 'text';
            const button = document.createElement('button');
            document.querySelector('main').append(img, input, button);
        }"""
    )
    ids = {v["id"] for v in _axe.run(page, options=OPTIONS).response["violations"]}
    assert {"image-alt", "label", "button-name"} <= ids, ids


@pytest.fixture(scope="module", autouse=True)
def write_report() -> Iterator[None]:
    yield
    lines = [
        "Saída do axe-core (axe-playwright-python) — OS-031",
        "Regras: conjunto padrão do axe; falha apenas em impacto serious/critical.",
        f"Estados verificados ({len(_checked)}): " + ", ".join(sorted(_checked)),
        "",
    ]
    lines += _findings or [
        "Nenhuma violação (nenhum impacto) reportada pelo axe nos estados acima."
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.mark.parametrize("viewport", VIEWPORTS)
@pytest.mark.parametrize(("name", "setup", "logged_in"), STATES, ids=[s[0] for s in STATES])
def test_axe_has_no_serious_or_critical_violations(
    page: Page,
    name: str,
    setup: Callable[[Page, FakeApi], None],
    logged_in: bool,
    viewport: str,
) -> None:
    page.set_viewport_size(VIEWPORTS[viewport])  # type: ignore[arg-type]
    api = FakeApi(page, logged_in=logged_in)
    setup(page, api)
    violations = _axe.run(page, options=OPTIONS).response["violations"]
    label = f"{name} [{viewport}]"
    _checked.append(label)
    for violation in violations:
        targets = "; ".join(str(n["target"]) for n in violation["nodes"][:3])
        _findings.append(
            f"{label}: {violation['id']} ({violation['impact']}) — {violation['help']} → {targets}"
        )
    blocking = [v for v in violations if v["impact"] in BLOCKING]
    assert not blocking, [f"{v['id']}: {v['help']}" for v in blocking]
