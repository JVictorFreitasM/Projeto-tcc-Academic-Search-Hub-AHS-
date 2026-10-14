"""O pacote de evidências (OS-035) só aponta para arquivos que existem."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs" / "evidencias" / "PACOTE.md"
PATH_IN_BACKTICKS = re.compile(r"`((?:docs|tests|scripts|app|deploy|config)/[^`\s]+)`")


def referenced_paths(text: str) -> list[str]:
    return sorted(set(PATH_IN_BACKTICKS.findall(text)))


def test_every_file_cited_in_the_package_exists() -> None:
    paths = referenced_paths(PACKAGE.read_text(encoding="utf-8"))
    assert len(paths) >= 40  # o pacote cita bastante coisa; não pode ter virado vazio
    missing = [p for p in paths if not (ROOT / p.rstrip("/")).exists()]
    assert missing == [], f"o pacote cita arquivos que não existem: {missing}"


def test_the_package_covers_sections_4_1_to_4_6_and_the_pending_items() -> None:
    text = PACKAGE.read_text(encoding="utf-8")
    for section in ("## 4.1", "## 4.2", "## 4.3", "## 4.4", "## 4.5", "## 4.6"):
        assert section in text
    assert text.count("**Falta**") >= 5  # cada seção diz o que ainda falta fazer
    for pending in ("medição manual", "leitor de tela", "Zotero", "chaves"):
        assert pending in text or pending.capitalize() in text, pending


def test_the_package_never_claims_full_wcag_conformity() -> None:
    text = PACKAGE.read_text(encoding="utf-8").lower()
    for match in re.finditer(r"conformidade wcag 2\.1 aa", text):
        before = text[max(0, match.start() - 30) : match.start()]
        assert "não" in before, f"afirmação de conformidade sem negação: ...{before}"


def test_referenced_paths_are_found_in_a_sample_text() -> None:
    sample = "veja `docs/API.md`, `tests/unit/x.py` e `README.md` (esse último não é pasta listada)"
    assert referenced_paths(sample) == ["docs/API.md", "tests/unit/x.py"]
