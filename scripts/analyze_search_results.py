"""Analisa resultados reais da API para o cenário controlado do TCC."""

from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import httpx
from measure_search import load_queries

ROOT = Path(__file__).resolve().parents[1]
MEDICAO = ROOT / "docs" / "evidencias" / "medicao"
STOPWORDS = {"a", "as", "de", "do", "da", "dos", "das", "e", "em", "na", "no", "para"}


def normalized_words(value: str) -> set[str]:
    text = unicodedata.normalize("NFKD", value.lower()).encode("ascii", "ignore").decode()
    return {
        word for word in re.findall(r"[a-z0-9]+", text) if word not in STOPWORDS and len(word) > 2
    }


def percentage(part: int, total: int) -> float:
    return round(100 * part / total, 1) if total else 0.0


def has_author(record: dict[str, Any]) -> bool:
    return bool(record.get("authors"))


def lexical_match(record: dict[str, Any], query: str) -> bool:
    query_words = normalized_words(query)
    content_words = normalized_words(f"{record.get('title', '')} {record.get('abstract', '')}")
    return bool(query_words & content_words)


def analyze_response(query: str, elapsed_ms: float, body: dict[str, Any]) -> dict[str, Any]:
    results: list[dict[str, Any]] = body.get("results", [])
    total = len(results)
    fields = {
        "autoria": sum(has_author(item) for item in results),
        "ano": sum(item.get("year") is not None for item in results),
        "resumo": sum(bool(item.get("abstract")) for item in results),
        "doi": sum(bool(item.get("doi")) for item in results),
        "pdf": sum(bool(item.get("pdf_url")) for item in results),
        "idioma": sum(bool(item.get("language")) for item in results),
    }
    source_status = body.get("sources_status", {})
    return {
        "consulta": query,
        "tempo_ms": round(elapsed_ms, 1),
        "total_estimado": body.get("total_estimated", 0),
        "resultados_exibidos": total,
        "fontes_ok": sorted(k for k, v in source_status.items() if v.get("status") == "ok"),
        "fontes_com_falha": sorted(k for k, v in source_status.items() if v.get("status") != "ok"),
        "completude": {
            key: {"n": value, "percentual": percentage(value, total)}
            for key, value in fields.items()
        },
        "aderencia_lexical": {
            "n": sum(lexical_match(item, query) for item in results),
            "percentual": percentage(sum(lexical_match(item, query) for item in results), total),
        },
        "registros_multifonte": sum(len(item.get("sources", [])) > 1 for item in results),
        "tipos": dict(sorted(Counter(item.get("type", "other") for item in results).items())),
    }


def to_markdown(analyses: list[dict[str, Any]], day: date) -> str:
    lines = [
        f"# Análise multidimensional do cenário controlado ({day:%d/%m/%Y})",
        "",
        "Os dados vieram de respostas reais da aplicação, com uma execução por consulta ",
        "e 20 itens na primeira página. O cenário representa um perfil fictício de estudante ",
        "e não corresponde a um participante. A aderência lexical indica apenas a presença ",
        "de ao menos uma palavra relevante da consulta no título ou resumo; não é uma avaliação ",
        "humana de relevância.",
        "",
        "## Resultado por consulta",
        "",
        (
            "| Consulta | Tempo | Total estimado | Exibidos | Fontes OK | "
            "Aderência lexical | Mult fonte |"
        ),
        "|---|---:|---:|---:|---|---:|---:|",
    ]
    for item in analyses:
        lines.append(
            f"| {item['consulta']} | {item['tempo_ms']:.1f} ms | {item['total_estimado']} | "
            f"{item['resultados_exibidos']} | {', '.join(item['fontes_ok']) or 'nenhuma'} | "
            f"{item['aderencia_lexical']['percentual']:.1f}% | {item['registros_multifonte']} |"
        )
    lines += [
        "",
        "## Completude da primeira página",
        "",
        "| Consulta | Autoria | Ano | Resumo | DOI | PDF | Idioma |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in analyses:
        values = item["completude"]
        lines.append(
            f"| {item['consulta']} | {values['autoria']['percentual']:.1f}% | "
            f"{values['ano']['percentual']:.1f}% | {values['resumo']['percentual']:.1f}% | "
            f"{values['doi']['percentual']:.1f}% | {values['pdf']['percentual']:.1f}% | "
            f"{values['idioma']['percentual']:.1f}% |"
        )
    ok_counts = Counter(source for item in analyses for source in item["fontes_ok"])
    failure_counts = Counter(source for item in analyses for source in item["fontes_com_falha"])
    lines += [
        "",
        "## Disponibilidade das fontes",
        "",
        "| Fonte | Respostas OK | Respostas não OK |",
        "|---|---:|---:|",
    ]
    for source in sorted(ok_counts.keys() | failure_counts.keys()):
        lines.append(f"| {source} | {ok_counts[source]} | {failure_counts[source]} |")
    lines += [
        "",
        "## Comparação procedural do cenário",
        "",
        "Na busca convencional simulada, o mesmo texto teria de ser submetido separadamente às "
        "quatro fontes operacionais avaliadas (CORE, OpenAlex, BDTD e índice UFPE), seguido de "
        "cópia e consolidação dos resultados. Na aplicação, cada tema exigiu uma submissão e a "
        "consolidação ocorreu no serviço de busca. Para cinco temas, isso corresponde a 20 "
        "submissões repetidas no fluxo convencional contra 5 na aplicação. Essa contagem mede "
        "etapas do procedimento, não tempo humano nem facilidade percebida.",
        "",
        "## Limitações",
        "",
        "- Uma execução de completude por consulta; os resultados das fontes mudam com o tempo.",
        "- O total é estimado pela soma informada pelas fontes e pode conter duplicatas.",
        "- A primeira página não representa todo o conjunto recuperado.",
        "- O cenário não mede satisfação, compreensão, carga cognitiva nem desempenho de pessoas.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--queries", type=Path, default=MEDICAO / "consultas.txt")
    parser.add_argument("--out-dir", type=Path, default=MEDICAO)
    args = parser.parse_args()
    queries = load_queries(args.queries)
    analyses: list[dict[str, Any]] = []
    with httpx.Client(base_url=args.base_url, timeout=90) as client:
        for query in queries:
            started = time.perf_counter()
            response = client.get("/api/v1/search", params={"q": query, "page_size": 20})
            elapsed = (time.perf_counter() - started) * 1000
            response.raise_for_status()
            analyses.append(analyze_response(query, elapsed, response.json()))
    day = date.today()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.out_dir / f"analise-resultados-{day:%Y%m%d}"
    stem.with_suffix(".json").write_text(
        json.dumps(analyses, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    stem.with_suffix(".md").write_text(to_markdown(analyses, day), encoding="utf-8")
    print(f"{len(analyses)} consultas analisadas; saída em {stem}.*")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
