"""Tarefas de desenvolvimento (substitui o Makefile, que não existe no Windows).

Uso: python tasks.py <alvo>
Alvos: install, lint, format, typecheck, test, run, check, sast
"""

from __future__ import annotations

import subprocess
import sys

COMMANDS: dict[str, list[list[str]]] = {
    "install": [
        ["uv", "sync"],
        ["uv", "export", "--format", "requirements-txt", "-o", "requirements.lock"],
    ],
    "lint": [["uv", "run", "ruff", "check", "."], ["uv", "run", "ruff", "format", "--check", "."]],
    "format": [["uv", "run", "ruff", "check", "--fix", "."], ["uv", "run", "ruff", "format", "."]],
    "typecheck": [["uv", "run", "mypy"]],
    "test": [["uv", "run", "pytest"]],
    "run": [["uv", "run", "python", "-m", "app.run"]],
    "sast": [
        ["uv", "run", "python", "scripts/run_sast.py"],
        ["uv", "run", "python", "scripts/sast_summary.py", "--write"],
    ],
}
COMMANDS["check"] = COMMANDS["lint"] + COMMANDS["typecheck"] + COMMANDS["test"]


def main(argv: list[str]) -> int:
    """Executa os comandos do alvo pedido, parando no primeiro que falhar."""
    if len(argv) != 2 or argv[1] not in COMMANDS:
        print(__doc__)
        return 2
    for cmd in COMMANDS[argv[1]]:
        print("$", " ".join(cmd), flush=True)
        code = subprocess.call(cmd)  # noqa: S603
        if code != 0:
            return code
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
