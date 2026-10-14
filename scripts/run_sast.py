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


OUTPUT_FILES = ("bandit.json", "pip-audit.json", "ruff-S.json", "semgrep.json")


def version(cmd: list[str]) -> str:
    """Primeira linha da versão da ferramenta; se o comando falhar, diz que falhou."""
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)  # noqa: S603
    text = (result.stdout or result.stderr).strip()
    if result.returncode != 0 or not text:
        return "n/d (não foi possível obter a versão)"
    return text.splitlines()[0]


def remove_stale_outputs(folder: Path) -> None:
    """Apaga as saídas de uma execução anterior: nada de reaproveitar arquivo velho como se fosse
    desta execução (um semgrep que falha não pode deixar o resultado de outro dia no lugar)."""
    for name in OUTPUT_FILES:
        (folder / name).unlink(missing_ok=True)


def tool_status(returncode: int, output: Path, ok_codes: tuple[int, ...] = (0, 1)) -> str:
    """`ok`, ou o motivo de a ferramenta não ter produzido uma saída confiável."""
    if returncode not in ok_codes:
        return f"FALHOU (código {returncode})"
    if not output.exists() or output.stat().st_size == 0:
        return "FALHOU (sem arquivo de saída)"
    return "ok"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    remove_stale_outputs(OUT)
    meta: dict[str, object] = {
        "data": datetime.now(UTC).isoformat(timespec="seconds"),
        "ferramentas": {},
    }
    tools: dict[str, object] = {}
    failures: list[str] = []

    def record(name: str, status: str, tool_version: str) -> None:
        tools[name] = tool_version if status == "ok" else f"{status}; versão: {tool_version}"
        if status != "ok":
            failures.append(f"{name}: {status}")

    bandit = run(
        ["uv", "run", "bandit", "-r", "app", "-f", "json", "-o", str(OUT / "bandit.json")],
        ok_codes=(0, 1),
    )
    record(
        "bandit",
        tool_status(bandit.returncode, OUT / "bandit.json"),
        version(["uv", "run", "bandit", "--version"]).replace("python.exe ", ""),
    )

    audit = run(["uv", "run", "pip-audit", "-r", "requirements.lock", "--no-deps", "--disable-pip",
                 "-f", "json", "-o", str(OUT / "pip-audit.json")], ok_codes=(0, 1))  # fmt: skip
    record(
        "pip-audit",
        tool_status(audit.returncode, OUT / "pip-audit.json"),
        version(["uv", "run", "pip-audit", "--version"]),
    )

    ruff = run(["uv", "run", "ruff", "check", "app", "--select", "S", "--ignore-noqa",
                "--output-format", "json", "--no-cache"], ok_codes=(0, 1))  # fmt: skip
    (OUT / "ruff-S.json").write_text(ruff.stdout or "[]", encoding="utf-8")
    record(
        "ruff-S",
        tool_status(ruff.returncode, OUT / "ruff-S.json"),
        version(["uv", "run", "ruff", "--version"]),
    )

    semgrep = os.environ.get("SEMGREP_BIN") or shutil.which("semgrep")
    if (semgrep and Path(semgrep).exists()) or (semgrep and shutil.which(semgrep)):
        scan = run([semgrep, "--config", "p/python", "--config", "p/owasp-top-ten", "--metrics=off",
                    "--json", "--output", str(OUT / "semgrep.json"), "app", "frontend"],
                   ok_codes=(0, 1))  # fmt: skip
        record(
            "semgrep",
            tool_status(scan.returncode, OUT / "semgrep.json"),
            version([semgrep, "--version"]),
        )
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
    for failure in failures:
        sys.stderr.write(f"FALHA na análise estática: {failure}\n")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
