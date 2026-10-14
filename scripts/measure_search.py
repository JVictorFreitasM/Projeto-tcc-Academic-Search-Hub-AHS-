"""Mede a busca da aplicação (OS-033): tempo, resultados por fonte, duplicatas e falhas.

Uso (com a aplicação rodando, chaves reais e índice colhido):
    uv run python scripts/measure_search.py --base-url http://127.0.0.1:8000 --runs 5

Para cada consulta de docs/evidencias/medicao/consultas.txt, faz a busca `--runs` vezes e grava
docs/evidencias/medicao/resultado-AAAAMMDD.csv (uma linha por consulta, execução e fonte) e
resultado-AAAAMMDD.md (resumo). Todos os números vêm das respostas e do cronômetro desta execução;
nada é estimado. As consultas são escolhidas pelo desenvolvedor: o arquivo não vem preenchido.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
import time
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
MEDICAO = ROOT / "docs" / "evidencias" / "medicao"
FIELDS = [
    "consulta",
    "execucao",
    "tempo_total_ms",
    "http_status",
    "resultados_exibidos",
    "registros_das_fontes",
    "duplicatas_fundidas",
    "fonte",
    "status_da_fonte",
    "fonte_registros",
    "fonte_total_estimado",
    "fonte_duracao_ms",
]
Row = dict[str, Any]


class NoQueriesError(ValueError):
    """O arquivo de consultas está vazio: o desenvolvedor ainda não definiu as 5 consultas."""


def load_queries(path: Path) -> list[str]:
    """Uma consulta por linha; linhas em branco e iniciadas por `#` são ignoradas."""
    queries = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not queries:
        raise NoQueriesError(
            f"{path} não tem nenhuma consulta. "
            "Escreva as 5 consultas (uma por linha) antes de medir."
        )
    return queries


def duplicates_merged(status: dict[str, Any], shown: int, page_size: int) -> int | None:
    """Duplicatas fundidas = registros devolvidos pelas fontes menos resultados exibidos.

    Só é determinável quando a página não cortou nada (soma das fontes <= page_size): senão a
    diferença mistura fusão e corte, e o valor fica vazio em vez de um número enganoso.
    """
    returned = sum(int(item.get("count") or 0) for item in status.values())
    if returned > page_size:
        return None
    return returned - shown


def rows_from_response(
    query: str, run: int, total_ms: float, http_status: int, body: dict[str, Any], page_size: int
) -> list[Row]:
    """Linhas do CSV (uma por fonte) para uma execução. Resposta sem corpo válido gera uma linha."""
    base: Row = {
        "consulta": query,
        "execucao": run,
        "tempo_total_ms": round(total_ms, 1),
        "http_status": http_status,
    }
    status = body.get("sources_status") if isinstance(body, dict) else None
    if http_status != 200 or not isinstance(status, dict):
        return [{**base, "fonte": "(aplicação)", "status_da_fonte": f"http_{http_status}"}]
    shown = len(body.get("results", []))
    returned = sum(int(item.get("count") or 0) for item in status.values())
    merged = duplicates_merged(status, shown, page_size)
    common = {
        **base,
        "resultados_exibidos": shown,
        "registros_das_fontes": returned,
        "duplicatas_fundidas": "" if merged is None else merged,
    }
    return [
        {
            **common,
            "fonte": slug,
            "status_da_fonte": item.get("status"),
            "fonte_registros": item.get("count"),
            "fonte_total_estimado": item.get("total"),
            "fonte_duracao_ms": item.get("duration_ms", ""),
        }
        for slug, item in sorted(status.items())
    ]


def measure(
    client: httpx.Client, queries: Iterable[str], runs: int, page_size: int = 20
) -> list[Row]:
    """Executa cada consulta `runs` vezes contra `/api/v1/search` e devolve as linhas medidas."""
    rows: list[Row] = []
    for query in queries:
        for run in range(1, runs + 1):
            started = time.perf_counter()
            try:
                response = client.get("/api/v1/search", params={"q": query, "page_size": page_size})
                status_code = response.status_code
                body = response.json() if response.content else {}
            except httpx.HTTPError as exc:
                status_code, body = 0, {"erro": type(exc).__name__}
            elapsed_ms = (time.perf_counter() - started) * 1000
            rows += rows_from_response(query, run, elapsed_ms, status_code, body, page_size)
    return rows


def write_csv(rows: list[Row], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:  # utf-8-sig: abre no Excel
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter=";")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def _has(row: Row, field: str) -> bool:
    return row.get(field) not in ("", None)


def _stats(values: list[float]) -> str:
    if not values:
        return "sem dados"
    return (
        f"média {statistics.fmean(values):.0f} ms · mín {min(values):.0f} · máx {max(values):.0f}"
    )


def summarize(rows: list[Row], day: date) -> str:
    """Resumo em Markdown. Só repete números calculados das linhas medidas."""
    lines = [f"# Resultado da medição da aplicação ({day:%d/%m/%Y})", ""]
    queries = list(dict.fromkeys(row["consulta"] for row in rows))
    lines += [
        "Gerado por `scripts/measure_search.py`. Tempo total = cronômetro do cliente, do pedido à "
        "resposta completa; duração por fonte = `sources_status.duration_ms` da resposta.",
        "",
        "## Tempo total por consulta",
        "",
        "| Consulta | Execuções | Tempo total | Resultados exibidos (média) "
        "| Duplicatas fundidas |",
        "|---|---|---|---|---|",
    ]
    for query in queries:
        mine = [r for r in rows if r["consulta"] == query]
        runs = {r["execucao"]: r for r in mine}  # as colunas de execução se repetem por fonte
        totals = [float(r["tempo_total_ms"]) for r in runs.values()]
        shown = [
            float(r["resultados_exibidos"]) for r in runs.values() if _has(r, "resultados_exibidos")
        ]
        merged = [
            int(r["duplicatas_fundidas"]) for r in runs.values() if _has(r, "duplicatas_fundidas")
        ]
        shown_text = f"{statistics.fmean(shown):.1f}" if shown else "sem dados"
        merged_text = (
            f"{sum(merged)} (em {len(merged)} de {len(runs)} execuções)"
            if merged
            else "não determinável"
        )
        lines.append(f"| {query} | {len(runs)} | {_stats(totals)} | {shown_text} | {merged_text} |")
    lines += [
        "",
        "## Por fonte",
        "",
        "| Fonte | Respostas | Falhas | Duração |",
        "|---|---|---|---|",
    ]
    for source in sorted({r["fonte"] for r in rows}):
        mine = [r for r in rows if r["fonte"] == source]
        failed = [r for r in mine if r["status_da_fonte"] != "ok"]
        durations = [float(r["fonte_duracao_ms"]) for r in mine if _has(r, "fonte_duracao_ms")]
        lines.append(f"| {source} | {len(mine)} | {len(failed)} | {_stats(durations)} |")
    failures = sorted(
        {f"{r['fonte']}: {r['status_da_fonte']}" for r in rows if r["status_da_fonte"] != "ok"}
    )
    lines += ["", "## Fontes que não responderam como `ok`", ""]
    lines += [f"- {item}" for item in failures] or ["- nenhuma nas execuções medidas"]
    lines += [
        "",
        "Duplicatas fundidas = registros devolvidos pelas fontes menos resultados exibidos; só é "
        'calculada quando a página não cortou resultados (senão fica "não determinável").',
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--queries", type=Path, default=MEDICAO / "consultas.txt")
    parser.add_argument("--out-dir", type=Path, default=MEDICAO)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args(argv)
    if args.runs < 1:
        parser.error("--runs deve ser pelo menos 1")
    try:
        queries = load_queries(args.queries)
    except (NoQueriesError, OSError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    today = date.today()
    with httpx.Client(base_url=args.base_url, timeout=args.timeout) as client:
        rows = measure(client, queries, args.runs, args.page_size)
    stem = f"resultado-{today:%Y%m%d}"
    write_csv(rows, args.out_dir / f"{stem}.csv")
    (args.out_dir / f"{stem}.md").write_text(summarize(rows, today), encoding="utf-8")
    print(f"{len(queries)} consultas x {args.runs} execuções; saída em {args.out_dir / stem}.*")
    return 0


if __name__ == "__main__":
    sys.exit(main())
