"""Varreduras de higiene de código ligadas aos riscos do OWASP Top 10 (2017). Veja docs/SEGURANCA.md."""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app"
FRONTEND = ROOT / "frontend"
PY_FILES = sorted(APP.rglob("*.py"))
JS_FILES = sorted((FRONTEND / "js").glob("*.js"))
HTML_FILES = sorted(FRONTEND.glob("*.html"))


def parse(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def is_dynamic_string(node: ast.expr) -> bool:
    """f-string, concatenação/formatação de texto ou .format(): SQL montado com texto variável."""
    if isinstance(node, ast.JoinedStr):
        return any(isinstance(part, ast.FormattedValue) for part in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add | ast.Mod):
        return True
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "format"
    )


def test_python_files_were_found() -> None:
    assert len(PY_FILES) > 30


# ---------- A1 Injeção ----------


@pytest.mark.parametrize("path", PY_FILES, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_a1_sql_is_never_built_from_dynamic_strings(path: Path) -> None:
    offenders = []
    for node in ast.walk(parse(path)):
        is_sql_call = isinstance(node, ast.Call) and call_name(node) in {
            "text",
            "execute",
            "exec_driver_sql",
        }
        if is_sql_call and node.args and is_dynamic_string(node.args[0]):  # type: ignore[attr-defined]
            offenders.append(f"{path.name}:{node.lineno}")  # type: ignore[attr-defined]
    assert offenders == [], f"SQL montado com texto variável: {offenders}"


# ---------- A4 XXE ----------

FORBIDDEN_XML = ("xml.etree", "xml.dom", "xml.sax", "xml.parsers", "lxml", "xmlrpc")


@pytest.mark.parametrize("path", PY_FILES, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_a4_xml_is_only_parsed_with_defusedxml(path: Path) -> None:
    for node in ast.walk(parse(path)):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        for name in names:
            assert not name.startswith(FORBIDDEN_XML), f"{path.name}:{node.lineno} importa {name}"


def test_a4_the_oai_client_uses_defusedxml_with_dtd_forbidden() -> None:
    source = (APP / "harvest" / "oai_client.py").read_text(encoding="utf-8")
    assert "from defusedxml.ElementTree import" in source
    assert "forbid_dtd=True" in source


# ---------- A8 Desserialização insegura ----------

FORBIDDEN_MODULES = {"pickle", "cPickle", "marshal", "shelve", "dill", "jsonpickle", "cloudpickle"}
FORBIDDEN_CALLS = {"eval", "exec", "unsafe_load", "full_load", "load_all", "unsafe_load_all"}


@pytest.mark.parametrize("path", PY_FILES, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_a8_no_unsafe_deserialization_or_dynamic_execution(path: Path) -> None:
    offenders = []
    for node in ast.walk(parse(path)):
        if isinstance(node, ast.Import):
            offenders += [a.name for a in node.names if a.name.split(".")[0] in FORBIDDEN_MODULES]
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] in FORBIDDEN_MODULES:
                offenders.append(node.module)
        elif isinstance(node, ast.Call):
            name = call_name(node)
            if name in FORBIDDEN_CALLS:
                offenders.append(f"{name}() em {path.name}:{node.lineno}")
            if name == "load" and isinstance(node.func, ast.Attribute):
                owner = node.func.value
                if isinstance(owner, ast.Name) and owner.id == "yaml":
                    offenders.append(f"yaml.load() em {path.name}:{node.lineno}")
    assert offenders == []


def test_a8_yaml_is_read_with_safe_load() -> None:
    source = (APP / "harvest" / "oai_sources.py").read_text(encoding="utf-8")
    assert "yaml.safe_load" in source


# ---------- A7 XSS no frontend ----------

DANGEROUS_JS = re.compile(
    r"\.innerHTML\b|\.outerHTML\b|insertAdjacentHTML|document\.write\s*\(|\beval\s*\(|new\s+Function\s*\(|"
    r"setTimeout\s*\(\s*[\"'`]|setInterval\s*\(\s*[\"'`]|\.srcdoc\b|createContextualFragment"
)


def test_a7_frontend_files_were_found() -> None:
    assert len(JS_FILES) >= 15 and len(HTML_FILES) >= 4


@pytest.mark.parametrize("path", JS_FILES, ids=lambda p: p.name)
def test_a7_no_html_injection_apis_in_javascript(path: Path) -> None:
    offenders = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        code = line.split("//", 1)[0]
        if DANGEROUS_JS.search(code):
            offenders.append(f"{path.name}:{number}: {line.strip()}")
    assert offenders == [], (
        "APIs que interpretam HTML (permitido só com literal constante e comentário)"
    )


@pytest.mark.parametrize("path", HTML_FILES, ids=lambda p: p.name)
def test_a7_html_has_no_inline_script_style_or_handlers(path: Path) -> None:
    html = path.read_text(encoding="utf-8")
    assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>\s*\S", html), "script embutido"
    assert not re.search(r"\sstyle\s*=", html), "atributo style"
    assert not re.search(r"<style\b", html), "bloco <style>"
    assert not re.search(r"\son[a-z]+\s*=", html, re.IGNORECASE), (
        "manipulador de evento em atributo"
    )
    assert "javascript:" not in html.lower()
    assert not re.search(r"(?:src|href)=[\"']https?://", html), "recurso externo (CDN)"


@pytest.mark.parametrize("path", sorted((FRONTEND / "css").glob("*.css")), ids=lambda p: p.name)
def test_a7_css_loads_no_external_resources(path: Path) -> None:
    css = path.read_text(encoding="utf-8")
    assert "@import" not in css
    assert not re.search(r"url\(\s*[\"']?https?:", css)


def test_a7_token_is_never_stored_in_local_storage() -> None:
    for path in JS_FILES:
        code = "\n".join(
            line.split("//", 1)[0] for line in path.read_text(encoding="utf-8").splitlines()
        )
        assert "localStorage" not in code, path.name  # só sessionStorage (e só em state.js)


# ---------- A3 / A6 Segredos e configuração ----------

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(
        r"(?i)(?:api[_-]?key|secret[_-]?key|password|token)\s*[:=]\s*[\"'][A-Za-z0-9/+_\-]{16,}[\"']"
    ),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
]


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return [ROOT / line for line in result.stdout.splitlines() if line]


def test_a3_env_is_ignored_and_not_tracked() -> None:
    assert ".env" in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    tracked = {p.relative_to(ROOT).as_posix() for p in tracked_files()}
    assert ".env" not in tracked and ".env.example" in tracked


def test_a3_env_example_has_no_real_values_for_secrets() -> None:
    values = {}
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key] = value
    for key in ("SECRET_KEY", "OPENALEX_API_KEY", "CORE_API_KEY", "CONTACT_EMAIL"):
        assert values[key] == "", key
    assert "pass@" in values["DATABASE_URL"]  # exemplo genérico, não uma senha real


def test_a3_no_secrets_in_tracked_application_files() -> None:
    offenders = []
    for path in tracked_files():
        relative = path.relative_to(ROOT).as_posix()
        if not relative.startswith(("app/", "frontend/", "config/", "scripts/", "migrations/")):
            continue
        if path.suffix not in {
            ".py",
            ".js",
            ".html",
            ".css",
            ".yml",
            ".yaml",
            ".md",
            ".ini",
            ".json",
        }:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                if "AcademicSearchHub" in match.group(0):  # nome público do agente em robots.txt
                    continue
                offenders.append(f"{relative}: {pattern.pattern[:30]}")
    assert offenders == []


def test_a6_application_never_enables_debug() -> None:
    for path in PY_FILES:
        for node in ast.walk(parse(path)):
            if isinstance(node, ast.keyword) and node.arg == "debug":
                assert not (isinstance(node.value, ast.Constant) and node.value.value is True), (
                    path.name
                )
    run_source = (APP / "run.py").read_text(encoding="utf-8")
    assert "reload=True" not in run_source


def test_a6_cors_never_uses_wildcard_literal() -> None:
    source = (APP / "main.py").read_text(encoding="utf-8")
    assert 'allow_origins=["*"]' not in source and "allow_origins=['*']" not in source
