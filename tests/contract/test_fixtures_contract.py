"""Contrato dos conectores: as fixtures (reais ou sintéticas) produzem `RecordOut` válidos.

Com `STRICT_FIXTURES=1` o teste `test_no_synthetic_fixture_left` falha e LISTA as fixtures
sintéticas que ainda precisam ser trocadas por respostas reais do desenvolvedor.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from defusedxml.ElementTree import fromstring

from app.connectors.core_api import work_to_record as core_record
from app.connectors.openalex import work_to_record as openalex_record
from app.harvest.mapping import parse_oai_dc
from app.harvest.oai_client import OAI_NS, parse_record_element
from app.harvest.oai_sources import OaiSourceConfig
from app.schemas.common import RecordType
from app.schemas.record import RecordOut

pytestmark = pytest.mark.contract

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SYNTHETIC_XML_MARK = "SINTÉTICA"
OAI_RECORD_FILES = sorted(
    p
    for p in (FIXTURES / "oai").rglob("*.xml")
    if p.name.startswith("list_records") or p.name == "deleted_record.xml"
)


def load_json(path: Path) -> dict:  # type: ignore[type-arg]
    return json.loads(path.read_text(encoding="utf-8"))


def synthetic_fixtures() -> list[str]:
    """Fixtures de fonte ainda sintéticas (JSON com `_synthetic` ou XML com o comentário)."""
    found: list[str] = []
    for folder in ("openalex", "core"):
        for path in sorted((FIXTURES / folder).glob("*.json")):
            data = load_json(path)
            # `_permanent`: casos de borda sintéticos que ficam de propósito (não são pendência)
            if data.get("_synthetic") is True and data.get("_permanent") is not True:
                found.append(path.relative_to(FIXTURES).as_posix())
    for path in sorted((FIXTURES / "oai").rglob("*.xml")):
        if SYNTHETIC_XML_MARK in path.read_text(encoding="utf-8"):
            found.append(path.relative_to(FIXTURES).as_posix())
    return found


def test_openalex_fixtures_produce_valid_records() -> None:
    files = sorted((FIXTURES / "openalex").glob("*.json"))
    assert files, "nenhuma fixture do OpenAlex"
    for path in files:
        records = [openalex_record(w) for w in load_json(path)["results"]]
        valid = [r for r in records if r is not None]
        assert valid and all(isinstance(r, RecordOut) for r in valid), path.name


def test_core_fixtures_produce_valid_records() -> None:
    files = sorted((FIXTURES / "core").glob("*.json"))
    assert files, "nenhuma fixture do CORE"
    for path in files:
        records = [core_record(w) for w in load_json(path)["results"]]
        valid = [r for r in records if r is not None]
        assert valid and all(isinstance(r, RecordOut) for r in valid), path.name


@pytest.mark.parametrize("path", OAI_RECORD_FILES, ids=lambda p: p.relative_to(FIXTURES).as_posix())
def test_oai_fixtures_produce_valid_rows(path: Path) -> None:
    source = OaiSourceConfig(
        slug="contrato", name="Contrato", base_url="https://oai.exemplo.org/oai",
        default_type=RecordType.OTHER,
    )  # fmt: skip
    root = fromstring(path.read_bytes(), forbid_dtd=True)
    elements = root.findall(f".//{OAI_NS}record")
    assert elements, f"{path.name} sem registros"
    for element in elements:
        raw = parse_record_element(element)
        assert raw is not None and raw.identifier
        if raw.deleted:
            assert raw.dc is None
            continue
        row = parse_oai_dc(raw, source)
        if row is None:  # registro sem título é ignorado de propósito (conta como "ignorado")
            continue
        assert row["title"] and row["type"] in {t.value for t in RecordType}
        assert row["source"] == "contrato" and row["oai_identifier"] == raw.identifier


def test_every_synthetic_fixture_is_marked_as_such() -> None:
    """Fixture sintética sem marca passaria por real: o marcador é obrigatório."""
    for path in sorted((FIXTURES / "oai" / "synthetic").glob("*.xml")):
        assert SYNTHETIC_XML_MARK in path.read_text(encoding="utf-8"), path.name
    for folder in ("openalex", "core"):
        for path in (FIXTURES / folder).glob("*.json"):
            data = load_json(path)
            if "_synthetic" in data:
                assert data["_synthetic"] is True, path.name


def test_synthetic_fixtures_are_discoverable() -> None:
    found = synthetic_fixtures()
    # OpenAlex e CORE já têm resposta real; só as fixtures de OAI ainda são sintéticas
    assert found and all(name.startswith("oai/synthetic/") for name in found), found


@pytest.mark.parametrize("folder", ["openalex", "core"])
def test_main_api_fixtures_are_real_and_the_edge_cases_are_not_a_pending_item(folder: str) -> None:
    """As respostas reais (OpenAlex em 14/10 e CORE em 15/10/2026) saíram da lista de pendentes."""
    found = synthetic_fixtures()
    assert f"{folder}/search_ok.json" not in found
    assert f"{folder}/edge_cases.json" not in found  # sintética permanente, de propósito
    assert "_synthetic" not in load_json(FIXTURES / folder / "search_ok.json")
    edge = load_json(FIXTURES / folder / "edge_cases.json")
    assert edge["_synthetic"] is True and edge["_permanent"] is True


@pytest.mark.skipif(os.environ.get("STRICT_FIXTURES") != "1", reason="defina STRICT_FIXTURES=1")
def test_no_synthetic_fixture_left() -> None:
    found = synthetic_fixtures()
    assert not found, (
        "Fixtures sintéticas pendentes de troca por respostas reais:\n  " + "\n  ".join(found)
    )
