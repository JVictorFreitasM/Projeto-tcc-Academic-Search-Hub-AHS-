"""Testes dos instrumentos de medição (OS-033), só com dados falsos e sem rede.

Os números abaixo são fictícios, escolhidos para conferir a aritmética dos scripts. Eles não são
medições e não podem ser citados como resultado.
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from datetime import date
from pathlib import Path
from types import ModuleType
from typing import Any

import httpx
import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]


def load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def ms() -> ModuleType:
    return load("measure_search")


@pytest.fixture(scope="module")
def sm() -> ModuleType:
    return load("summarize_manual")


def fake_body(
    results: int = 5, a_count: int = 3, b_count: int = 3, b_status: str = "ok"
) -> dict[str, Any]:
    return {
        "query": "x",
        "results": [{"id": str(i)} for i in range(results)],
        "sources_status": {
            "openalex": {"status": "ok", "count": a_count, "total": 100, "duration_ms": 120},
            "core": {"status": b_status, "count": b_count, "total": 50, "duration_ms": 300},
        },
    }


def client_returning(handler: Any) -> httpx.Client:
    return httpx.Client(base_url="http://app.test", transport=httpx.MockTransport(handler))


# ---------- measure_search ----------


def test_load_queries_skips_comments_and_blank_lines(ms: ModuleType, tmp_path: Path) -> None:
    path = tmp_path / "q.txt"
    path.write_text("# comentário\n\n  consulta um \nconsulta dois\n   # outro\n", encoding="utf-8")
    assert ms.load_queries(path) == ["consulta um", "consulta dois"]


def test_load_queries_refuses_an_empty_file(ms: ModuleType, tmp_path: Path) -> None:
    path = tmp_path / "q.txt"
    path.write_text("# só comentários\n", encoding="utf-8")
    with pytest.raises(ms.NoQueriesError, match="nenhuma consulta"):
        ms.load_queries(path)


def test_shipped_queries_file_contains_the_documented_scenario() -> None:
    """As consultas distribuídas são exatamente as usadas no cenário documentado."""
    module = load("measure_search")
    assert module.load_queries(
        ROOT / "docs" / "evidencias" / "medicao" / "consultas.txt"
    ) == [
        "letramento digital",
        "acessibilidade web",
        "segurança em aplicações web",
        "repositórios institucionais",
        "educação a distância",
    ]


def test_duplicates_merged_is_only_computed_when_nothing_was_truncated(ms: ModuleType) -> None:
    status = fake_body()["sources_status"]  # 3 + 3 = 6 registros
    assert ms.duplicates_merged(status, shown=5, page_size=20) == 1
    assert ms.duplicates_merged(status, shown=6, page_size=20) == 0
    assert ms.duplicates_merged(status, shown=5, page_size=5) is None  # 6 > 5: houve corte


def test_rows_from_response_has_one_row_per_source(ms: ModuleType) -> None:
    rows = ms.rows_from_response("q", 2, 123.456, 200, fake_body(), page_size=20)
    assert [r["fonte"] for r in rows] == ["core", "openalex"]
    core = rows[0]
    assert core["consulta"] == "q" and core["execucao"] == 2 and core["tempo_total_ms"] == 123.5
    assert core["resultados_exibidos"] == 5 and core["registros_das_fontes"] == 6
    assert core["duplicatas_fundidas"] == 1 and core["fonte_duracao_ms"] == 300


def test_rows_from_response_records_failed_sources_and_http_errors(ms: ModuleType) -> None:
    rows = ms.rows_from_response("q", 1, 10, 200, fake_body(b_status="timeout", b_count=0), 20)
    assert {r["fonte"]: r["status_da_fonte"] for r in rows} == {"core": "timeout", "openalex": "ok"}
    error = ms.rows_from_response("q", 1, 10, 502, {"error": {"code": "all_failed"}}, 20)
    assert len(error) == 1 and error[0]["status_da_fonte"] == "http_502"
    assert error[0]["fonte"] == "(aplicação)"


def test_measure_runs_every_query_the_requested_number_of_times(ms: ModuleType) -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.url.params["q"], request.url.params["page_size"]))
        return httpx.Response(200, json=fake_body())

    with client_returning(handler) as client:
        rows = ms.measure(client, ["alfa", "beta"], runs=3, page_size=20)
    assert seen == [("alfa", "20")] * 3 + [("beta", "20")] * 3
    assert len(rows) == 2 * 3 * 2  # consultas x execuções x fontes
    assert all(r["tempo_total_ms"] >= 0 for r in rows)


def test_measure_records_connection_failures_without_crashing(ms: ModuleType) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sem conexão", request=request)

    with client_returning(handler) as client:
        rows = ms.measure(client, ["alfa"], runs=2)
    assert [r["status_da_fonte"] for r in rows] == ["http_0", "http_0"]


def test_write_csv_is_excel_friendly_and_round_trips(ms: ModuleType, tmp_path: Path) -> None:
    rows = ms.rows_from_response("avaliação", 1, 50, 200, fake_body(), 20)
    path = tmp_path / "out" / "r.csv"
    ms.write_csv(rows, path)
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")  # BOM: o Excel reconhece os acentos
    with path.open(encoding="utf-8-sig", newline="") as handle:
        read = list(csv.DictReader(handle, delimiter=";"))
    assert list(read[0]) == ms.FIELDS
    assert read[0]["consulta"] == "avaliação" and read[0]["fonte"] == "core"


def test_summarize_reports_only_numbers_computed_from_the_rows(ms: ModuleType) -> None:
    rows: list[dict[str, Any]] = []
    for run, total in enumerate((100.0, 200.0, 300.0), start=1):
        rows += ms.rows_from_response("alfa", run, total, 200, fake_body(), 20)
    rows += ms.rows_from_response(
        "beta", 1, 50.0, 200, fake_body(b_status="timeout", b_count=0), 20
    )
    text = ms.summarize(rows, date(2026, 10, 14))
    assert "14/10/2026" in text
    assert "| alfa | 3 | média 200 ms · mín 100 · máx 300 | 5.0 | 3 (em 3 de 3 execuções) |" in text
    assert "| core | 4 | 1 | média 300 ms · mín 300 · máx 300 |" in text
    assert "| openalex | 4 | 0 | média 120 ms · mín 120 · máx 120 |" in text
    assert "- core: timeout" in text


def test_summarize_with_no_failures_says_so(ms: ModuleType) -> None:
    rows = ms.rows_from_response("alfa", 1, 10.0, 200, fake_body(), 20)
    assert "- nenhuma nas execuções medidas" in ms.summarize(rows, date(2026, 10, 14))


def test_main_writes_csv_and_markdown_from_the_run(
    ms: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    queries = tmp_path / "q.txt"
    queries.write_text("alfa\nbeta\n", encoding="utf-8")
    real_client = httpx.Client

    def factory(**kwargs: Any) -> httpx.Client:
        handler = lambda request: httpx.Response(200, json=fake_body())  # noqa: E731
        return real_client(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(ms.httpx, "Client", factory)
    code = ms.main(["--queries", str(queries), "--runs", "2", "--out-dir", str(tmp_path / "o")])
    assert code == 0
    stem = f"resultado-{date.today():%Y%m%d}"
    assert (tmp_path / "o" / f"{stem}.csv").exists()
    assert "## Por fonte" in (tmp_path / "o" / f"{stem}.md").read_text(encoding="utf-8")


def test_main_exits_with_error_when_there_are_no_queries(
    ms: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    queries = tmp_path / "q.txt"
    queries.write_text("# vazio\n", encoding="utf-8")
    assert ms.main(["--queries", str(queries), "--out-dir", str(tmp_path)]) == 2
    assert "nenhuma consulta" in capsys.readouterr().err


# ---------- summarize_manual ----------


@pytest.mark.parametrize(
    ("text", "seconds"),
    [("95", 95.0), ("95,5", 95.5), ("1:35", 95.0), ("0:01:35", 95.0), ("1:01:01", 3661.0)],
)
def test_parse_seconds_accepts_seconds_and_clock_formats(
    sm: ModuleType, text: str, seconds: float
) -> None:
    assert sm.parse_seconds(text) == seconds


@pytest.mark.parametrize("text", ["abc", "1:2:3:4", "1::"])
def test_parse_seconds_rejects_garbage(sm: ModuleType, text: str) -> None:
    with pytest.raises(ValueError, match=r".*"):
        sm.parse_seconds(text)


SHEET = (
    "consulta,metodo,pessoa,tempo,resultados_uteis,observacoes\n"
    "alfa,manual,P1,2:00,10,\n"
    "alfa,manual,P2,180,12,\n"
    "alfa,aplicacao,P1,0:30,15,\n"
    "alfa,aplicação,P2,50,17,\n"
    "beta,manual,P1,,,ainda não feita\n"
)


def write_sheet(tmp_path: Path, text: str = SHEET) -> Path:
    path = tmp_path / "planilha.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_read_sheet_counts_measures_and_empty_rows(sm: ModuleType, tmp_path: Path) -> None:
    measures, empty = sm.read_sheet(write_sheet(tmp_path))
    assert empty == 1
    assert [(m[0], m[1], m[2], m[3]) for m in measures] == [
        ("alfa", "manual", 120.0, 10.0),
        ("alfa", "manual", 180.0, 12.0),
        ("alfa", "aplicação", 30.0, 15.0),
        ("alfa", "aplicação", 50.0, 17.0),
    ]


def test_read_sheet_accepts_excel_semicolons_and_bom(sm: ModuleType, tmp_path: Path) -> None:
    text = "﻿" + SHEET.replace(",", ";").replace("95;5", "95,5")
    measures, _ = sm.read_sheet(write_sheet(tmp_path, text))
    assert len(measures) == 4


def test_summarize_gives_mean_min_max_by_method_and_query(sm: ModuleType, tmp_path: Path) -> None:
    measures, empty = sm.read_sheet(write_sheet(tmp_path))
    text = sm.summarize(measures, empty)
    # manual: 120 e 180 s  -> média 150, mínimo 120, máximo 180; resultados úteis (10+12)/2 = 11
    assert "| manual | 2 | 2:30 (150.0 s) | 2:00 (120.0 s) | 3:00 (180.0 s) | 11.0 |" in text
    # aplicação: 30 e 50 s -> média 40; úteis (15+17)/2 = 16
    assert "| aplicação | 2 | 0:40 (40.0 s) | 0:30 (30.0 s) | 0:50 (50.0 s) | 16.0 |" in text
    assert "| alfa · manual | 2 |" in text and "| alfa · aplicação | 2 |" in text
    assert "Medições usadas: 4. Linhas sem tempo, ignoradas: 1." in text


def test_summary_never_states_a_comparison_or_a_percentage(sm: ModuleType, tmp_path: Path) -> None:
    measures, empty = sm.read_sheet(write_sheet(tmp_path))
    text = sm.summarize(measures, empty).lower()
    assert "%" not in text and "reduz" not in text and "mais rápid" not in text


def test_empty_sheet_produces_no_numbers(sm: ModuleType, tmp_path: Path) -> None:
    header = "consulta,metodo,pessoa,tempo,resultados_uteis,observacoes\nalfa,manual,P1,,,\n"
    measures, empty = sm.read_sheet(write_sheet(tmp_path, header))
    text = sm.summarize(measures, empty)
    assert "Nenhuma medição preenchida" in text and "(1 linhas sem tempo)" in text
    assert "Média" not in text


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("consulta,metodo\nalfa,manual\n", "colunas ausentes"),
        ("consulta,metodo,tempo\nalfa,robo,10\n", "linha 2: método"),
        ("consulta,metodo,tempo\nalfa,manual,dez\n", "linha 2: tempo inválido"),
        ("consulta,metodo,tempo\nalfa,manual,-5\n", "tempo negativo"),
        ("consulta,metodo,tempo,resultados_uteis\nalfa,manual,10,x\n", "resultados_uteis inválido"),
    ],
)
def test_read_sheet_reports_bad_input_with_the_line(
    sm: ModuleType, tmp_path: Path, text: str, message: str
) -> None:
    with pytest.raises(sm.SheetError, match=message):
        sm.read_sheet(write_sheet(tmp_path, text))


def test_main_prints_and_writes_the_summary_and_fails_cleanly(
    sm: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "resumo.md"
    assert sm.main([str(write_sheet(tmp_path)), "--out", str(out)]) == 0
    assert "# Resumo da medição manual" in capsys.readouterr().out
    assert out.read_text(encoding="utf-8").startswith("# Resumo da medição manual")
    assert sm.main([str(tmp_path / "nao-existe.csv")]) == 2
    assert "erro:" in capsys.readouterr().err
