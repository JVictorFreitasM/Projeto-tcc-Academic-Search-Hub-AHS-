from collections.abc import Iterator
from pathlib import Path

import pytest
import respx
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.db import session as db_session
from app.harvest.cli import main
from tests.oai_support import OAI_URL, oai_server

pytestmark = pytest.mark.integration

SOURCES = """
sources:
  - slug: exemplo
    name: Exemplo
    base_url: https://oai.exemplo.org/oai
    enabled: true
    default_type: thesis
  - slug: parada
    name: Parada
    base_url: TODO-VERIFICAR
    enabled: false
"""


@pytest.fixture
def env(tmp_path: Path, migrated_db_url: str, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    file = tmp_path / "fontes.yml"
    file.write_text(SOURCES, encoding="utf-8")
    monkeypatch.setenv("DATABASE_URL", migrated_db_url)
    monkeypatch.setenv("OAI_SOURCES_FILE", str(file))
    monkeypatch.setenv("CONTACT_EMAIL", "dev@exemplo.com")
    monkeypatch.setenv("OAI_HARVEST_DELAY_SECONDS", "0")
    get_settings.cache_clear()
    db_session.get_engine.cache_clear()
    db_session.get_sessionmaker.cache_clear()
    sync_url = migrated_db_url.replace("postgresql+psycopg", "postgresql+psycopg")
    engine = create_engine(sync_url)

    def clean() -> None:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM oai_records WHERE source = 'exemplo'"))
            conn.execute(text("DELETE FROM harvest_runs WHERE source = 'exemplo'"))

    clean()
    yield
    clean()
    engine.dispose()
    get_settings.cache_clear()
    db_session.get_engine.cache_clear()
    db_session.get_sessionmaker.cache_clear()


@respx.mock
def test_run_then_status_shows_counts(env: None, capsys: pytest.CaptureFixture[str]) -> None:
    respx.get(OAI_URL).mock(side_effect=oai_server)
    assert main(["run", "exemplo", "--full"]) == 0
    out = capsys.readouterr().out
    assert "exemplo: partial" in out and "lidos=4" in out and "gravados=3" in out

    assert main(["status"]) == 0
    status = capsys.readouterr().out
    assert "exemplo (habilitada): 3 registros" in status
    assert "partial" in status
    assert "parada (desabilitada): 0 registros | nenhuma colheita" in status


@respx.mock
def test_dry_run_prints_samples_and_writes_nothing(
    env: None, capsys: pytest.CaptureFixture[str]
) -> None:
    respx.get(OAI_URL).mock(side_effect=oai_server)
    assert main(["run", "exemplo", "--dry-run", "--limit", "2"]) == 0
    out = capsys.readouterr().out
    assert "simulação" in out and "exemplo:" in out
    assert main(["status"]) == 0
    assert "exemplo (habilitada): 0 registros" in capsys.readouterr().out


@respx.mock
def test_identify_and_sets(env: None, capsys: pytest.CaptureFixture[str]) -> None:
    respx.get(OAI_URL).mock(side_effect=oai_server)
    assert main(["identify", "exemplo"]) == 0
    assert "Repositório de Exemplo" in capsys.readouterr().out
    assert main(["sets", "exemplo"]) == 0
    assert "teses\tTeses" in capsys.readouterr().out


@respx.mock
def test_dump_saves_raw_files(
    env: None, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    respx.get(OAI_URL).mock(side_effect=oai_server)
    out_dir = tmp_path / "dump"
    assert main(["dump", "exemplo", "--out", str(out_dir)]) == 0
    assert (out_dir / "identify.xml").read_bytes().startswith(b"<?xml")
    assert b"ListRecords" in (out_dir / "list_records.xml").read_bytes()
    capsys.readouterr()


def test_run_refuses_without_contact_email(
    env: None, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("CONTACT_EMAIL", "")
    get_settings.cache_clear()
    assert main(["run", "exemplo"]) == 1
    assert "CONTACT_EMAIL" in capsys.readouterr().err


def test_unknown_source_and_unconfigured_source(
    env: None, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["run", "naoexiste"]) == 2
    assert "não existe" in capsys.readouterr().err
    assert main(["identify", "parada"]) == 1
    assert "base_url" in capsys.readouterr().err


@respx.mock
def test_run_all_only_runs_enabled_sources(env: None, capsys: pytest.CaptureFixture[str]) -> None:
    respx.get(OAI_URL).mock(side_effect=oai_server)
    assert main(["run-all", "--full"]) == 0
    out = capsys.readouterr().out
    assert "exemplo:" in out and "parada" not in out


def test_run_exit_code_is_nonzero_on_error(env: None, capsys: pytest.CaptureFixture[str]) -> None:
    with respx.mock:
        respx.get(OAI_URL).mock(return_value=__import__("httpx").Response(404))
        assert main(["run", "exemplo", "--full"]) == 1
    assert "404" in capsys.readouterr().err
