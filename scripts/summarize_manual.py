"""Resume a planilha da medição manual (OS-033): média, mínimo e máximo por método e consulta.

Uso:
    uv run python scripts/summarize_manual.py docs/evidencias/medicao/planilha_preenchida.csv

A planilha tem as colunas: consulta, metodo (manual ou aplicacao), pessoa, tempo, resultados_uteis,
observacoes. O tempo pode ser em segundos (`95`, `95,5`) ou `mm:ss` / `h:mm:ss`. Linhas sem tempo
(planilha ainda não preenchida) são ignoradas e contadas. Calcula só o que está na planilha: não
compara métodos nem estima ganho.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("consulta", "metodo", "tempo")
METHODS = {"manual": "manual", "aplicacao": "aplicação", "aplicação": "aplicação"}
Measure = tuple[str, str, float, float | None]  # consulta, método, segundos, resultados úteis


class SheetError(ValueError):
    """Planilha com coluna ausente ou valor que não dá para interpretar."""


def parse_seconds(value: str) -> float:
    """`95`, `95,5`, `1:35` ou `0:01:35` -> segundos."""
    text = value.strip().replace(",", ".")
    if ":" in text:
        parts = text.split(":")
        if len(parts) not in (2, 3):
            raise ValueError(value)
        numbers = [float(p) for p in parts]
        seconds = 0.0
        for number in numbers:
            seconds = seconds * 60 + number
        return seconds
    return float(text)


def format_seconds(seconds: float) -> str:
    whole = round(seconds)
    return f"{whole // 60}:{whole % 60:02d} ({seconds:.1f} s)"


def read_sheet(path: Path) -> tuple[list[Measure], int]:
    """Lê a planilha (vírgula ou ponto e vírgula) e devolve (medições, linhas sem tempo)."""
    text = path.read_text(encoding="utf-8-sig")
    header = text.splitlines()[0] if text.strip() else ""
    delimiter = ";" if header.count(";") > header.count(",") else ","
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
    if missing:
        raise SheetError("colunas ausentes na planilha: " + ", ".join(missing))
    measures: list[Measure] = []
    empty = 0
    for number, row in enumerate(reader, start=2):  # linha 1 é o cabeçalho
        raw_time = (row.get("tempo") or "").strip()
        if not raw_time:
            empty += 1
            continue
        method = METHODS.get((row.get("metodo") or "").strip().lower())
        if method is None:
            raise SheetError(f"linha {number}: método deve ser 'manual' ou 'aplicacao'")
        try:
            seconds = parse_seconds(raw_time)
        except ValueError:
            raise SheetError(f"linha {number}: tempo inválido: {raw_time!r}") from None
        if seconds < 0:
            raise SheetError(f"linha {number}: tempo negativo")
        useful_raw = (row.get("resultados_uteis") or "").strip()
        try:
            useful = float(useful_raw.replace(",", ".")) if useful_raw else None
        except ValueError:
            raise SheetError(f"linha {number}: resultados_uteis inválido: {useful_raw!r}") from None
        measures.append(((row.get("consulta") or "").strip(), method, seconds, useful))
    return measures, empty


def _line(label: str, items: list[Measure]) -> str:
    times = [m[2] for m in items]
    useful = [m[3] for m in items if m[3] is not None]
    useful_text = f"{statistics.fmean(useful):.1f}" if useful else "—"
    return (
        f"| {label} | {len(items)} | {format_seconds(statistics.fmean(times))} "
        f"| {format_seconds(min(times))} | {format_seconds(max(times))} | {useful_text} |"
    )


def summarize(measures: list[Measure], empty: int) -> str:
    lines = ["# Resumo da medição manual", ""]
    if not measures:
        lines += [
            "Nenhuma medição preenchida na planilha"
            + (f" ({empty} linhas sem tempo)." if empty else "."),
            "",
            "Sem medições não há o que resumir, e nenhuma conclusão sobre tempo pode ser escrita.",
        ]
        return "\n".join(lines) + "\n"
    header = "| {} | Medições | Média | Mínimo | Máximo | Resultados úteis (média) |"
    divider = "|---|---|---|---|---|---|"
    lines += ["## Por método", "", header.format("Método"), divider]
    for method in ("manual", "aplicação"):
        items = [m for m in measures if m[1] == method]
        if items:
            lines.append(_line(method, items))
    lines += ["", "## Por consulta e método", "", header.format("Consulta · método"), divider]
    for query in dict.fromkeys(m[0] for m in measures):
        for method in ("manual", "aplicação"):
            items = [m for m in measures if m[0] == query and m[1] == method]
            if items:
                lines.append(_line(f"{query} · {method}", items))
    lines += ["", f"Medições usadas: {len(measures)}. Linhas sem tempo, ignoradas: {empty}."]
    lines += [
        "",
        "Os números acima são exatamente os da planilha. Poucos participantes e consultas: não "
        "generalize (ver RELATORIO.md).",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("planilha", type=Path)
    parser.add_argument("--out", type=Path, help="grava o resumo neste arquivo (além de imprimir)")
    args = parser.parse_args(argv)
    try:
        measures, empty = read_sheet(args.planilha)
    except (SheetError, OSError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    text = summarize(measures, empty)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
