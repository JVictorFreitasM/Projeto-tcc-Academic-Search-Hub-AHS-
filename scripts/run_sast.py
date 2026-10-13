"""Roda as ferramentas de análise estática e grava as saídas brutas (alvo `sast`).

Ferramentas: bandit, pip-audit, semgrep (se instalável/encontrado) e ruff com as regras `S`
(o mesmo conjunto do bandit, com `--ignore-noqa` para mostrar também o que foi justificado).
Se o semgrep não estiver disponível, isso é dito de forma explícita: nunca se finge que rodou.

Uso: uv run python scripts/run_sast.py   (opcional: SEMGREP_BIN=caminho\\do\\semgrep.exe)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "evidencias" / "sast"


def run(cmd: list[str], *, ok_codes: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(  # noqa: S603
        cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False,
        env={**os.environ, "PYTHONUTF8": "1", "SEMGREP_SEND_METRICS": "off"},
    )  # fmt: skip
    if result.returncode not in ok_codes:
        sys.stderr.write(result.stderr[-2000:])
    return result


def version(cmd: list[str]) -> str:
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)  # noqa: S603
    return (
        (result.stdout or result.stderr).strip().splitlines()[0]
        if (result.stdout or result.stderr)
        else "n/d"
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    meta: dict[str, object] = {
        "data": datetime.now(UTC).isoformat(timespec="seconds"),
        "ferramentas": {},
    }
    tools: dict[str, object] = {}

    run(
        ["uv", "run", "bandit", "-r", "app", "-f", "json", "-o", str(OUT / "bandit.json")],
        ok_codes=(0, 1),
    )
    tools["bandit"] = version(["uv", "run", "bandit", "--version"]).replace("python.exe ", "")

    run(["uv", "run", "pip-audit", "-r", "requirements.lock", "--no-deps", "--disable-pip",
         "-f", "json", "-o", str(OUT / "pip-audit.json")], ok_codes=(0, 1))  # fmt: skip
    tools["pip-audit"] = version(["uv", "run", "pip-audit", "--version"])

    ruff = run(["uv", "run", "ruff", "check", "app", "--select", "S", "--ignore-noqa",
                "--output-format", "json", "--no-cache"], ok_codes=(0, 1))  # fmt: skip
    (OUT / "ruff-S.json").write_text(ruff.stdout or "[]", encoding="utf-8")
    tools["ruff-S"] = version(["uv", "run", "ruff", "--version"])

    semgrep = os.environ.get("SEMGREP_BIN") or shutil.which("semgrep")
    if (semgrep and Path(semgrep).exists()) or (semgrep and shutil.which(semgrep)):
        run([semgrep, "--config", "p/python", "--config", "p/owasp-top-ten", "--metrics=off",
             "--json", "--output", str(OUT / "semgrep.json"), "app", "frontend"],
            ok_codes=(0, 1))  # fmt: skip
        tools["semgrep"] = version([semgrep, "--version"])
    else:
        sys.stdout.write(
            "semgrep NÃO encontrado: não rodou (defina SEMGREP_BIN). Nada foi simulado.\n"
        )
        tools["semgrep"] = "não executado"
    meta["ferramentas"] = tools
    (OUT / "versoes.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    sys.stdout.write(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
