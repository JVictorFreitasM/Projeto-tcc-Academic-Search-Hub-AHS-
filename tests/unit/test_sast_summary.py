import json
from pathlib import Path

import pytest

from scripts import sast_summary as s

pytestmark = pytest.mark.unit

BANDIT = {
    "results": [
        {
            "test_id": "B101",
            "filename": "app\\core\\errors.py",
            "line_number": 10,
            "issue_severity": "LOW",
            "issue_text": "assert",
        },
        {
            "test_id": "B105",
            "filename": "app/x.py",
            "line_number": 3,
            "issue_severity": "LOW",
            "issue_text": "senha",
        },
    ]
}
SEMGREP = {
    "results": [
        {
            "check_id": "python.lang.x.rule",
            "path": "app/core/errors.py",
            "start": {"line": 10},
            "extra": {"severity": "WARNING", "message": "m"},
        },
        {"check_id": "a.b.c", "path": "app/outro.py", "start": {"line": 99}, "extra": {}},
    ]
}
RUFF = [
    {
        "code": "S101",
        "filename": "app/core/errors.py",
        "location": {"row": 10},
        "message": "assert",
    },
    {"code": "S105", "filename": "app/x.py", "location": {"row": 3}, "message": "senha"},
    {"code": "S106", "filename": "app/y.py", "location": {"row": 7}, "message": "arg"},
]
AUDIT = {
    "dependencies": [
        {"name": "a", "version": "1.0", "vulns": []},
        {"name": "b", "version": "2.0", "vulns": [{"id": "PYSEC-1", "description": "falha"}]},
    ]
}


def write(directory: Path, **files: object) -> None:
    for name, content in files.items():
        (directory / name.replace("_", "-", 1).replace("-json", ".json")).write_text(
            json.dumps(content), encoding="utf-8"
        )


def test_parsers_normalize_paths_and_fields() -> None:
    bandit = s.parse_bandit(BANDIT)
    assert bandit[0] == s.Finding("bandit", "B101", "app/core/errors.py", 10, "low", "assert")
    semgrep = s.parse_semgrep(SEMGREP)
    assert (
        semgrep[0].rule == "rule"
        and semgrep[0].severity == "warning"
        and semgrep[1].severity == "info"
    )
    ruff = s.parse_ruff(RUFF)
    assert [f.rule for f in ruff] == ["S101", "S105", "S106"]
    audit = s.parse_pip_audit(AUDIT)
    assert audit == [s.Finding("pip-audit", "PYSEC-1", "b==2.0", 0, "n/d", "falha")]
    assert s.count_dependencies(AUDIT) == 2


def test_overlap_counts_same_file_and_line_only() -> None:
    findings = {
        "bandit": s.parse_bandit(BANDIT),
        "semgrep": s.parse_semgrep(SEMGREP),
        "ruff-S": s.parse_ruff(RUFF),
        "pip-audit": [],
    }
    result = s.overlaps(findings)
    assert result[("bandit", "semgrep")] == 1  # errors.py:10
    assert result[("bandit", "ruff-S")] == 2  # errors.py:10 e x.py:3
    assert result[("semgrep", "ruff-S")] == 1


def test_overlap_with_missing_tool_is_zero_and_marked_in_report() -> None:
    findings = {
        "bandit": s.parse_bandit(BANDIT),
        "semgrep": None,
        "ruff-S": s.parse_ruff(RUFF),
        "pip-audit": [],
    }
    assert s.overlaps(findings)[("bandit", "semgrep")] == 0
    report = s.render(findings, 86)
    assert "| semgrep | **não** | n/d | n/d |" in report
    assert "n/d (uma delas não rodou)" in report
    assert "analisou 86 dependências" in report


def test_render_counts_findings_and_distinct_spots() -> None:
    findings = {
        "bandit": s.parse_bandit(BANDIT),
        "semgrep": s.parse_semgrep(SEMGREP),
        "ruff-S": s.parse_ruff(RUFF),
        "pip-audit": s.parse_pip_audit(AUDIT),
    }
    report = s.render(findings, 2)
    assert "| bandit | sim | 2 | 2 |" in report
    assert "| ruff-S | sim | 3 | 3 |" in report
    assert "| pip-audit | sim | 1 | n/a |" in report
    assert "| bandit x semgrep | 1 |" in report


def test_load_reads_files_and_marks_missing_tools(tmp_path: Path) -> None:
    (tmp_path / "bandit.json").write_text(json.dumps(BANDIT), encoding="utf-8")
    (tmp_path / "pip-audit.json").write_text(json.dumps(AUDIT), encoding="utf-8")
    loaded = s.load(tmp_path)
    assert len(loaded["bandit"] or []) == 2 and len(loaded["pip-audit"] or []) == 1
    assert loaded["semgrep"] is None and loaded["ruff-S"] is None


def test_empty_results_are_valid() -> None:
    assert (
        s.parse_bandit({"results": []}) == []
        and s.parse_semgrep({}) == []
        and s.parse_ruff([]) == []
    )
    assert s.parse_pip_audit({"dependencies": []}) == []
