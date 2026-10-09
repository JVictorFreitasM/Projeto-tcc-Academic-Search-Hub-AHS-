import json

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.fake_api import FakeApi, record

pytestmark = pytest.mark.e2e


@pytest.fixture
def api(page: Page) -> FakeApi:
    return FakeApi(page, logged_in=True)


def open_account(page: Page) -> None:
    page.goto("/conta.html")
    expect(page.get_by_role("heading", level=1)).to_have_text("Minha conta")
    expect(page.get_by_role("heading", level=2, name="Dados da conta")).to_be_visible()


def test_account_data_is_shown(page: Page, api: FakeApi) -> None:
    open_account(page)
    area = page.locator("#conta-logada")
    expect(area).to_contain_text("Maria de Souza")
    expect(area).to_contain_text("maria@exemplo.com")
    expect(area).to_contain_text("política versão 1.0")
    assert "hash" not in area.inner_text().lower() and "argon" not in area.inner_text().lower()
    assert page.probe.errors == []  # type: ignore[attr-defined]


def test_every_article_18_right_has_a_working_control(page: Page, api: FakeApi) -> None:
    open_account(page)
    headings = [h.strip() for h in page.locator("#conta-logada h2").all_inner_texts()]
    assert headings == [
        "Dados da conta",  # acesso
        "Corrigir dados",  # correção
        "Trocar senha",
        "Baixar meus dados",  # portabilidade
        "Excluir minha conta",  # eliminação
    ]
    for name in ("Salvar alterações", "Trocar senha", "Baixar meus dados", "Excluir minha conta"):
        expect(page.get_by_role("button", name=name, exact=True)).to_be_enabled()


def test_edit_name_updates_summary_and_header(page: Page, api: FakeApi) -> None:
    page.set_viewport_size({"width": 1280, "height": 900})
    open_account(page)
    page.locator("#conta-nome").fill("Ana Clara Lima")
    page.get_by_role("button", name="Salvar alterações").click()
    expect(page.locator("#conta-logada dl")).to_contain_text("Ana Clara Lima")
    expect(page.get_by_role("link", name="Minha conta (Ana)")).to_be_visible()
    patch = api.calls_to("PATCH", "/me")[0]
    assert patch["body"] == {"full_name": "Ana Clara Lima"}  # sem e-mail, sem senha


def test_changing_email_requires_the_current_password(page: Page, api: FakeApi) -> None:
    open_account(page)
    page.locator("#conta-email").fill("novo@exemplo.com")
    page.get_by_role("button", name="Salvar alterações").click()
    expect(page.locator("#erro-conta-senha-email")).to_have_text(
        "Informe a senha atual para trocar o e-mail."
    )
    expect(page.locator("#conta-senha-email")).to_have_attribute("aria-invalid", "true")
    assert api.calls_to("PATCH", "/me") == []

    page.locator("#conta-senha-email").fill("SenhaErrada99")
    page.get_by_role("button", name="Salvar alterações").click()
    expect(page.locator("#erro-conta-senha-email")).to_have_text("Senha atual incorreta.")

    page.locator("#conta-senha-email").fill("Senha12345")
    page.get_by_role("button", name="Salvar alterações").click()
    expect(page.locator("#conta-logada dl")).to_contain_text("novo@exemplo.com")
    last = api.calls_to("PATCH", "/me")[-1]["body"]
    assert last["email"] == "novo@exemplo.com" and last["current_password"] == "Senha12345"


def test_taken_email_shows_generic_message(page: Page, api: FakeApi) -> None:
    open_account(page)
    page.locator("#conta-email").fill("ocupado@exemplo.com")
    page.locator("#conta-senha-email").fill("Senha12345")
    page.get_by_role("button", name="Salvar alterações").click()
    alert = page.locator("#conta-logada .alert-error").first
    expect(alert).to_have_text("Erro: Não foi possível atualizar os dados.")
    assert "ocupado" not in alert.inner_text()


def test_invalid_profile_fields_are_flagged(page: Page, api: FakeApi) -> None:
    open_account(page)
    page.locator("#conta-nome").fill("A")
    page.locator("#conta-email").fill("sem-arroba")
    page.get_by_role("button", name="Salvar alterações").click()
    expect(page.locator("#erro-conta-nome")).to_have_text("Informe o nome completo.")
    expect(page.locator("#erro-conta-email")).to_have_text("Informe um e-mail válido.")
    assert page.evaluate("document.activeElement.id") == "conta-nome"
    assert api.calls_to("PATCH", "/me") == []


def test_change_password_flow(page: Page, api: FakeApi) -> None:
    open_account(page)
    page.get_by_role("button", name="Trocar senha", exact=True).click()
    expect(page.locator("#erro-senha-atual")).to_have_text("Informe a senha atual.")
    page.locator("#senha-atual").fill("Senha12345")
    page.locator("#senha-nova").fill("curta1")
    page.get_by_role("button", name="Trocar senha", exact=True).click()
    expect(page.locator("#erro-senha-nova")).to_contain_text("ao menos 10")
    page.locator("#senha-atual").fill("Errada123456")
    page.locator("#senha-nova").fill("NovaSenha789")
    page.get_by_role("button", name="Trocar senha", exact=True).click()
    expect(page.locator("#erro-senha-atual")).to_have_text("Senha atual incorreta.")
    page.locator("#senha-atual").fill("Senha12345")
    page.get_by_role("button", name="Trocar senha", exact=True).click()
    expect(page.locator("#conta-logada .alert-success")).to_have_text("Senha alterada com sucesso.")
    expect(page.locator("#senha-atual")).to_have_value("")
    assert api.password == "NovaSenha789"
    assert page.locator("#senha-atual").get_attribute("autocomplete") == "current-password"
    assert page.locator("#senha-nova").get_attribute("autocomplete") == "new-password"


def test_download_my_data(page: Page, api: FakeApi) -> None:
    api.add_favorite(record(1), "minha nota")
    api.add_history("educação")
    open_account(page)
    with page.expect_download() as info:
        page.get_by_role("button", name="Baixar meus dados").click()
    download = info.value
    assert download.suggested_filename == "meus-dados-20261009.json"
    with open(download.path(), encoding="utf-8") as handle:
        data = json.load(handle)
    assert data["account"]["email"] == "maria@exemplo.com"
    assert (
        data["favorites"][0]["note"] == "minha nota"
        and data["search_history"][0]["query"] == "educação"
    )
    expect(page.locator("#conta-logada")).to_contain_text(
        "Arquivo meus-dados-20261009.json gerado."
    )


def test_delete_account_requires_password_and_confirms(page: Page, api: FakeApi) -> None:
    api.add_favorite(record(1))
    open_account(page)
    page.get_by_role("button", name="Excluir minha conta").click()
    dialog = page.get_by_role("dialog", name="Excluir a conta?")
    expect(dialog).to_be_visible()
    for line in ("dados de cadastro", "favoritos e anotações", "histórico de buscas"):
        expect(dialog).to_contain_text(line)
    expect(dialog.get_by_label("Digite sua senha para confirmar")).to_be_focused()

    dialog.get_by_role("button", name="Excluir definitivamente").click()
    expect(dialog.get_by_role("alert")).to_have_text("Informe a senha para confirmar.")
    dialog.get_by_label("Digite sua senha para confirmar").fill("Errada123456")
    dialog.get_by_role("button", name="Excluir definitivamente").click()
    expect(dialog.get_by_role("alert")).to_have_text("Senha incorreta.")
    expect(dialog).to_be_visible()  # continua aberto
    assert api.deleted is False

    dialog.get_by_role("button", name="Cancelar").click()
    assert api.deleted is False
    expect(page.get_by_role("button", name="Excluir minha conta")).to_be_focused()

    page.get_by_role("button", name="Excluir minha conta").click()
    page.get_by_role("dialog").get_by_label("Digite sua senha para confirmar").fill("Senha12345")
    page.get_by_role("dialog").get_by_role("button", name="Excluir definitivamente").click()
    page.wait_for_url("**/index.html?conta_excluida=1")
    expect(page.locator(".alert-success")).to_contain_text("Conta excluída.")
    assert api.deleted is True
    assert page.evaluate("sessionStorage.length") == 0
    delete = api.calls_to("DELETE", "/me")[-1]
    assert delete["body"] == {"password": "Senha12345"}
    expect(page.get_by_role("link", name="Entrar", exact=True).first).to_be_visible()
    assert "conta_excluida" not in page.url


def test_login_with_new_policy_version_asks_for_acceptance(page: Page) -> None:
    api = FakeApi(page, logged_in=False)
    api.login_consent_required = True
    api.policy_version = "2.0"
    page.goto("/conta.html?voltar=%2Ffavoritos.html")
    page.locator("#email-login").fill("maria@exemplo.com")
    page.locator("#senha-login").fill("Senha12345")
    page.get_by_role("button", name="Entrar").last.click()
    heading = page.get_by_role("heading", level=2, name="Nova versão da Política de Privacidade")
    expect(heading).to_be_visible()  # não segue para o destino enquanto não aceitar
    assert page.url.endswith("/conta.html?voltar=%2Ffavoritos.html")
    expect(page.get_by_role("link", name="Ler a política")).to_have_attribute(
        "href", "privacidade.html"
    )
    expect(page.get_by_role("heading", level=2, name="Dados da conta")).to_have_count(0)

    page.get_by_role("button", name="Aceitar e continuar").click()
    expect(page.locator("#erro-aceite-nova-politica")).to_have_text(
        "Marque a caixa para aceitar a nova versão e continuar."
    )
    assert api.calls_to("POST", "/me/consent") == []
    page.get_by_label("Li e aceito a nova versão").check()
    page.get_by_role("button", name="Aceitar e continuar").click()
    expect(page.get_by_role("heading", level=2, name="Dados da conta")).to_be_visible()
    expect(page.locator("#conta-logada")).to_contain_text("política versão 2.0")
    assert len(api.calls_to("POST", "/me/consent")) == 1


def test_returning_user_with_old_consent_is_asked_on_account_page(page: Page, api: FakeApi) -> None:
    api.policy_version = "3.0"
    page.goto("/conta.html")
    expect(
        page.get_by_role("heading", level=2, name="Nova versão da Política de Privacidade")
    ).to_be_visible()
    expect(page.locator("#conta-logada")).to_contain_text("versão 3.0")


def test_account_page_has_no_horizontal_scroll_and_labelled_fields(
    page: Page, api: FakeApi
) -> None:
    page.set_viewport_size({"width": 320, "height": 800})
    open_account(page)
    assert page.evaluate("document.documentElement.scrollWidth") <= 320
    unlabeled = page.evaluate(
        "[...document.querySelectorAll('#conta-logada input')].filter(i => !i.labels.length).map(i => i.id)"
    )
    assert unlabeled == []
    for field_id, autocomplete in (
        ("conta-nome", "name"),
        ("conta-email", "email"),
        ("conta-senha-email", "current-password"),
    ):
        assert page.locator(f"#{field_id}").get_attribute("autocomplete") == autocomplete


def test_header_logout_from_account_page_returns_to_forms(page: Page, api: FakeApi) -> None:
    page.set_viewport_size({"width": 1280, "height": 900})
    open_account(page)
    page.get_by_role("button", name="Sair").click()
    expect(page.get_by_role("heading", level=1)).to_have_text("Entrar ou criar conta")
    expect(page.locator("#conta-visitante")).to_be_visible()
