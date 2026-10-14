"""Fluxos de ponta a ponta (OS-032): navegador real, servidor real, banco de teste e conectores falsos.

Diferente dos outros testes de interface, aqui a API não é interceptada: as chamadas passam pela
aplicação de verdade (autenticação, favoritos, histórico, exportação, LGPD) e pelo PostgreSQL de
teste. Só as fontes externas são trocadas por conectores falsos de dados fixos e fictícios.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import sys
import threading
import time
from collections.abc import Iterator
from typing import Any

import pytest
import uvicorn
from playwright.sync_api import Browser, BrowserContext, Page, expect
from sqlalchemy import create_engine, text

from app.connectors.base import SourcePage, SourceQuery
from app.core.config import Settings, get_settings
from app.core.rate_limit import limiter
from app.db import session as db_session
from app.main import create_app
from app.schemas.common import RecordType
from app.schemas.record import AuthorOut, RecordOut, SourceRef
from app.services.search_service import SearchService
from tests.e2e.conftest import LiveServer, _free_port
from tests.integration.conftest import migrated_db_url  # noqa: F401

pytestmark = pytest.mark.e2e

SECRET = "f" * 40
PASSWORD = "Senha12345"
EMAIL = "maria.fluxos@exemplo.com"
NAME = "Maria de Souza"


# ---------- conectores falsos, com dados fictícios e fixos ----------


def _rec(source: str, n: int, title: str, year: int, kind: RecordType, doi: str) -> RecordOut:
    return RecordOut(
        id=f"doi:{doi}",
        title=f"{title} (dado fictício)",
        authors=[AuthorOut(name=f"Autora Fictícia {n}")],
        abstract="Resumo fictício usado nos testes de fluxo.",
        year=year,
        doi=doi,
        type=kind,
        language="pt",
        sources=[SourceRef(source=source, source_id=f"{source}-{n}")],
    )


OPENALEX_DATA = [
    _rec("openalex", 1, "Letramento digital na escola A", 2018, RecordType.ARTICLE, "10.9999/a1"),
    _rec("openalex", 2, "Letramento digital na escola B", 2020, RecordType.ARTICLE, "10.9999/a2"),
    _rec("openalex", 3, "Letramento digital na escola C", 2021, RecordType.THESIS, "10.9999/a3"),
    _rec("openalex", 4, "Letramento digital na escola D", 2022, RecordType.ARTICLE, "10.9999/a4"),
]
CORE_DATA = [
    _rec("core", 3, "Letramento digital na escola C", 2021, RecordType.THESIS, "10.9999/a3"),
    _rec("core", 5, "Letramento digital na escola E", 2021, RecordType.ARTICLE, "10.9999/b5"),
]


class FixedConnector:
    """Fonte falsa: devolve dados fixos, respeitando filtros de ano e tipo."""

    kind = "api"
    supports_year_sort = True

    def __init__(self, slug: str, data: list[RecordOut]) -> None:
        self.slug, self.name, self.data = slug, slug.upper(), data

    def is_enabled(self) -> bool:
        return True

    async def availability(self) -> tuple[bool, str | None]:
        return True, None

    async def search(self, query: SourceQuery) -> SourcePage:
        items = [
            r.model_copy(deep=True)
            for r in self.data
            if (query.year_from is None or (r.year or 0) >= query.year_from)
            and (query.year_to is None or (r.year or 0) <= query.year_to)
            and (not query.types or r.type in query.types)
        ]
        return SourcePage(records=items, total=len(items))


# ---------- servidor e navegador ----------


@pytest.fixture(scope="module")
def flow_server(migrated_db_url: str) -> Iterator[LiveServer]:  # noqa: F811
    """Aplicação real com o banco de teste e conectores falsos, em outra thread."""
    overrides = {
        "DATABASE_URL": migrated_db_url,
        "SECRET_KEY": SECRET,
        "RATE_LIMIT_SEARCH": "1000/minute",
        "RATE_LIMIT_AUTH": "1000/minute",
    }
    previous = {key: os.environ.get(key) for key in overrides}
    os.environ.update(overrides)
    caches = (get_settings, db_session.get_engine, db_session.get_sessionmaker)
    for cached in caches:
        cached.cache_clear()
    limiter.reset()

    port = _free_port()
    settings = Settings(_env_file=None, allowed_origins=f"http://127.0.0.1:{port}")  # type: ignore[call-arg]
    app = create_app(settings)
    app.state.search_service = SearchService(
        [FixedConnector("openalex", OPENALEX_DATA), FixedConnector("core", CORE_DATA)],  # type: ignore[list-item]
        settings,
    )
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_config=None, lifespan="on")
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
    assert server.started, "o servidor de fluxos não iniciou"
    yield LiveServer(f"http://127.0.0.1:{port}")
    server.should_exit = True
    thread.join(timeout=10)
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    for cached in caches:
        cached.cache_clear()
    limiter.reset()


@pytest.fixture(autouse=True)
def clean_db(migrated_db_url: str) -> Iterator[None]:  # noqa: F811
    """Cada fluxo começa sem usuários, favoritos nem histórico."""

    def wipe() -> None:
        engine = create_engine(migrated_db_url)
        with engine.begin() as connection:
            connection.execute(text("TRUNCATE users CASCADE"))
        engine.dispose()

    wipe()
    limiter.reset()
    yield
    wipe()


@pytest.fixture
def flow_context(browser: Browser, flow_server: LiveServer) -> Iterator[BrowserContext]:
    ctx = browser.new_context(
        base_url=flow_server.base_url, locale="pt-BR", viewport={"width": 1280, "height": 900}
    )
    yield ctx
    ctx.close()


@pytest.fixture
def fpage(flow_context: BrowserContext) -> Page:
    return flow_context.new_page()


# ---------- ações reutilizadas ----------


def search(page: Page, expected: int, text_: str = "letramento") -> None:
    page.get_by_label("Buscar trabalhos").fill(text_)
    page.get_by_role("button", name="Buscar", exact=True).click()
    expect(page.locator(".result")).to_have_count(expected)


def sign_up(page: Page) -> None:
    page.goto("/conta.html")
    page.get_by_label("Nome completo").fill(NAME)
    page.locator("#email-cadastro").fill(EMAIL)
    page.locator("#senha-cadastro").fill(PASSWORD)
    page.get_by_label("Li e aceito a").check()
    page.get_by_role("button", name="Criar conta").click()
    expect(page.get_by_role("heading", level=1)).to_have_text("Minha conta")


def log_in_keeping_session(page: Page) -> None:
    """Sai e entra de novo com "Manter conectado nesta aba": sem isso o token fica só em memória
    e se perde ao trocar de página (decisão de segurança da OS-023)."""
    page.get_by_role("button", name="Sair").click()
    page.locator("#email-login").fill(EMAIL)
    page.locator("#senha-login").fill(PASSWORD)
    page.get_by_label("Manter conectado nesta aba").check()
    page.get_by_role("button", name="Entrar").last.click()
    expect(page.get_by_role("heading", level=1)).to_have_text("Minha conta")
    expect(page.get_by_role("button", name="Sair")).to_be_visible()


def read_download(download: Any) -> str:
    with open(download.path(), encoding="utf-8") as handle:
        return handle.read()


def titles(page: Page) -> list[str]:
    return [t.strip() for t in page.locator(".result h2, .result h3").all_inner_texts()]


# ---------- (a) visitante busca e exporta ----------


def test_visitor_searches_and_exports_results(fpage: Page, flow_server: LiveServer) -> None:
    fpage.goto("/")
    search(fpage, expected=5)  # 4 + 2 resultados, com 1 duplicata fundida por DOI
    expect(fpage.locator("#resumo-busca")).to_contain_text("2 de 2 fontes responderam")
    fpage.get_by_label("Selecionar para exportar").nth(0).check()
    fpage.get_by_label("Selecionar para exportar").nth(1).check()
    fpage.locator("#formato-exportar").select_option("csv")
    with fpage.expect_download() as info:
        fpage.get_by_role("button", name="Exportar selecionados").click()
    content = read_download(info.value)
    assert info.value.suggested_filename.endswith(".csv")
    assert content.count("(dado fictício)") == 2
    assert "Letramento digital na escola" in content


# ---------- (b) cadastro → login → busca → favorita → anota → exporta ----------


def test_signup_search_favorite_annotate_and_export_favorites(fpage: Page) -> None:
    sign_up(fpage)
    log_in_keeping_session(fpage)
    fpage.get_by_role("link", name="Busca", exact=True).first.click()
    search(fpage, expected=5)
    button = fpage.locator(".favorite-button").first
    expect(button).to_have_text("Salvar nos favoritos")
    button.click()
    expect(button).to_have_text("Remover dos favoritos")

    fpage.goto("/favoritos.html")
    expect(fpage.locator("#contagem-favoritos")).to_contain_text("1")
    fpage.get_by_label("Anotação").fill("ler o capítulo 3")
    fpage.get_by_role("button", name="Salvar anotação").click()
    expect(fpage.locator(".note-editor [role=status]")).to_have_text("Anotação salva.")

    fpage.reload()  # a anotação veio do banco, não da memória da página
    expect(fpage.get_by_label("Anotação")).to_have_value("ler o capítulo 3")

    fpage.locator("#formato-favoritos").select_option("csv")
    with fpage.expect_download() as info:
        fpage.get_by_role("button", name="Exportar todos").click()
    assert "(dado fictício)" in read_download(info.value)


# ---------- (c) filtros ----------


def test_filters_narrow_the_results(fpage: Page) -> None:
    fpage.goto("/")
    search(fpage, expected=5)
    fpage.get_by_role("button", name="Filtros").click()
    fpage.get_by_label("De", exact=True).fill("2020")
    fpage.get_by_label("Até", exact=True).fill("2021")
    fpage.get_by_role("button", name="Aplicar").click()
    expect(fpage.locator(".result")).to_have_count(3)  # B, C (tese) e E

    fpage.get_by_role("button", name="Filtros").click()
    fpage.get_by_role("checkbox", name="Artigo", exact=True).check()
    fpage.get_by_role("button", name="Aplicar").click()
    expect(fpage.locator(".result")).to_have_count(2)  # B e E
    assert "year_from=2020" in fpage.url and "year_to=2021" in fpage.url
    for title in titles(fpage):
        assert "escola C" not in title and "escola A" not in title and "escola D" not in title


# ---------- (d) histórico → repetir busca ----------


def test_history_lists_the_search_and_repeats_it(fpage: Page) -> None:
    sign_up(fpage)
    log_in_keeping_session(fpage)
    fpage.get_by_role("link", name="Busca", exact=True).first.click()
    search(fpage, expected=5)
    fpage.goto("/favoritos.html")
    items = fpage.locator("#lista-historico li, #lista-historico .history-item")
    expect(items.first).to_contain_text("letramento")  # gravado em segundo plano, no banco
    fpage.get_by_role("link", name="Repetir a busca").first.click()
    expect(fpage.locator(".result")).to_have_count(5)
    expect(fpage.get_by_label("Buscar trabalhos")).to_have_value("letramento")


# ---------- (e) baixar dados → excluir conta → login falha ----------


def test_download_data_delete_account_and_login_fails(fpage: Page) -> None:
    sign_up(fpage)
    with fpage.expect_download() as info:
        fpage.get_by_role("button", name="Baixar meus dados").click()
    data = json.loads(read_download(info.value))
    assert data["account"]["email"] == EMAIL

    fpage.get_by_role("button", name="Excluir minha conta").click()
    dialog = fpage.get_by_role("dialog")
    dialog.get_by_label("Digite sua senha para confirmar").fill(PASSWORD)
    dialog.get_by_role("button", name="Excluir definitivamente").click()
    fpage.wait_for_url("**/index.html?conta_excluida=1")
    expect(fpage.locator(".alert-success")).to_contain_text("Conta excluída.")

    fpage.goto("/conta.html")
    fpage.locator("#email-login").fill(EMAIL)
    fpage.locator("#senha-login").fill(PASSWORD)
    fpage.locator("#form-login").get_by_role("button", name="Entrar").click()
    expect(fpage.locator("#erro-login")).to_contain_text("E-mail ou senha inválidos.")
    with contextlib.suppress(Exception):
        assert fpage.evaluate("sessionStorage.getItem('ash.token')") is None
