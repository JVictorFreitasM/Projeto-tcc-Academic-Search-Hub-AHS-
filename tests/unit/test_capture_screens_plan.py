"""O plano de capturas do TCC (OS-032): lista completa, nomes únicos e dados só de demonstração."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SLUGS = [
    "busca-vazia",
    "resultados",
    "erro-parcial",
    "sem-resultados",
    "filtros-abertos",
    "filtros-ativos",
    "favoritos",
    "anotacao",
    "exportar",
    "historico",
    "cadastro",
    "login",
    "minha-conta",
    "excluir-conta",
    "politica-privacidade",
    "api-docs",
]


@pytest.fixture(scope="module")
def script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "capture_screens", ROOT / "scripts" / "capture_screens.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["capture_screens"] = module
    spec.loader.exec_module(module)
    return module


def test_every_screen_listed_by_the_os_is_planned_in_order(script: ModuleType) -> None:
    assert [s.slug for s in script.SCREENS] == EXPECTED_SLUGS


def test_file_names_are_numbered_unique_and_cover_both_widths(script: ModuleType) -> None:
    names = [
        script.filename(i, screen, device)
        for i, screen in enumerate(script.SCREENS, start=1)
        for device in script.DEVICES
    ]
    assert len(names) == len(set(names)) == 2 * len(EXPECTED_SLUGS)
    assert names[0] == "4.1-01-busca-vazia-computador.png"
    assert names[1] == "4.1-01-busca-vazia-celular.png"
    assert set(script.DEVICES) == {"computador", "celular"}


def test_every_screen_maps_to_a_tcc_section_and_describes_itself(script: ModuleType) -> None:
    for screen in script.SCREENS:
        assert screen.section.startswith("4.") and screen.title and screen.shows


def test_demo_records_are_clearly_marked_and_fictitious(script: ModuleType) -> None:
    records = script.demo_records()
    assert len(records) == 4
    for rec in records:
        assert rec["title"].startswith("[DEMONSTRAÇÃO]")
        assert rec["authors"][0]["name"] == "Autora Fictícia"
    assert script.DEMO_EMAIL.endswith("@example.org")  # domínio reservado: nunca é pessoa real
