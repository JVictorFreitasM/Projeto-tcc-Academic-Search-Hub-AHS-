"""Varredura de escopo (OS-035): nada fora do escopo do TCC nem fora da stack fechada.

Fora do escopo (seção 3 das OS): aplicativo móvel, recomendação, alertas, integração direta com
gerenciadores de referências, outros repositórios por tela/rota, outros idiomas, 2FA, Redis,
Celery/filas, frameworks JavaScript, bundlers, Docker como requisito, serviço de e-mail, painel de
estatísticas, modo escuro e MARCXML. Este teste olha dependências, importações, configuração,
rotas, tabelas e arquivos. Se um dia algo daqui for ampliado de propósito, o teste deve mudar junto
com `docs/DECISOES.md`.
"""

from __future__ import annotations

import ast
import os
import re
import tomllib
from pathlib import Path

import pytest

from app.core.config import Settings
from app.db.base import Base
from app.main import create_app

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]

# Seção 4 das OS (+ as duas adições permitidas: pyyaml e a biblioteca de HTML, beautifulsoup4).
RUNTIME_ALLOWED = {
    "fastapi", "uvicorn", "sqlalchemy", "alembic", "psycopg", "pydantic", "pydantic-settings",
    "httpx", "defusedxml", "argon2-cffi", "pyjwt", "slowapi", "pyyaml", "beautifulsoup4",
}  # fmt: skip
# Desenvolvimento: testes, qualidade, segurança, interface; os "types-*" são só as dicas de tipo
# que o mypy estrito pede para pyyaml e defusedxml.
DEV_ALLOWED = {
    "pytest", "pytest-asyncio", "respx", "pytest-cov", "ruff", "mypy", "bandit", "pip-audit",
    "playwright", "axe-playwright-python", "types-pyyaml", "types-defusedxml",
}  # fmt: skip
FORBIDDEN_MODULES = {
    "redis", "celery", "kombu", "rq", "dramatiq",  # fila e cache
    "smtplib", "aiosmtplib", "sendgrid", "yagmail",  # e-mail
    "pyotp", "onetimepass",  # 2FA
    "babel", "gettext",  # outros idiomas
    "pymarc",  # MARCXML
    "pyzotero", "docker",  # gerenciadores de referências, Docker
    "sklearn", "surprise", "implicit",  # recomendação
}  # fmt: skip
EXPECTED_TABLES = {
    "users", "favorites", "search_history", "oai_records", "harvest_runs", "security_events",
}  # fmt: skip
FORBIDDEN_ROUTE_WORDS = (
    "recommend", "alert", "notif", "zotero", "mendeley", "dashboard", "statistic", "estatist",
    "2fa", "totp", "mfa", "otp", "locale", "i18n", "admin", "language",
)  # fmt: skip
FORBIDDEN_SETTING_WORDS = ("smtp", "redis", "celery", "broker", "totp", "otp", "mail_", "queue")
SKIP_DIRS = {
    ".venv",
    ".git",
    "node_modules",
    "htmlcov",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}


def dependency_names(specs: list[str]) -> set[str]:
    names = set()
    for spec in specs:
        match = re.match(r"[A-Za-z0-9_.\-]+", spec)
        assert match, spec
        names.add(match.group(0).lower().replace("_", "-").replace(".", "-"))
    return names


@pytest.fixture(scope="module")
def pyproject() -> dict[str, object]:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_runtime_dependencies_are_exactly_the_closed_stack(pyproject: dict[str, object]) -> None:
    declared = dependency_names(pyproject["project"]["dependencies"])  # type: ignore[index]
    assert declared <= RUNTIME_ALLOWED, f"dependência fora da stack: {declared - RUNTIME_ALLOWED}"


def test_dev_dependencies_are_only_the_allowed_tools(pyproject: dict[str, object]) -> None:
    declared = dependency_names(pyproject["dependency-groups"]["dev"])  # type: ignore[index]
    assert declared <= DEV_ALLOWED, f"ferramenta fora da lista: {declared - DEV_ALLOWED}"


def test_no_forbidden_package_is_installed_even_indirectly() -> None:
    lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
    locked = set(re.findall(r'^name = "([^"]+)"', lock, re.MULTILINE))
    banned = {"redis", "celery", "kombu", "pymarc", "pyotp", "babel", "docker", "pyzotero"}
    assert not (locked & banned), locked & banned


def python_files() -> list[Path]:
    return [p for folder in ("app", "migrations", "scripts") for p in (ROOT / folder).rglob("*.py")]


def test_no_python_code_imports_a_forbidden_module() -> None:
    offenders = []
    for path in python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module]
            offenders += [
                f"{path.relative_to(ROOT)}: {m}"
                for m in modules
                if m.split(".")[0] in FORBIDDEN_MODULES
            ]
    assert offenders == []


def test_settings_have_no_mail_queue_or_second_factor_options() -> None:
    names = [name.lower() for name in Settings.model_fields]
    offenders = [n for n in names if any(word in n for word in FORBIDDEN_SETTING_WORDS)]
    assert offenders == []


def test_api_has_no_out_of_scope_routes_and_no_way_to_add_sources() -> None:
    schema = create_app(Settings(_env_file=None)).openapi()  # type: ignore[call-arg]
    paths = list(schema["paths"])
    offenders = [p for p in paths if any(w in p.lower() for w in FORBIDDEN_ROUTE_WORDS)]
    assert offenders == []
    # fontes novas só por edição de config/oai_sources.yml: a rota de fontes só lê
    assert set(schema["paths"]["/api/v1/sources"]) == {"get"}


def test_database_has_only_the_expected_tables() -> None:
    import app.models  # noqa: F401  (registra as tabelas)

    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_there_is_no_docker_or_javascript_toolchain_in_the_repository() -> None:
    forbidden = re.compile(
        r"^(Dockerfile.*|docker-compose.*|\.dockerignore|package(-lock)?\.json|yarn\.lock|"
        r"pnpm-lock\.yaml|webpack\.config\..*|vite\.config\..*|tsconfig.*\.json|.*\.tsx?)$"
    )
    found = []
    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        found += [str(Path(folder, f).relative_to(ROOT)) for f in files if forbidden.match(f)]
    assert found == []


def test_frontend_is_native_modules_with_no_external_code_and_no_dark_mode() -> None:
    frontend = ROOT / "frontend"
    for path in frontend.rglob("*"):
        if path.suffix not in {".js", ".html", ".css"}:
            continue
        content = path.read_text(encoding="utf-8")
        assert not re.search(r"https?://", content), f"endereço externo em {path.name}"
        assert "prefers-color-scheme" not in content, f"modo escuro em {path.name}"
        if path.suffix == ".js":
            targets = (
                re.findall(r"""\bfrom\s+["']([^"']+)["']""", content)  # import x from "y"
                + re.findall(r"""\bimport\s*\(\s*["']([^"']+)["']""", content)  # import("y")
                + re.findall(r"""^\s*import\s+["']([^"']+)["']""", content, re.MULTILINE)
            )
            for target in targets:
                assert target.startswith("./"), f"{path.name} importa {target}"
        if path.suffix == ".html":
            for src in re.findall(r"""<script[^>]*\ssrc=["']([^"']+)["']""", content):
                assert src.startswith("js/"), f"{path.name} carrega {src}"
