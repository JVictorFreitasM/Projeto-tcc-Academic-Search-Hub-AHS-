"""scripts/run_sast.py (OS-035): saída velha não passa por nova, e ferramenta que falha é dita."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def sast() -> ModuleType:
    spec = importlib.util.spec_from_file_location("run_sast", ROOT / "scripts" / "run_sast.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_sast"] = module
    spec.loader.exec_module(module)
    return module


def test_stale_outputs_are_removed_before_a_new_run(sast: ModuleType, tmp_path: Path) -> None:
    for name in sast.OUTPUT_FILES:
        (tmp_path / name).write_text("{}")
    (tmp_path / "RESUMO.md").write_text("não é saída de ferramenta")
    sast.remove_stale_outputs(tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["RESUMO.md"]
    sast.remove_stale_outputs(tmp_path)  # sem arquivos: não dá erro


def test_a_tool_is_ok_only_with_an_accepted_exit_code_and_a_non_empty_output(
    sast: ModuleType, tmp_path: Path
) -> None:
    output = tmp_path / "out.json"
    assert sast.tool_status(0, output) == "FALHOU (sem arquivo de saída)"
    output.write_text("")
    assert sast.tool_status(0, output) == "FALHOU (sem arquivo de saída)"
    output.write_text("{}")
    assert sast.tool_status(0, output) == "ok"
    assert sast.tool_status(1, output) == "ok"  # bandit e semgrep saem com 1 quando há achados
    assert sast.tool_status(2, output) == "FALHOU (código 2)"
    assert sast.tool_status(-1, output) == "FALHOU (código -1)"


def test_a_failing_version_command_is_reported_instead_of_its_error_text(
    sast: ModuleType,
) -> None:
    broken = [sys.executable, "-c", "import sys; print('error: trampoline failed'); sys.exit(3)"]
    assert sast.version(broken).startswith("n/d")
    working = [sys.executable, "-c", "print('ferramenta 1.2.3')"]
    assert sast.version(working) == "ferramenta 1.2.3"
