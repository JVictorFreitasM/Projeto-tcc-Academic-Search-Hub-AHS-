"""Calcula as razões de contraste (WCAG 2.1) dos pares de cores de frontend/css/tokens.css.

Uso: uv run python scripts/contrast_check.py [--write-doc]

Lê as variáveis CSS do arquivo de tokens, calcula a razão de cada par declarado em PAIRS e falha
(código 1) se algum não atingir o mínimo. Com --write-doc, grava a tabela em docs/ACESSIBILIDADE.md.
Nada é estimado: os números impressos são os calculados.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "frontend" / "css" / "tokens.css"
DOC = ROOT / "docs" / "ACESSIBILIDADE.md"
MARK_START = "<!-- contraste:inicio -->"
MARK_END = "<!-- contraste:fim -->"

TEXT_MIN = 4.5  # texto comum (WCAG 1.4.3)
UI_MIN = 3.0  # texto grande e componentes de interface (WCAG 1.4.3 e 1.4.11)


@dataclass(frozen=True)
class Pair:
    foreground: str
    background: str
    minimum: float
    use: str


PAIRS = [
    Pair("--color-text", "--color-bg", TEXT_MIN, "texto comum sobre o fundo"),
    Pair("--color-text", "--color-surface", TEXT_MIN, "texto comum sobre superfícies"),
    Pair("--color-text-muted", "--color-bg", TEXT_MIN, "texto secundário sobre o fundo"),
    Pair("--color-text-muted", "--color-surface", TEXT_MIN, "texto secundário sobre superfícies"),
    Pair("--color-primary", "--color-bg", TEXT_MIN, "links e texto na cor primária"),
    Pair("--color-primary", "--color-surface", TEXT_MIN, "links sobre superfícies"),
    Pair("--color-on-primary", "--color-primary", TEXT_MIN, "texto de botão primário"),
    Pair("--color-on-primary", "--color-primary-hover", TEXT_MIN, "botão primário em foco/hover"),
    Pair("--color-danger", "--color-bg", TEXT_MIN, "mensagens de erro"),
    Pair("--color-danger", "--color-danger-bg", TEXT_MIN, "erro sobre aviso de erro"),
    Pair("--color-success", "--color-bg", TEXT_MIN, "mensagens de sucesso"),
    Pair("--color-success", "--color-success-bg", TEXT_MIN, "sucesso sobre aviso de sucesso"),
    Pair("--color-warning-text", "--color-warning-bg", TEXT_MIN, "texto de aviso"),
    Pair("--color-info-text", "--color-info-bg", TEXT_MIN, "texto informativo"),
    Pair("--color-badge-text", "--color-badge-bg", TEXT_MIN, "selos de fonte e tipo"),
    Pair("--color-border-strong", "--color-bg", UI_MIN, "borda de campos e botões"),
    Pair("--color-border-strong", "--color-surface", UI_MIN, "borda de campos sobre superfícies"),
    Pair("--color-focus", "--color-bg", UI_MIN, "anel de foco sobre o fundo"),
    Pair("--color-focus", "--color-surface", UI_MIN, "anel de foco sobre superfícies"),
    # O anel de foco usa outline-offset de 2 px: entre ele e o botão primário aparece o fundo da
    # página, então o par (foco x primário) não se toca e não entra na conferência. Foco x fundo
    # e foco x superfície acima cobrem o que fica ao redor do anel.
]


def read_tokens(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    return {
        name: value.lower()
        for name, value in re.findall(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{6})\s*;", text)
    }


def _linear(channel: int) -> float:
    value = channel / 255
    return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _linear(r) + 0.7152 * _linear(g) + 0.0722 * _linear(b)


def contrast(a: str, b: str) -> float:
    first, second = sorted((luminance(a), luminance(b)), reverse=True)
    return (first + 0.05) / (second + 0.05)


def evaluate(tokens: dict[str, str]) -> list[tuple[Pair, float, bool]]:
    results = []
    for pair in PAIRS:
        ratio = contrast(tokens[pair.foreground], tokens[pair.background])
        results.append((pair, ratio, ratio >= pair.minimum))
    return results


def render_table(tokens: dict[str, str], results: list[tuple[Pair, float, bool]]) -> str:
    lines = [
        "| Primeiro plano | Fundo | Razão calculada | Mínimo | Resultado | Uso |",
        "|---|---|---|---|---|---|",
    ]
    for pair, ratio, ok in results:
        lines.append(
            f"| `{pair.foreground}` {tokens[pair.foreground]} | `{pair.background}` "
            f"{tokens[pair.background]} | {ratio:.2f}:1 | {pair.minimum:g}:1 | "
            f"{'passa' if ok else 'FALHA'} | {pair.use} |"
        )
    return "\n".join(lines)


def write_doc(table: str) -> None:
    block = f"{MARK_START}\n{table}\n{MARK_END}"
    text = DOC.read_text(encoding="utf-8") if DOC.exists() else "# Acessibilidade\n\n"
    if MARK_START in text:
        head, rest = text.split(MARK_START, 1)
        tail = rest.split(MARK_END, 1)[1]
        text = head + block + tail
    else:
        text = (
            text.rstrip()
            + "\n\n## Contraste das cores (calculado por `scripts/contrast_check.py`)\n\n"
            + block
            + "\n"
        )
    DOC.write_text(text, encoding="utf-8")


def main(argv: list[str]) -> int:
    tokens = read_tokens(TOKENS)
    results = evaluate(tokens)
    table = render_table(tokens, results)
    sys.stdout.write(table + "\n")
    if "--write-doc" in argv:
        write_doc(table)
    failed = [pair for pair, _, ok in results if not ok]
    if failed:
        sys.stderr.write(f"{len(failed)} par(es) abaixo do mínimo.\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
