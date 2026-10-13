"""Resume as saídas brutas da análise estática (bandit, pip-audit, semgrep, ruff-S).

Uso: uv run python scripts/sast_summary.py [--write]

Lê os JSON de docs/evidencias/sast/ e calcula, por ferramenta, quantos achados houve e quantos se
sobrepõem (mesmo arquivo e mesma linha) com os de outra ferramenta. Nada é estimado: os números
saem das contagens dos próprios arquivos. Com --write, grava docs/evidencias/sast/RESUMO.md.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SAST_DIR = ROOT / "docs" / "evidencias" / "sast"
TOOLS = ("bandit", "semgrep", "ruff-S", "pip-audit")
CODE_TOOLS = ("bandit", "semgrep", "ruff-S")  # as que apontam arquivo e linha


@dataclass(frozen=True)
class Finding:
    tool: str
    rule: str
    file: str
    line: int
    severity: str
    message: str


def _norm(path: str) -> str:
    """Caminho relativo à raiz do projeto, com barras normais (aceita caminhos absolutos)."""
    text = path.replace("\\", "/")
    for marker in ("/app/", "/frontend/"):
        if marker in text:
            return text[text.rindex(marker) + 1 :]
    return text.lstrip("./")


def parse_bandit(data: dict[str, Any]) -> list[Finding]:
    return [
        Finding("bandit", r["test_id"], _norm(r["filename"]), int(r["line_number"]),
                r["issue_severity"].lower(), r["issue_text"])
        for r in data.get("results", [])
    ]  # fmt: skip


def parse_semgrep(data: dict[str, Any]) -> list[Finding]:
    return [
        Finding("semgrep", r["check_id"].rsplit(".", 1)[-1], _norm(r["path"]),
                int(r["start"]["line"]), r.get("extra", {}).get("severity", "info").lower(),
                r.get("extra", {}).get("message", ""))
        for r in data.get("results", [])
    ]  # fmt: skip


def parse_ruff(data: list[dict[str, Any]]) -> list[Finding]:
    return [
        Finding("ruff-S", r["code"], _norm(r["filename"]),
                int(r["location"]["row"]), "n/d", r["message"])
        for r in data
    ]  # fmt: skip


def parse_pip_audit(data: dict[str, Any]) -> list[Finding]:
    found = []
    for dep in data.get("dependencies", []):
        for vuln in dep.get("vulns", []):
            found.append(
                Finding("pip-audit", vuln["id"], f"{dep['name']}=={dep['version']}", 0, "n/d",
                        vuln.get("description", ""))
            )  # fmt: skip
    return found


def count_dependencies(data: dict[str, Any]) -> int:
    return len(data.get("dependencies", []))


def load(directory: Path = SAST_DIR) -> dict[str, list[Finding] | None]:
    """Achados por ferramenta; `None` quando o arquivo da ferramenta não existe (não rodou)."""
    parsers = {
        "bandit": ("bandit.json", parse_bandit),
        "semgrep": ("semgrep.json", parse_semgrep),
        "ruff-S": ("ruff-S.json", parse_ruff),
        "pip-audit": ("pip-audit.json", parse_pip_audit),
    }
    result: dict[str, list[Finding] | None] = {}
    for tool, (name, parser) in parsers.items():
        path = directory / name
        result[tool] = (
            parser(json.loads(path.read_text(encoding="utf-8-sig"))) if path.exists() else None
        )
    return result


def overlaps(findings: dict[str, list[Finding] | None]) -> dict[tuple[str, str], int]:
    """Quantos pontos (arquivo + linha) duas ferramentas de código apontam em comum."""
    spots = {tool: {(f.file, f.line) for f in (findings.get(tool) or [])} for tool in CODE_TOOLS}
    return {(a, b): len(spots[a] & spots[b]) for a, b in combinations(CODE_TOOLS, 2)}


def render(findings: dict[str, list[Finding] | None], dependencies: int | None = None) -> str:
    lines = [
        "| Ferramenta | Rodou? | Achados | Pontos distintos (arquivo+linha) |",
        "|---|---|---|---|",
    ]
    for tool in TOOLS:
        items = findings.get(tool)
        if items is None:
            lines.append(f"| {tool} | **não** | n/d | n/d |")
            continue
        spots = len({(f.file, f.line) for f in items}) if tool != "pip-audit" else "n/a"
        lines.append(f"| {tool} | sim | {len(items)} | {spots} |")
    if dependencies is not None:
        lines.append("")
        lines.append(f"`pip-audit` analisou {dependencies} dependências.")
    lines += ["", "Sobreposição entre ferramentas de código (mesmo arquivo e linha):", ""]
    lines += ["| Par | Pontos em comum |", "|---|---|"]
    ran = {t for t in CODE_TOOLS if findings.get(t) is not None}
    for (a, b), count in overlaps(findings).items():
        value = str(count) if a in ran and b in ran else "n/d (uma delas não rodou)"
        lines.append(f"| {a} x {b} | {value} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    directory = Path(argv[argv.index("--dir") + 1]) if "--dir" in argv else SAST_DIR
    findings = load(directory)
    audit = directory / "pip-audit.json"
    dependencies = (
        count_dependencies(json.loads(audit.read_text(encoding="utf-8-sig")))
        if audit.exists()
        else None
    )
    table = render(findings, dependencies)
    sys.stdout.write(table)
    if "--write" in argv:
        (directory / "RESUMO.md").write_text(
            "# Resumo da análise estática (gerado por script)\n\n" + table, encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
