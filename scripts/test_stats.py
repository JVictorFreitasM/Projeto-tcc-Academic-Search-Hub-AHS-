"""Conta os testes por marcador (comando `pytest --collect-only`) e resume a cobertura medida.

Uso: uv run python scripts/test_stats.py

Os números saem de comandos executados agora (coleta de testes e do `coverage.xml` da última
execução de `pytest`); nada é digitado à mão. Grava docs/evidencias/os-030-cobertura.txt.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET  # nosec B405 - arquivo local gerado pelo coverage
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "evidencias" / "os-030-cobertura.txt"
MARKERS = ("unit", "integration", "contract", "e2e", "a11y")


def collect(marker: str | None) -> int:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--collect-only",
        "-q",
        "--no-cov",
        "-p",
        "no:cacheprovider",
        "tests",
    ]
    if marker:
        cmd[-1:-1] = ["-m", marker]
    result = subprocess.run(  # noqa: S603
        cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False,
        env={**os.environ, "PYTHONUTF8": "1"},
    )  # fmt: skip
    match = re.search(r"(\d+)(?:/\d+)? tests? collected", result.stdout) or re.search(
        r"(\d+) tests? collected", result.stdout + result.stderr
    )
    if match:
        return int(match.group(1))
    return sum(1 for line in result.stdout.splitlines() if "::" in line)


def coverage_lines() -> list[str]:
    path = ROOT / "coverage.xml"
    if not path.exists():
        return ["coverage.xml não existe: rode `python tasks.py test` antes."]
    root = ET.parse(path).getroot()  # noqa: S314  # nosec B314 - arquivo local do próprio coverage
    rate = float(root.attrib["line-rate"]) * 100
    lines = [f"Cobertura de linhas de app/ (pytest-cov): {rate:.1f}%"]
    lines.append(
        f"(linhas cobertas {root.attrib.get('lines-covered')} de {root.attrib.get('lines-valid')})"
    )
    worst = []
    for cls in root.iter("class"):
        value = float(cls.attrib["line-rate"]) * 100
        worst.append((value, cls.attrib["filename"]))
    lines.append("Arquivos com menor cobertura:")
    lines += [f"  {value:5.1f}%  {name}" for value, name in sorted(worst)[:8]]
    return lines


def main() -> int:
    total = collect(None)
    rows = [(marker, collect(marker)) for marker in MARKERS]
    out = [
        "Testes por marcador (coletados por `pytest --collect-only`):",
        "",
        "| Marcador | Testes |",
        "|---|---|",
    ]
    out += [f"| {marker} | {count} |" for marker, count in rows]
    out += [f"| **total** | **{total}** |", ""]
    out += coverage_lines()
    text = "\n".join(out) + "\n"
    OUT.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
