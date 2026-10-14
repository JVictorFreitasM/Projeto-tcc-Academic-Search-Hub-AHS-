"""Arquivos de implantação (OS-037): sem segredos e coerentes com as decisões do projeto."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy"
FILES = sorted(p for p in DEPLOY.iterdir() if p.is_file())


def text(name: str) -> str:
    return (DEPLOY / name).read_text(encoding="utf-8")


def test_the_expected_deploy_files_exist() -> None:
    names = {p.name for p in FILES}
    assert {
        "academic-search.service",
        "academic-search.env.example",
        "nginx.conf.example",
        "Caddyfile.example",
        "crontab.example",
    } <= names


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_no_file_has_windows_line_endings_or_a_long_random_looking_token(path: Path) -> None:
    data = path.read_bytes()
    assert b"\r\n" not in data
    content = data.decode("utf-8")
    # um segredo costuma ser uma sequência longa de letras e números sem significado
    tokens = [
        t for t in re.findall(r"[A-Za-z0-9_\-]{32,}", content) if not re.fullmatch(r"[a-z\-]+", t)
    ]
    assert tokens == [], tokens


def test_env_example_has_no_secret_values() -> None:
    values = dict(
        line.split("=", 1)
        for line in text("academic-search.env.example").splitlines()
        if line and not line.startswith("#") and "=" in line
    )
    for key in ("SECRET_KEY", "OPENALEX_API_KEY", "CORE_API_KEY", "CONTACT_EMAIL"):
        assert values[key] == "", f"{key} deve vir vazio no modelo"
    assert "TROCAR" in values["DATABASE_URL"]  # senha de marcação, não a de verdade
    assert values["APP_ENV"] == "production"
    assert "*" not in values["ALLOWED_ORIGINS"]
    assert values["ALLOWED_ORIGINS"].startswith("https://")


def test_service_runs_one_unprivileged_process_with_an_environment_file() -> None:
    unit = text("academic-search.service")
    assert re.search(r"^EnvironmentFile=/etc/", unit, re.MULTILINE)
    assert re.search(r"^Restart=on-failure$", unit, re.MULTILINE)
    assert re.search(r"^User=(?!root\b)\S+", unit, re.MULTILINE)
    assert re.search(r"^ExecStart=.*-m app\.run$", unit, re.MULTILINE)
    assert "--workers" not in unit  # limite de requisições em memória: um processo só
    assert not re.search(r"^Environment=.*(SECRET|PASSWORD|KEY)", unit, re.MULTILINE)
    assert "NoNewPrivileges=true" in unit


@pytest.mark.parametrize("name", ["nginx.conf.example", "Caddyfile.example"])
def test_proxy_examples_forward_to_the_app_and_do_not_add_security_headers(name: str) -> None:
    config = text(name)
    assert "127.0.0.1:8000" in config
    # os cabeçalhos de segurança vêm da aplicação; repeti-los aqui os duplicaria
    directives = [ln for ln in config.splitlines() if not ln.lstrip().startswith("#")]
    assert not any(re.search(r"\badd_header\b|\bheader\b", ln) for ln in directives)


def test_nginx_redirects_http_to_https_and_does_not_forward_a_client_forged_ip() -> None:
    config = text("nginx.conf.example")
    assert "return 301 https://$host$request_uri;" in config
    assert "proxy_set_header X-Forwarded-For   $remote_addr;" in config
    assert "$proxy_add_x_forwarded_for" not in config
    assert "ssl_protocols       TLSv1.2 TLSv1.3;" in config


def test_crontab_runs_a_daily_incremental_harvest_and_a_backup_without_secrets() -> None:
    cron = text("crontab.example")
    jobs = [ln for ln in cron.splitlines() if ln and not ln.startswith(("#", " ")) and "* *" in ln]
    harvest = next(j for j in jobs if "app.harvest.cli run-all" in j)
    assert harvest.startswith("0 3 * * * ")  # uma vez por dia
    assert "flock -n" in harvest and ">> /var/log/academic-search/colheita.log 2>&1" in harvest
    assert any("scripts/backup_db.sh" in j for j in jobs)
    assert any("app.cli_security purge" in j for j in jobs)
    assert "SECRET_KEY" not in cron and "PASSWORD" not in cron
