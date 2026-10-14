"""Gera as capturas de tela do capítulo 4 do TCC (OS-032), sem intervenção.

Uso: uv run python scripts/capture_screens.py

O frontend é o real, servido pela aplicação. A API é simulada no navegador (a mesma simulação dos
testes de interface), com dados de DEMONSTRAÇÃO: todo título começa com "[DEMONSTRAÇÃO]" e os nomes
e e-mails são fictícios. Nada é gravado no banco e nenhuma fonte externa é consultada, então estas
capturas NÃO mostram resultados reais das fontes (para isso, ver ROTEIRO_REAIS.md).

Saída: docs/evidencias/telas/4.1-NN-<tela>-<computador|celular>.png e INDICE.md.
A página /api/docs carrega o Swagger UI de uma CDN: precisa de internet só nesta captura.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import uvicorn  # noqa: E402
from playwright.sync_api import Browser, Page, expect  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402
from tests.e2e.conftest import _free_port, _start_browser  # noqa: E402
from tests.e2e.fake_api import FakeApi, record  # noqa: E402

OUT = ROOT / "docs" / "evidencias" / "telas"
DEVICES = {"computador": {"width": 1280, "height": 800}, "celular": {"width": 390, "height": 844}}
MARK = "[DEMONSTRAÇÃO]"
LEGEND = "Fonte: Elaborado pelo Autor (2026)"
DEMO_NAME = "Maria Demonstração"
DEMO_EMAIL = "pessoa.demo@example.org"
DEMO_PASSWORD = "SenhaDemo12345"  # noqa: S105 - dado fictício
QUERY = "letramento digital"
TITLES = [
    "Letramento digital na formação de professores",
    "Práticas de leitura mediadas por tecnologias",
    "Inclusão digital em escolas públicas",
    "Avaliação de materiais didáticos digitais",
]


def demo_records(count: int = 4) -> list[dict[str, Any]]:
    kinds = ["article", "thesis", "article", "thesis"]
    return [
        record(
            n + 1,
            title=f"{MARK} {TITLES[n]}",
            authors=[{"name": "Autora Fictícia", "orcid": None}],
            abstract="Resumo fictício, usado apenas para ilustrar a interface.",
            year=2018 + n,
            type=kinds[n],
        )
        for n in range(count)
    ]


# ---------- como chegar a cada tela ----------


def _search(page: Page, count: int | None = 4) -> None:
    page.goto("/")
    page.get_by_label("Buscar trabalhos").fill(QUERY)
    page.get_by_role("button", name="Buscar", exact=True).click()
    if count:
        expect(page.locator(".result")).to_have_count(count)


def empty_search(page: Page, api: FakeApi) -> None:
    page.goto("/")
    expect(page.get_by_role("search")).to_be_visible()


def results(page: Page, api: FakeApi) -> None:
    _search(page)


def partial_error(page: Page, api: FakeApi) -> None:
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
    _search(page)
    expect(page.locator("#avisos-busca .alert-warning")).to_be_visible()


def no_results(page: Page, api: FakeApi) -> None:
    api.search_results, api.search_total = [], 0
    _search(page, count=None)
    expect(page.locator("#lista-resultados")).to_contain_text("Nenhum resultado")


def filters_open(page: Page, api: FakeApi) -> None:
    _search(page)
    page.get_by_role("button", name="Filtros").click()
    expect(page.locator("#painel-filtros")).to_be_visible()


def filters_active(page: Page, api: FakeApi) -> None:
    _search(page)
    page.get_by_role("button", name="Filtros").click()
    page.get_by_label("De", exact=True).fill("2018")
    page.get_by_label("Até", exact=True).fill("2020")
    page.get_by_role("checkbox", name="Artigo", exact=True).check()
    api.search_results = api.search_results[:2]  # a simulação não filtra: reduz à mão
    page.get_by_role("button", name="Aplicar").click()
    expect(page.locator(".result")).to_have_count(2)


def export_selection(page: Page, api: FakeApi) -> None:
    _search(page)
    page.get_by_label("Selecionar para exportar").nth(0).check()
    page.get_by_label("Selecionar para exportar").nth(2).check()
    page.locator("#formato-exportar").select_option("bibtex")
    expect(page.locator("#contagem-selecao")).to_contain_text("2 trabalhos")


def favorites(page: Page, api: FakeApi) -> None:
    for rec in demo_records(3):
        api.add_favorite(rec)
    page.goto("/favoritos.html")
    expect(page.locator("#contagem-favoritos")).to_contain_text("3")


def annotation(page: Page, api: FakeApi) -> None:
    api.add_favorite(demo_records(1)[0])
    page.goto("/favoritos.html")
    page.get_by_label("Anotação").fill("Ler o capítulo 3 antes da reunião (nota fictícia).")
    page.get_by_role("button", name="Salvar anotação").click()
    expect(page.locator(".note-editor [role=status]")).to_have_text("Anotação salva.")


def history(page: Page, api: FakeApi) -> None:
    api.add_history(QUERY, total=1234)
    api.add_history("inclusão digital", total=480)
    api.add_history("avaliação de materiais didáticos", total=95)
    page.goto("/favoritos.html")
    expect(page.get_by_role("link", name="Repetir a busca").first).to_be_visible()


def signup(page: Page, api: FakeApi) -> None:
    page.goto("/conta.html")
    page.get_by_label("Nome completo").fill(DEMO_NAME)
    page.locator("#email-cadastro").fill(DEMO_EMAIL)
    page.locator("#senha-cadastro").fill(DEMO_PASSWORD)
    page.get_by_label("Li e aceito a").check()


def login(page: Page, api: FakeApi) -> None:
    page.goto("/conta.html")
    page.locator("#email-login").fill(DEMO_EMAIL)
    expect(page.locator("#form-login")).to_be_visible()


def account(page: Page, api: FakeApi) -> None:
    api.user.update(full_name=DEMO_NAME, email=DEMO_EMAIL)
    page.goto("/conta.html")
    expect(page.get_by_role("button", name="Excluir minha conta")).to_be_visible()


def delete_account(page: Page, api: FakeApi) -> None:
    account(page, api)
    page.get_by_role("button", name="Excluir minha conta").click()
    expect(page.get_by_role("dialog")).to_be_visible()


def privacy(page: Page, api: FakeApi) -> None:
    page.goto("/privacidade.html")
    expect(page.get_by_role("heading", level=1)).to_be_visible()
    page.wait_for_function(
        "document.querySelector('#politica')?.getAttribute('aria-busy') !== 'true'"
    )


def api_docs(page: Page, api: FakeApi) -> None:
    page.goto("/api/docs")
    try:
        page.wait_for_selector(".swagger-ui .opblock", timeout=20000)
    except Exception:
        print("  aviso: o Swagger UI não carregou (sem internet?); a captura sai sem as rotas.")


@dataclass(frozen=True)
class Screen:
    slug: str
    title: str
    shows: str
    logged_in: bool
    setup: Callable[[Page, FakeApi], None]
    section: str = "4.1"
    full_page: bool = True  # diálogo modal: só a janela visível, onde o fundo escurece por inteiro


SCREENS: list[Screen] = [
    Screen(
        "busca-vazia",
        "Busca vazia",
        "Tela inicial com o campo de busca e as dicas.",
        False,
        empty_search,
    ),
    Screen(
        "resultados", "Resultados", "Lista unificada com selo da fonte e do tipo.", False, results
    ),
    Screen(
        "erro-parcial",
        "Erro parcial",
        "Aviso quando uma fonte falha e as outras respondem.",
        False,
        partial_error,
    ),
    Screen("sem-resultados", "Sem resultados", "Mensagem de nenhum resultado.", False, no_results),
    Screen(
        "filtros-abertos",
        "Filtros abertos",
        "Painel de filtros por ano, tipo e ordem.",
        False,
        filters_open,
    ),
    Screen(
        "filtros-ativos",
        "Filtros ativos",
        "Resultados com os filtros aplicados e etiquetas ativas.",
        False,
        filters_active,
    ),
    Screen(
        "favoritos", "Favoritos", "Lista de trabalhos salvos pela pessoa logada.", True, favorites
    ),
    Screen("anotacao", "Anotação", "Anotação pessoal num favorito, já salva.", True, annotation),
    Screen(
        "exportar",
        "Exportar",
        "Seleção de resultados e escolha do formato.",
        False,
        export_selection,
    ),
    Screen("historico", "Histórico", "Buscas anteriores com o link para repetir.", True, history),
    Screen(
        "cadastro",
        "Cadastro com consentimento",
        "Formulário de cadastro com o aceite da política.",
        False,
        signup,
    ),
    Screen("login", "Entrar", "Formulário de login.", False, login),
    Screen(
        "minha-conta",
        "Minha conta",
        "Direitos do titular: ver, corrigir, baixar e excluir.",
        True,
        account,
    ),
    Screen(
        "excluir-conta",
        "Excluir conta",
        "Diálogo de confirmação com a senha.",
        True,
        delete_account,
        full_page=False,
    ),
    Screen(
        "politica-privacidade",
        "Política de privacidade",
        "Texto da política (LGPD).",
        False,
        privacy,
    ),
    Screen("api-docs", "Documentação da API", "Swagger UI em /api/docs.", False, api_docs),
]


def filename(index: int, screen: Screen, device: str) -> str:
    return f"4.1-{index:02d}-{screen.slug}-{device}.png"


# ---------- execução ----------


def start_server() -> tuple[uvicorn.Server, threading.Thread, str]:
    port = _free_port()
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None, allowed_origins=f"http://127.0.0.1:{port}", docs_enabled=True
    )
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(settings), host="127.0.0.1", port=port, log_config=None, lifespan="on"
        )
    )

    def serve() -> None:
        factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
        with asyncio.Runner(loop_factory=factory) as runner:
            runner.run(server.serve())

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    deadline = time.time() + 15
    while not server.started and time.time() < deadline:
        time.sleep(0.05)
    if not server.started:
        raise RuntimeError("o servidor não iniciou")
    return server, thread, f"http://127.0.0.1:{port}"


def capture(browser: Browser, base_url: str) -> list[str]:
    written: list[str] = []
    for device, size in DEVICES.items():
        for index, screen in enumerate(SCREENS, start=1):
            context = browser.new_context(base_url=base_url, locale="pt-BR", viewport=size)  # type: ignore[arg-type]
            page = context.new_page()
            api = FakeApi(page, logged_in=screen.logged_in)
            api.search_results = demo_records()
            api.search_total = 1234
            try:
                screen.setup(page, api)
                page.wait_for_timeout(250)  # deixa a interface assentar
                name = filename(index, screen, device)
                page.screenshot(path=str(OUT / name), full_page=screen.full_page)
                written.append(name)
                print(f"  ok  {name}")
            finally:
                context.close()
    return written


def write_index(written: list[str]) -> None:
    lines = [
        "# Índice das capturas de tela",
        "",
        f"Legenda para o TCC: **{LEGEND}**.",
        "",
        f"> Todas as capturas usam dados de **demonstração** (títulos começam com `{MARK}`; "
        "nomes e e-mails fictícios) e a API simulada. **Não são resultados reais das fontes.** "
        "Para capturas com dados reais, siga `ROTEIRO_REAIS.md`. "
        "Gerado por `scripts/capture_screens.py`.",
        "",
        'A coluna "Seção do TCC" indica onde a captura cabe; ajuste a subseção ao texto final.',
        "",
        "| # | Tela | O que mostra | Seção do TCC | Computador | Celular |",
        "|---|---|---|---|---|---|",
    ]
    for index, screen in enumerate(SCREENS, start=1):
        desktop, phone = (filename(index, screen, d) for d in DEVICES)
        assert desktop in written and phone in written  # noqa: S101 - script de desenvolvimento
        lines.append(
            f"| {index:02d} | {screen.title} | {screen.shows} | {screen.section} "
            f"| [{desktop}]({desktop}) | [{phone}]({phone}) |"
        )
    lines += [
        "",
        "A captura 16 (`/api/docs`) depende de internet (o Swagger UI vem de uma CDN). Se a CDN "
        "estiver fora do ar, a imagem sai sem a lista de rotas: rode o script de novo.",
    ]
    (OUT / "INDICE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    logging.disable(logging.INFO)  # o servidor local não precisa poluir a saída do script
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("4.1-*.png"):
        old.unlink()
    server, thread, base_url = start_server()
    manager, browser = _start_browser()
    try:
        print(f"Gerando capturas em {OUT} ...")
        written = capture(browser, base_url)
        write_index(written)
    finally:
        with contextlib.suppress(Exception):
            browser.close()
        manager.stop()
        server.should_exit = True
        thread.join(timeout=10)
    print(f"{len(written)} capturas geradas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
