import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.unit


def test_integration_tests_are_skipped_without_test_database_url() -> None:
    """Sem TEST_DATABASE_URL os testes de banco são pulados, não falham."""
    env = {**os.environ, "TEST_DATABASE_URL": "", "PYTHONUTF8": "1"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/test_db_connection.py",
            "-q",
            "--no-cov",
            "-rs",
        ],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 0, result.stdout
    assert "skipped" in result.stdout
    assert "TEST_DATABASE_URL não definida" in result.stdout
    assert "failed" not in result.stdout
