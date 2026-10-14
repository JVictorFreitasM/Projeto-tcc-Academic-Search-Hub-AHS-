import json
from typing import Any

import pytest
from playwright.sync_api import Page, Route, expect

pytestmark = pytest.mark.e2e

USER = {
    "id": "11111111-1111-1111-1111-111111111111",
    "full_name": "Maria de Souza",
    "email": "maria@exemplo.com",
    "created_at": "2026-10-09T10:00:00Z",
    "consent_at": "2026-10-09T10:00:00Z",
    "consent_policy_version": "1.0",
}
POLICY = {
    "version": "1.0",
    "content": (
        "# Política de Privacidade\n\nTexto com **negrito** e *itálico* e <script>window.__xss=1</script>"
        " e <img src=x onerror=window.__xss=2>.\n\n## Quais dados tratamos\n\n- Nome e e-mail\n- Senha em *hash*\n\n"
        "## Seus direitos\n\nContato: {CONTATO_DO_RESPONSAVEL}.\n"
    ),
}


class Server:
    """API simulada de autenticação."""

    def __init__(self, page: Page) -> None:
        self.requests: list[tuple[str, str, Any, dict[str, str]]] = []
        self.login = lambda body: (
            200,
            {
                "access_token": "tok-123",
                "token_type": "bearer",
                "expires_in": 3600,
                "consent_required": False,
            },
        )
        self.register = lambda body: (201, USER)
        self.me = lambda headers: (
            (200, USER)
            if headers.get("authorization") == "Bearer tok-123"
            else (401, error("unauthorized", "Sessão inválida."))
        )
        page.route(
            "**/api/v1/auth/login", lambda r: self._handle(r, lambda: self.login(self._body(r)))
        )
        page.route(
            "**/api/v1/auth/register",
            lambda r: self._handle(r, lambda: self.register(self._body(r))),
        )
        page.route("**/api/v1/me", lambda r: self._handle(r, lambda: self.me(r.request.headers)))
        page.route("**/api/v1/privacy", lambda r: r.fulfill(status=200, json=POLICY))

    @staticmethod
    def _body(route: Route) -> Any:
        data = route.request.post_data
        return json.loads(data) if data else None

    def _handle(self, route: Route, produce: Any) -> None:
        self.requests.append(
            (
                route.request.method,
                route.request.url,
                self._body(route),
                dict(route.request.headers),
            )
        )
        status, body = produce()
        route.fulfill(status=status, content_type="application/json", body=json.dumps(body))

    def posted(self, suffix: str) -> list[Any]:
        return [b for m, u, b, _ in self.requests if m == "POST" and u.endswith(suffix)]


def error(code: str, message: str, details: list[dict[str, str]] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details or []}}


@pytest.fixture
def server(page: Page) -> Server:
    return Server(page)


def fill_signup(page: Page, *, consent: bool = True, secret: str = "Senha12345") -> None:  # noqa: S107
    page.get_by_label("Nome completo").fill("Maria de Souza")
    page.locator("#email-cadastro").fill("maria@exemplo.com")
    page.locator("#senha-cadastro").fill(secret)
    if consent:
        page.get_by_label("Li e aceito a").check()


def test_page_has_both_forms_with_labels_and_autocomplete(page: Page, server: Server) -> None:
    page.goto("/conta.html")
    expect(page.get_by_role("heading", level=1)).to_have_text("Entrar ou criar conta")
    assert page.locator("#email-login").get_attribute("autocomplete") == "email"
    assert page.locator("#senha-login").get_attribute("autocomplete") == "current-password"
    assert page.locator("#nome-cadastro").get_attribute("autocomplete") == "name"
    assert page.locator("#email-cadastro").get_attribute("autocomplete") == "email"
    assert page.locator("#senha-cadastro").get_attribute("autocomplete") == "new-password"
    unlabeled = page.evaluate(
        "[...document.querySelectorAll('input')].filter(i => !i.labels.length).map(i => i.id)"
    )
    assert unlabeled == []
    expect(page.locator("#regras-senha")).to_contain_text(
        "10 a 128 caracteres"
    )  # regras visíveis antes de digitar
    assert "regras-senha" in page.locator("#senha-cadastro").get_attribute("aria-describedby")
    assert page.probe.errors == []  # type: ignore[attr-defined]


def test_consent_link_points_to_the_privacy_page(page: Page, server: Server) -> None:
    page.goto("/conta.html")
    link = page.get_by_role("link", name="Política de Privacidade", exact=True)
    expect(link).to_have_attribute("href", "privacidade.html")
    expect(link).to_have_attribute("rel", "noopener noreferrer")


def test_signup_without_consent_does_not_send_and_shows_accessible_message(
    page: Page, server: Server
) -> None:
    page.goto("/conta.html")
    fill_signup(page, consent=False)
    page.get_by_role("button", name="Criar conta").click()
    box = page.get_by_label("Li e aceito a")
    expect(box).to_have_attribute("aria-invalid", "true")
    expect(page.locator("#erro-consentimento")).to_have_text(
        "É preciso aceitar a Política de Privacidade para criar a conta."
    )
    assert "erro-consentimento" in box.get_attribute("aria-describedby")
    assert server.posted("/auth/register") == []
    assert page.evaluate("document.activeElement.id") == "consentimento"
    box.check()
    expect(page.locator("#erro-consentimento")).to_be_hidden()


@pytest.mark.parametrize(
    ("password", "fragment"),
    [
        ("curta1", "ao menos 10"),
        ("somenteletrasaqui", "uma letra e um número"),
        ("1234567890123", "uma letra e um número"),
        ("xxmaria@exemplo.comx1", "conter o seu e-mail"),
    ],
)
def test_signup_password_rules_are_checked_before_sending(
    page: Page, server: Server, password: str, fragment: str
) -> None:
    page.goto("/conta.html")
    fill_signup(page, secret=password)
    page.get_by_role("button", name="Criar conta").click()
    expect(page.locator("#erro-senha-cadastro")).to_contain_text(fragment)
    expect(page.locator("#senha-cadastro")).to_have_attribute("aria-invalid", "true")
    assert server.posted("/auth/register") == []


def test_signup_success_sends_consent_and_signs_in(page: Page, server: Server) -> None:
    page.goto("/conta.html")
    fill_signup(page)
    page.get_by_role("button", name="Criar conta").click()
    expect(page.get_by_role("heading", level=1)).to_have_text("Minha conta")
    body = server.posted("/auth/register")[0]
    assert body == {
        "full_name": "Maria de Souza",
        "email": "maria@exemplo.com",
        "password": "Senha12345",
        "accept_privacy_policy": True,
    }
    assert server.posted("/auth/login")[0] == {
        "email": "maria@exemplo.com",
        "password": "Senha12345",
    }
    expect(page.locator("#conta-logada")).to_contain_text("Dados da conta")
    expect(page.locator("#conta-logada")).to_contain_text("Maria de Souza")
    expect(page.locator("#conta-visitante")).to_be_hidden()
    expect(page.get_by_role("button", name="Sair")).to_be_visible()


def test_signup_server_errors_go_to_the_right_fields(page: Page, server: Server) -> None:
    server.register = lambda body: (
        422,
        error(
            "validation_error",
            "Dados inválidos.",
            [
                {"field": "email", "issue": "e-mail inválido"},
                {"field": "", "issue": "a senha deve ter ao menos uma letra e um número"},
            ],
        ),
    )
    page.goto("/conta.html")
    fill_signup(page)
    page.get_by_role("button", name="Criar conta").click()
    expect(page.locator("#erro-email-cadastro")).to_have_text("E-mail inválido.")
    expect(page.locator("#erro-senha-cadastro")).to_contain_text("uma letra e um número")
    assert page.evaluate("document.activeElement.id") == "email-cadastro"
    expect(page.locator("#email-cadastro")).to_have_attribute("aria-invalid", "true")


def test_signup_conflict_shows_generic_message_only(page: Page, server: Server) -> None:
    server.register = lambda body: (409, error("conflict", "Não foi possível concluir o cadastro."))
    page.goto("/conta.html")
    fill_signup(page)
    page.get_by_role("button", name="Criar conta").click()
    box = page.locator("#erro-cadastro")
    expect(box).to_have_attribute("role", "alert")
    expect(box).to_have_text("Erro: Não foi possível concluir o cadastro.")
    assert "já existe" not in box.inner_text().lower()


def test_login_success_updates_header_and_logout_clears_state(page: Page, server: Server) -> None:
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto("/conta.html")
    expect(page.get_by_role("link", name="Entrar", exact=True).first).to_be_visible()
    page.locator("#email-login").fill("maria@exemplo.com")
    page.locator("#senha-login").fill("Senha12345")
    page.get_by_role("button", name="Entrar").last.click()
    expect(page.get_by_role("link", name="Minha conta (Maria)")).to_be_visible()
    expect(page.get_by_role("button", name="Sair")).to_be_visible()
    page.get_by_role("button", name="Sair").click()
    page.wait_for_load_state()
    expect(page.get_by_role("link", name="Entrar", exact=True).first).to_be_visible()
    expect(page.get_by_role("button", name="Sair")).to_have_count(0)
    assert page.evaluate("sessionStorage.length") == 0 and page.evaluate("localStorage.length") == 0


def test_token_never_goes_to_local_storage(page: Page, server: Server) -> None:
    page.goto("/conta.html")
    page.locator("#email-login").fill("maria@exemplo.com")
    page.locator("#senha-login").fill("Senha12345")
    page.get_by_label("Manter conectado nesta aba").check()
    page.get_by_role("button", name="Entrar").last.click()
    expect(page.locator("#conta-logada")).to_be_visible()
    assert page.evaluate("localStorage.length") == 0
    assert page.evaluate("sessionStorage.getItem('ash.token')") == "tok-123"
    page.reload()
    expect(page.locator("#conta-logada")).to_be_visible()  # sessão restaurada na mesma aba
    assert page.evaluate("localStorage.length") == 0


def sign_in(page: Page) -> None:
    page.locator("#email-login").fill("maria@exemplo.com")
    page.locator("#senha-login").fill("Senha12345")
    page.get_by_role("button", name="Entrar").last.click()


def test_signup_warns_that_there_is_no_password_recovery(page: Page, server: Server) -> None:
    """Avaliação de usabilidade (OS-036): quem esquece a senha não tem como recuperá-la."""
    page.goto("/conta.html")
    expect(page.locator("#regras-senha")).to_contain_text("não tem recuperação de senha por e-mail")


def test_keep_signed_in_is_on_by_default_and_the_session_survives_navigation(
    page: Page, server: Server
) -> None:
    """Regressão (OS-036): sem isso, quem entrava era deslogado ao abrir a próxima página."""
    page.goto("/conta.html")
    expect(page.get_by_label("Manter conectado nesta aba")).to_be_checked()
    expect(page.locator("#ajuda-manter")).to_contain_text("entrar de novo ao abrir outra página")
    sign_in(page)
    expect(page.locator("#conta-logada")).to_be_visible()
    assert page.evaluate("localStorage.length") == 0  # nunca em localStorage
    assert page.evaluate("sessionStorage.getItem('ash.token')") == "tok-123"
    page.goto("/privacidade.html")  # navegação completa para outra página
    expect(page.get_by_role("link", name="Minha conta (Maria)")).to_be_visible()


def test_login_that_returns_to_the_previous_page_stays_signed_in(
    page: Page, server: Server
) -> None:
    """O caminho de "Entre para salvar": entrar e voltar à página de origem, ainda logado."""
    page.goto("/conta.html?voltar=%2Fprivacidade.html")
    sign_in(page)
    page.wait_for_url("**/privacidade.html")
    expect(page.get_by_role("link", name="Minha conta (Maria)")).to_be_visible()


def test_signup_keeps_the_session_when_another_page_is_opened(page: Page, server: Server) -> None:
    page.goto("/conta.html")
    fill_signup(page)
    page.get_by_role("button", name="Criar conta").click()
    expect(page.get_by_role("heading", level=1)).to_have_text("Minha conta")
    assert page.evaluate("localStorage.length") == 0
    page.goto("/privacidade.html")
    expect(page.get_by_role("link", name="Minha conta (Maria)")).to_be_visible()


def test_without_keep_signed_in_nothing_is_stored(page: Page, server: Server) -> None:
    page.goto("/conta.html")
    page.get_by_label("Manter conectado nesta aba").uncheck()  # a escolha continua possível
    sign_in(page)
    expect(page.locator("#conta-logada")).to_be_visible()
    assert page.evaluate("sessionStorage.length") == 0 and page.evaluate("localStorage.length") == 0
    page.reload()
    expect(
        page.locator("#conta-visitante")
    ).to_be_visible()  # sem a marca, recarregar exige entrar de novo


def test_login_failure_shows_single_message_in_an_alert(page: Page, server: Server) -> None:
    server.login = lambda body: (401, error("unauthorized", "E-mail ou senha inválidos."))
    page.goto("/conta.html")
    page.locator("#email-login").fill("maria@exemplo.com")
    page.locator("#senha-login").fill("errada12345")
    page.get_by_role("button", name="Entrar").last.click()
    box = page.locator("#erro-login")
    expect(box).to_have_text("Erro: E-mail ou senha inválidos.")
    expect(box).to_have_attribute("role", "alert")
    assert page.evaluate("document.activeElement.id") == "senha-login"


def test_login_rate_limit_message(page: Page, server: Server) -> None:
    server.login = lambda body: (429, error("rate_limited", "Muitas requisições."))
    page.goto("/conta.html")
    page.locator("#email-login").fill("maria@exemplo.com")
    page.locator("#senha-login").fill("Senha12345")
    page.get_by_role("button", name="Entrar").last.click()
    expect(page.locator("#erro-login")).to_contain_text("Muitas tentativas. Aguarde um minuto")


def test_empty_login_fields_are_flagged_without_request(page: Page, server: Server) -> None:
    page.goto("/conta.html")
    page.get_by_role("button", name="Entrar").last.click()
    expect(page.locator("#erro-email-login")).to_have_text("Informe o e-mail.")
    expect(page.locator("#erro-senha-login")).to_have_text("Informe a senha.")
    assert server.posted("/auth/login") == []
    assert page.evaluate("document.activeElement.id") == "email-login"


def test_show_password_toggle(page: Page, server: Server) -> None:
    page.goto("/conta.html")
    field = page.locator("#senha-login")
    button = page.locator("button[data-target=senha-login]")
    expect(field).to_have_attribute("type", "password")
    expect(button).to_have_attribute("aria-pressed", "false")
    button.click()
    expect(field).to_have_attribute("type", "text")
    expect(button).to_have_attribute("aria-pressed", "true")
    button.click()
    expect(field).to_have_attribute("type", "password")


def test_login_return_path_is_followed_only_when_internal(page: Page, server: Server) -> None:
    page.goto("/conta.html?voltar=%2F%3Fq%3Drobotica")
    page.locator("#email-login").fill("maria@exemplo.com")
    page.locator("#senha-login").fill("Senha12345")
    page.get_by_role("button", name="Entrar").last.click()
    page.wait_for_url("**/?q=robotica")


@pytest.mark.parametrize(
    "target",
    ["https%3A%2F%2Fmalicioso.example", "%2F%2Fmalicioso.example", "javascript%3Aalert(1)"],
)
def test_login_ignores_external_return_paths(page: Page, server: Server, target: str) -> None:
    page.goto(f"/conta.html?voltar={target}")
    page.locator("#email-login").fill("maria@exemplo.com")
    page.locator("#senha-login").fill("Senha12345")
    page.get_by_role("button", name="Entrar").last.click()
    expect(page.locator("#conta-logada")).to_be_visible()
    assert page.url.startswith("http://127.0.0.1") and page.url.split("?")[0].endswith(
        "/conta.html"
    )


def test_session_expired_shows_banner_without_losing_the_current_search(
    page: Page, server: Server
) -> None:
    from tests.e2e.test_search_page import SOURCES, record, response_body

    page.add_init_script("sessionStorage.setItem('ash.token', 'expirado')")
    server.me = lambda headers: (200, USER)
    calls = {"n": 0}

    def search(route: Route) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            route.fulfill(status=401, json=error("unauthorized", "Sessão inválida ou expirada."))
        else:
            route.fulfill(status=200, json=response_body([record(1)]))

    page.route("**/api/v1/sources", lambda r: r.fulfill(status=200, json=SOURCES))
    page.route("**/api/v1/search?*", search)
    page.goto("/?q=letramento")
    banner = page.locator("#aviso-sessao")
    expect(banner).to_contain_text("Sessão expirada. Entre novamente")
    expect(banner.locator("[role=alert]")).to_have_count(1)
    assert "voltar=%2F%3Fq%3Dletramento" in banner.get_by_role("link", name="Entrar").get_attribute(
        "href"
    )
    expect(page.get_by_label("Buscar trabalhos")).to_have_value(
        "letramento"
    )  # a busca atual não se perde
    assert page.evaluate("sessionStorage.getItem('ash.token')") is None


def test_privacy_page_renders_markdown_without_executing_html(page: Page, server: Server) -> None:
    page.goto("/privacidade.html")
    expect(page.get_by_role("heading", level=1)).to_have_text("Política de Privacidade")
    assert page.get_by_role("heading", level=1).count() == 1
    expect(page.get_by_role("heading", level=2, name="Quais dados tratamos")).to_be_visible()
    expect(page.locator("#politica strong")).to_have_text("negrito")
    expect(page.locator("#politica em").first).to_have_text("itálico")
    assert page.locator("#politica li").count() == 2
    expect(page.locator("#versao-politica")).to_have_text("Versão 1.0")
    text = page.locator("#politica").inner_text()
    assert "<script>window.__xss=1</script>" in text and "<img src=x" in text
    page.wait_for_timeout(200)
    assert page.evaluate("window.__xss") is None
    assert (
        page.locator("#politica script").count() == 0 and page.locator("#politica img").count() == 0
    )
    assert "{CONTATO_DO_RESPONSAVEL}" in text
    assert page.probe.errors == []  # type: ignore[attr-defined]


def test_privacy_page_shows_error_when_policy_cannot_be_loaded(page: Page) -> None:
    page.route(
        "**/api/v1/privacy",
        lambda r: r.fulfill(status=500, json=error("internal_error", "Erro interno.")),
    )
    page.goto("/privacidade.html")
    expect(page.locator("#politica .alert-error")).to_contain_text("Erro interno.")


def test_footer_links_to_privacy_page(page: Page, server: Server) -> None:
    page.goto("/")
    expect(
        page.locator("footer").get_by_role("link", name="Política de privacidade")
    ).to_have_attribute("href", "privacidade.html")


def test_forms_have_no_horizontal_scroll_on_small_screens(page: Page, server: Server) -> None:
    page.set_viewport_size({"width": 320, "height": 800})
    page.goto("/conta.html")
    assert page.evaluate("document.documentElement.scrollWidth") <= 320
