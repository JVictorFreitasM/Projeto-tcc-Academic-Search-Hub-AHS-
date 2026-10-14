"""scripts/backup_db.sh (OS-037), com um `pg_dump` falso: sem banco, sem rede.

O que se prova aqui é o comportamento do script (arquivo gerado, nome com data, retenção, senha
fora da linha de comando, falhas sem arquivo parcial). A cópia e a restauração de um banco de
verdade são verificadas à mão e registradas em docs/evidencias/os-037/.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "backup_db.sh"
DUMP_NAME = re.compile(r"^academic_search-\d{8}-\d{6}\.dump$")

FAKE_PG_DUMP = """#!/bin/sh
{ echo "ARGS: $*"; echo "PGPASSWORD=$PGPASSWORD"; } >> "$STUB_LOG"
for a in "$@"; do case "$a" in --file=*) out="${a#--file=}";; esac; done
if [ "${STUB_EMPTY:-0}" = "1" ]; then : > "$out"; exit 0; fi
if [ "${STUB_FAIL:-0}" = "1" ]; then echo parcial > "$out"; exit 1; fi
echo conteudo-do-dump > "$out"
"""


def find_bash() -> str | None:
    """No Windows, `bash` do PATH costuma ser o do WSL: usa o Git Bash, se existir."""
    if sys.platform == "win32":
        for candidate in (
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files (x86)\Git\bin\bash.exe",
        ):
            if Path(candidate).exists():
                return candidate
        return None
    from shutil import which

    return which("bash")


BASH = find_bash()
needs_bash = pytest.mark.skipif(BASH is None, reason="bash não encontrado")


class Runner:
    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.stub_dir = tmp / "stub"
        self.stub_dir.mkdir()
        (self.stub_dir / "pg_dump").write_bytes(FAKE_PG_DUMP.encode())
        self.log = tmp / "pg_dump.log"
        self.backups = tmp / "backups"

    def run(
        self,
        url: str | None = "postgresql+psycopg://app_user:s3cr3t@127.0.0.1:5434/academic_search",
        **extra: str,
    ) -> subprocess.CompletedProcess[str]:
        env = {
            **os.environ,
            "PATH": f"{self.stub_dir}{os.pathsep}{os.environ['PATH']}",
            "STUB_LOG": self.log.as_posix(),
            "BACKUP_DIR": self.backups.as_posix(),
            **extra,
        }
        env.pop("DATABASE_URL", None)
        if url is not None:
            env["DATABASE_URL"] = url
        assert BASH is not None
        return subprocess.run(  # noqa: S603
            [BASH, SCRIPT.as_posix()],
            cwd=self.tmp, env=env, capture_output=True, text=True, encoding="utf-8", check=False,
        )  # fmt: skip

    def dumps(self) -> list[str]:
        return sorted(p.name for p in self.backups.glob("*")) if self.backups.exists() else []

    def calls(self) -> str:
        return self.log.read_text(encoding="utf-8") if self.log.exists() else ""


@pytest.fixture
def runner(tmp_path: Path) -> Runner:
    return Runner(tmp_path)


def test_script_has_a_shebang_and_unix_line_endings() -> None:
    data = SCRIPT.read_bytes()
    assert data.startswith(b"#!/usr/bin/env bash\n")
    assert b"\r\n" not in data


@needs_bash
def test_creates_one_dated_dump_and_no_partial_file(runner: Runner) -> None:
    result = runner.run()
    assert result.returncode == 0, result.stderr
    names = runner.dumps()
    assert len(names) == 1 and DUMP_NAME.match(names[0]), names
    assert (runner.backups / names[0]).read_text().strip() == "conteudo-do-dump"
    assert "gerado" in result.stdout and "1 cópia(s) mantida(s)" in result.stdout


@needs_bash
def test_keeps_only_the_seven_newest_by_default(runner: Runner) -> None:
    runner.backups.mkdir()
    for day in range(1, 10):  # nove cópias antigas, de 01 a 09 de janeiro
        (runner.backups / f"academic_search-202601{day:02d}-030000.dump").write_text("antiga")
    (runner.backups / "outro-arquivo.txt").write_text("não é cópia: não pode ser apagado")
    result = runner.run()
    assert result.returncode == 0, result.stderr
    dumps = [n for n in runner.dumps() if n.endswith(".dump")]
    assert len(dumps) == 7
    assert dumps[-1].startswith("academic_search-2026") and dumps[-1] > "academic_search-20260109"
    # 9 antigas + 1 nova = 10; ficam as 7 mais recentes, saem as 3 mais antigas
    for removed in ("20260101", "20260102", "20260103"):
        assert f"academic_search-{removed}-030000.dump" not in dumps
    for kept in ("20260104", "20260109"):
        assert f"academic_search-{kept}-030000.dump" in dumps
    assert "outro-arquivo.txt" in runner.dumps()


@needs_bash
def test_retention_works_in_a_directory_with_spaces_and_glob_characters(runner: Runner) -> None:
    """Regressão: o caminho não pode ser tratado como curinga (achado no teste real, no Windows)."""
    runner.backups = runner.tmp / "cópias [diárias] x"  # sem * e ?, que o Windows não aceita
    runner.backups.mkdir()
    for day in range(1, 9):
        (runner.backups / f"academic_search-202601{day:02d}-030000.dump").write_text("antiga")
    result = runner.run()
    assert result.returncode == 0, result.stderr
    dumps = [n for n in runner.dumps() if n.endswith(".dump")]
    assert len(dumps) == 7 and "academic_search-20260101-030000.dump" not in dumps
    assert "7 cópia(s) mantida(s)" in result.stdout


@needs_bash
def test_exit_code_is_zero_when_the_first_backup_is_the_only_file(runner: Runner) -> None:
    result = runner.run()
    assert result.returncode == 0 and "1 cópia(s) mantida(s)" in result.stdout


@needs_bash
def test_backup_keep_is_configurable(runner: Runner) -> None:
    runner.backups.mkdir()
    for day in range(1, 5):
        (runner.backups / f"academic_search-202601{day:02d}-030000.dump").write_text("antiga")
    assert runner.run(BACKUP_KEEP="2").returncode == 0
    assert len([n for n in runner.dumps() if n.endswith(".dump")]) == 2


@needs_bash
def test_password_goes_in_the_environment_never_on_the_command_line(runner: Runner) -> None:
    assert runner.run().returncode == 0
    calls = runner.calls()
    args = next(line for line in calls.splitlines() if line.startswith("ARGS:"))
    assert "s3cr3t" not in args
    assert "PGPASSWORD=s3cr3t" in calls
    for expected in (
        "--host=127.0.0.1", "--port=5434", "--username=app_user", "--dbname=academic_search",
        "--format=custom",
    ):  # fmt: skip
        assert expected in args


@needs_bash
def test_url_encoded_password_and_default_port_and_plain_postgresql_scheme(runner: Runner) -> None:
    assert runner.run(url="postgresql://u%40x:p%40ss%23w@db.exemplo.org/banco").returncode == 0
    calls = runner.calls()
    assert "PGPASSWORD=p@ss#w" in calls
    assert "--username=u@x" in calls and "--port=5432" in calls and "--host=db.exemplo.org" in calls


@needs_bash
def test_reads_the_env_file_without_executing_it(runner: Runner) -> None:
    (runner.tmp / ".env").write_text(
        'OUTRA=$(touch executado.txt)\nDATABASE_URL="postgresql+psycopg://u:pw@h:5433/d"\n',
        encoding="utf-8",
    )
    assert runner.run(url=None).returncode == 0
    assert "--port=5433" in runner.calls()
    assert not (runner.tmp / "executado.txt").exists()


@needs_bash
def test_environment_variable_wins_over_the_env_file(runner: Runner) -> None:
    (runner.tmp / ".env").write_text("DATABASE_URL=postgresql://a:b@arquivo:1111/x\n")
    assert runner.run(url="postgresql://a:b@ambiente:2222/x").returncode == 0
    assert "--host=ambiente" in runner.calls() and "arquivo" not in runner.calls()


@needs_bash
@pytest.mark.parametrize(
    ("url", "extra", "message"),
    [
        (None, {}, "DATABASE_URL não definida"),
        ("mysql://u:p@h/d", {}, "formato não reconhecido"),
        ("postgresql://u:p@h/d", {"BACKUP_KEEP": "0"}, "BACKUP_KEEP"),
        ("postgresql://u:p@h/d", {"BACKUP_KEEP": "sete"}, "BACKUP_KEEP"),
    ],
)
def test_bad_configuration_exits_with_2_and_creates_nothing(
    runner: Runner, url: str | None, extra: dict[str, str], message: str
) -> None:
    result = runner.run(url=url, **extra)
    assert result.returncode == 2 and message in result.stderr
    assert runner.dumps() == [] and runner.calls() == ""


@needs_bash
def test_a_failing_pg_dump_leaves_no_file_behind(runner: Runner) -> None:
    runner.backups.mkdir()
    (runner.backups / "academic_search-20260101-030000.dump").write_text("antiga")
    result = runner.run(STUB_FAIL="1")
    assert result.returncode == 1 and "pg_dump falhou" in result.stderr
    assert runner.dumps() == ["academic_search-20260101-030000.dump"]  # nada novo, nada apagado


@needs_bash
def test_an_empty_dump_is_refused(runner: Runner) -> None:
    result = runner.run(STUB_EMPTY="1")
    assert result.returncode == 1 and "vazia" in result.stderr
    assert runner.dumps() == []


@needs_bash
@pytest.mark.skipif(sys.platform == "win32", reason="permissões POSIX")
def test_dump_and_directory_are_private_to_the_owner(runner: Runner) -> None:
    assert runner.run().returncode == 0
    assert oct(runner.backups.stat().st_mode & 0o777) == "0o700"
    dump = next(runner.backups.glob("*.dump"))
    assert oct(dump.stat().st_mode & 0o777) == "0o600"
