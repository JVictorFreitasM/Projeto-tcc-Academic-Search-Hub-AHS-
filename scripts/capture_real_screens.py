"""Capturas de tela com DADOS REAIS das fontes, para o capítulo 4 do TCC.

Uso: uv run python scripts/capture_real_screens.py

Diferente de `capture_screens.py` (API simulada e dados de demonstração), aqui a aplicação real
roda com o `.env` (chaves do OpenAlex e do CORE), o banco local (índice OAI da UFPE) e as fontes ao
vivo (CORE, OpenAlex e BDTD). Exige o PostgreSQL de desenvolvimento no ar e internet.

Privacidade: a conta usada é de TESTE, com nome e e-mail fictícios (`CONTA_TESTE`); nenhuma chave,
token ou dado pessoal aparece nas imagens. Os resultados mudam com o tempo: a data vai no INDICE.

Saída: docs/evidencias/telas/reais/4.1-RNN-<tela>-<computador|celular>.png e INDICE.md.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import httpx  # noqa: E402
import uvicorn  # noqa: E402
from playwright.sync_api import Browser, Page, expect  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402
from tests.e2e.conftest import _free_port, _start_browser  # noqa: E402

OUT = ROOT / "docs" / "evidencias" / "telas" / "reais"
COMPUTADOR = {"width": 1280, "height": 900}
CELULAR = {"width": 390, "height": 844}
CONTA_TESTE = {
    "full_name": "Conta de Teste",
    "email": "conta.teste@example.org",
    "password": "SenhaDeTeste12345",
}
THEME = "letramento digital"
AUTHOR = "Magda Soares"
RESULT_TIMEOUT_MS = 60_000  # o CORE pode levar dezenas de segundos


@dataclass(frozen=True)
class Shot:
    slug: str
    title: str
    what: str
    setup: Callable[[Page], None]
    size: dict[str, int]
    logged_in: bool = False


def _wait_results(page: Page) -> None:
    expect(page.locator(".result").first).to_be_visible(timeout=RESULT_TIMEOUT_MS)
    expect(page.locator("#resumo-busca")).to_contain_text("fontes", timeout=RESULT_TIMEOUT_MS)


def _search(page: Page, text: str, field: str = "all") -> None:
    page.goto("/")
    page.locator("#tipo-busca").select_option(field)
    page.locator("#campo-busca").fill(text)
    page.get_by_role("button", name="Buscar", exact=True).click()
    _wait_results(page)


def theme(page: Page) -> None:
    _search(page, THEME)
    page.evaluate("window.scrollTo(0, 0)")  # mostra o campo de busca acima dos resultados


def author(page: Page) -> None:
    _search(page, AUTHOR, "author")
    page.evaluate("window.scrollTo(0, 0)")


def filters(page: Page) -> None:
    _search(page, THEME)
    page.get_by_role("button", name="Filtros").click()
    page.get_by_label("De", exact=True).fill("2018")
    page.get_by_label("Até", exact=True).fill("2024")
    page.get_by_role("checkbox", name="Tese ou dissertação", exact=True).check()
    page.get_by_role("button", name="Aplicar").click()
    _wait_results(page)
    page.get_by_role("button", name="Filtros").click()  # mostra o painel com os filtros ativos


def favorites(page: Page) -> None:
    _search(page, THEME)
    buttons = page.get_by_role("button", name="Salvar nos favoritos")
    for index in range(2):
        buttons.nth(0).click()  # o botão salvo muda de nome; o próximo vira o primeiro
        expect(page.get_by_role("button", name="Remover dos favoritos")).to_have_count(index + 1)
    page.goto("/favoritos.html")
    page.get_by_label("Anotação").first.fill("Ler a introdução e o método (anotação de teste).")
    page.get_by_role("button", name="Salvar anotação").first.click()
    expect(page.locator(".note-editor [role=status]").first).to_have_text("Anotação salva.")


def export(page: Page) -> None:
    _search(page, THEME)
    page.get_by_label("Selecionar para exportar").nth(0).check()
    page.get_by_label("Selecionar para exportar").nth(1).check()
    page.locator("#formato-exportar").select_option("bibtex")
    expect(page.locator("#contagem-selecao")).to_contain_text("2 trabalhos")


SHOTS = [
    Shot("R01-resultados-tema", "Busca por tema", f"Busca real por “{THEME}”.", theme, COMPUTADOR),
    Shot(
        "R02-busca-por-autor",
        "Busca por autor",
        f"Busca real pelo autor “{AUTHOR}”.",
        author,
        COMPUTADOR,
    ),
    Shot(
        "R03-filtros-ativos",
        "Filtros",
        "Anos 2018 a 2024 e tipo tese ou dissertação.",
        filters,
        COMPUTADOR,
    ),
    Shot(
        "R04-favoritos",
        "Favoritos",
        "Dois resultados reais salvos, um com anotação.",
        favorites,
        COMPUTADOR,
        True,
    ),
    Shot(
        "R05-exportar",
        "Exportação",
        "Dois resultados reais selecionados para BibTeX.",
        export,
        COMPUTADOR,
    ),
    Shot("R06-resultados", "Resultados no celular", "A busca R01 em 390 px.", theme, CELULAR),
]


def start_server() -> tuple[uvicorn.Server, str]:
    port = _free_port()
    settings = Settings(allowed_origins=f"http://127.0.0.1:{port}")  # type: ignore[call-arg]
    server = uvicorn.Server(
        uvicorn.Config(create_app(settings), host="127.0.0.1", port=port, log_config=None)
    )

    def serve() -> None:
        factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
        with asyncio.Runner(loop_factory=factory) as runner:
            runner.run(server.serve())

    threading.Thread(target=serve, daemon=True).start()
    deadline = time.time() + 20
    while not server.started and time.time() < deadline:
        time.sleep(0.05)
    if not server.started:
        raise RuntimeError("o servidor não iniciou")
    return server, f"http://127.0.0.1:{port}"


def test_account_token(base_url: str) -> str:
    """Cria a conta de teste (se faltar), entra e apaga favoritos e histórico antigos dela."""
    with httpx.Client(base_url=base_url, timeout=30) as client:
        client.post("/api/v1/auth/register", json={**CONTA_TESTE, "accept_privacy_policy": True})
        login = client.post(
            "/api/v1/auth/login",
            json={"email": CONTA_TESTE["email"], "password": CONTA_TESTE["password"]},
        )
        login.raise_for_status()
        token = str(login.json()["access_token"])
        headers = {"Authorization": f"Bearer {token}"}
        for item in client.get("/api/v1/favorites", headers=headers).json().get("items", []):
            client.delete(f"/api/v1/favorites/{item['id']}", headers=headers)
        client.delete("/api/v1/history", headers=headers)
        return token


def capture(browser: Browser, base_url: str, token: str) -> list[tuple[Shot, str]]:
    written: list[tuple[Shot, str]] = []
    for shot in SHOTS:
        context = browser.new_context(base_url=base_url, locale="pt-BR", viewport=shot.size)  # type: ignore[arg-type]
        if shot.logged_in:
            context.add_init_script(f"window.sessionStorage.setItem('ash.token', '{token}');")
        page = context.new_page()
        try:
            shot.setup(page)
            page.wait_for_timeout(500)
            device = "celular" if shot.size is CELULAR else "computador"
            name = f"4.1-{shot.slug}-{device}.png"
            page.screenshot(path=str(OUT / name), full_page=False)
            written.append((shot, name))
            print(f"  ok  {name}")
        finally:
            context.close()
        time.sleep(3)  # pausa entre buscas reais (o CORE recusa chamadas em sequência rápida)
    return written


def write_index(written: list[tuple[Shot, str]]) -> None:
    today = dt.date.today().strftime("%d/%m/%Y")
    lines = [
        "# Capturas com dados reais",
        "",
        f"Geradas em {today} por `scripts/capture_real_screens.py`, com a aplicação real,",
        "as fontes ao vivo (CORE, OpenAlex e BDTD) e o índice OAI-PMH local da UFPE.",
        "Os resultados mudam com o tempo. A conta logada é de teste, com nome e e-mail fictícios.",
        "Legenda: **Fonte: Elaborado pelo Autor (2026)**.",
        "",
        "| Arquivo | Tela | O que mostra |",
        "|---|---|---|",
    ]
    lines += [f"| [{name}]({name}) | {shot.title} | {shot.what} |" for shot, name in written]
    (OUT / "INDICE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    server, base_url = start_server()
    try:
        token = test_account_token(base_url)
        manager, browser = _start_browser()
        try:
            written = capture(browser, base_url, token)
        finally:
            browser.close()
            manager.stop()
        write_index(written)
    finally:
        server.should_exit = True
    print(f"{len(written)} capturas em {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
