"""docs/API.md acompanha o OpenAPI da aplicação (OS-034): nenhuma rota fica sem documentação."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "check_api_docs", ROOT / "scripts" / "check_api_docs.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_api_docs"] = module
    spec.loader.exec_module(module)
    return module


def test_every_openapi_route_is_documented_and_self_assessed(
    checker: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    assert checker.main() == 0, capsys.readouterr().err
    assert "operações do OpenAPI estão documentadas" in capsys.readouterr().out


def test_operations_are_listed_as_method_and_path(checker: ModuleType) -> None:
    schema = {"paths": {"/a": {"get": {}, "post": {}, "parameters": []}, "/b/{id}": {"delete": {}}}}
    assert checker.openapi_operations(schema) == ["DELETE /b/{id}", "GET /a", "POST /a"]


def test_a_missing_route_is_reported_per_section(checker: ModuleType) -> None:
    doc = "## Rotas\n`GET /a` e `POST /a`\n## Conformidade REST\n| `GET /a` |\n"
    missing = checker.missing_routes(["GET /a", "POST /a"], doc)
    assert missing == {"Rotas": [], "Conformidade REST": ["POST /a"]}


def test_a_route_only_in_the_rest_table_is_still_missing_from_routes(checker: ModuleType) -> None:
    doc = "## Rotas\nnada\n## Conformidade REST\n| `GET /a` |\n"
    assert checker.missing_routes(["GET /a"], doc)["Rotas"] == ["GET /a"]


@pytest.mark.parametrize(
    "doc",
    ["sem seções", "## Conformidade REST\n## Rotas\n", "## Rotas\nsó isso"],
)
def test_a_document_without_the_two_sections_in_order_is_rejected(
    checker: ModuleType, doc: str
) -> None:
    with pytest.raises(ValueError, match=r"seç(ão|ões)"):
        checker.missing_routes(["GET /a"], doc)


def test_main_fails_when_the_doc_lacks_a_route(
    checker: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    text = (ROOT / "docs" / "API.md").read_text(encoding="utf-8")
    partial = tmp_path / "API.md"
    partial.write_text(
        text.replace("POST /api/v1/export", "POST /api/v1/EXPORTAR"), encoding="utf-8"
    )
    monkeypatch.setattr(checker, "API_DOC", partial)
    assert checker.main() == 1
    assert "falta na seção" in capsys.readouterr().err
