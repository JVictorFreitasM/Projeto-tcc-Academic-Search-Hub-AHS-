from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI, Request

from app import main as main_module
from app.core.config import Settings, get_settings
from app.core.rate_limit import limiter
from app.db import session as db_session
from app.main import create_app

pytestmark = pytest.mark.integration

ORIGIN = "http://localhost:8000"
STRONG = "k" * 40


def settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


def client_for(app: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    async with client_for(create_app(settings())) as c:
        yield c


@pytest.fixture
def fresh_db_cache() -> Iterator[None]:
    get_settings.cache_clear()
    db_session.get_engine.cache_clear()
    yield
    get_settings.cache_clear()
    db_session.get_engine.cache_clear()


async def test_health_with_database_ok(
    client: httpx.AsyncClient,
    migrated_db_url: str,
    monkeypatch: pytest.MonkeyPatch,
    fresh_db_cache: None,
) -> None:
    monkeypatch.setenv("DATABASE_URL", migrated_db_url)
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok" and body["database"] == "ok" and body["version"]
    await db_session.get_engine().dispose()


async def test_health_with_database_down_has_no_details(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch, fresh_db_cache: None
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:senha@127.0.0.1:1/nada")
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["database"] == "error"
    assert "senha" not in response.text and "Traceback" not in response.text
    assert "127.0.0.1" not in response.text
    await db_session.get_engine().dispose()


async def test_openapi_document(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/openapi.json")
    assert response.status_code == 200
    doc = response.json()
    assert doc["openapi"].startswith("3.")
    assert doc["info"]["title"] and doc["info"]["version"] and doc["info"]["description"]
    assert doc["servers"]
    assert "/api/v1/health" in doc["paths"]
    assert doc["components"]["securitySchemes"]["bearerAuth"]["scheme"] == "bearer"
    responses = doc["paths"]["/api/v1/health"]["get"]["responses"]
    assert {"200", "422", "429", "500"} <= set(responses)
    ref = responses["500"]["content"]["application/json"]["schema"]["$ref"]
    assert ref.endswith("/ErrorResponse")
    assert "ErrorResponse" in doc["components"]["schemas"]


async def test_docs_page_opens(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "swagger" in response.text.lower()


async def test_docs_can_be_turned_off() -> None:
    async with client_for(create_app(settings(docs_enabled=False))) as c:
        assert (await c.get("/api/docs")).status_code == 404
        assert (await c.get("/api/openapi.json")).status_code == 404
        assert (await c.get("/api/v1/health")).status_code == 200


async def test_cors_allowed_origin_gets_header(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/health", headers={"Origin": ORIGIN})
    assert response.headers["access-control-allow-origin"] == ORIGIN


async def test_cors_foreign_origin_gets_no_header(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/health", headers={"Origin": "https://malicioso.example"})
    assert "access-control-allow-origin" not in response.headers


async def test_cors_preflight_methods_and_headers(client: httpx.AsyncClient) -> None:
    response = await client.options(
        "/api/v1/health",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "DELETE",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert "DELETE" in response.headers["access-control-allow-methods"]
    foreign = await client.options(
        "/api/v1/health",
        headers={"Origin": "https://malicioso.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in foreign.headers


EXPECTED_CSP = (
    "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
    "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)


@pytest.mark.parametrize("path", ["/api/v1/health", "/api/v1/nao-existe", "/nao-existe"])
async def test_security_headers_on_every_response(client: httpx.AsyncClient, path: str) -> None:
    headers = (await client.get(path)).headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "no-referrer"
    assert "camera=()" in headers["permissions-policy"]
    assert headers["content-security-policy"] == EXPECTED_CSP
    assert "unsafe-inline" not in headers["content-security-policy"]
    assert "strict-transport-security" not in headers  # só em produção


async def test_hsts_only_in_production() -> None:
    prod = settings(app_env="production", secret_key=STRONG, allowed_origins="https://a.org")
    async with client_for(create_app(prod)) as c:
        headers = (await c.get("/api/v1/health")).headers
    assert headers["strict-transport-security"].startswith("max-age=")


async def test_docs_page_has_its_own_csp_with_hash_but_api_keeps_the_strict_one(
    client: httpx.AsyncClient,
) -> None:
    docs = (await client.get("/api/docs")).headers["content-security-policy"]
    assert "'sha256-" in docs and "cdn.jsdelivr.net" in docs
    assert "frame-ancestors 'none'" in docs
    assert (await client.get("/api/v1/health")).headers["content-security-policy"] == EXPECTED_CSP


async def test_request_id_header(client: httpx.AsyncClient) -> None:
    first = await client.get("/api/v1/health")
    assert (
        first.headers["x-request-id"]
        != (await client.get("/api/v1/health")).headers["x-request-id"]
    )


async def test_unknown_api_route_uses_standard_error(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/nao-existe")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_static_frontend_is_served_after_api_routes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "index.html").write_text("<!doctype html><title>Início</title>", encoding="utf-8")
    monkeypatch.setattr(main_module, "FRONTEND_DIR", tmp_path)
    async with client_for(create_app(settings())) as c:
        page = await c.get("/")
        assert page.status_code == 200 and "Início" in page.text
        assert page.headers["content-security-policy"] == EXPECTED_CSP
        assert (await c.get("/api/v1/health")).json()["status"] == "ok"  # a API vence o estático


async def test_rate_limit_returns_429_in_standard_format(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # sem o mount estático em "/", que capturaria rotas adicionadas depois da criação
    monkeypatch.setattr(main_module, "FRONTEND_DIR", tmp_path / "inexistente")
    app = create_app(settings())

    def no_database() -> None:
        raise RuntimeError("sem banco neste teste")

    app.state.session_factory = no_database  # o evento rate_limited não deve sujar o banco

    @app.get("/limitado")
    @limiter.limit("2/minute")
    async def limited(request: Request) -> dict[str, str]:
        return {"ok": "sim"}

    limiter.reset()
    async with client_for(app) as c:
        assert (await c.get("/limitado")).status_code == 200
        assert (await c.get("/limitado")).status_code == 200
        blocked = await c.get("/limitado")
    limiter.reset()
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"
    assert blocked.headers["retry-after"] == "60" and blocked.headers["x-request-id"]


def test_module_attribute_app_is_created_lazily() -> None:
    app = main_module.app  # type: ignore[attr-defined]
    assert isinstance(app, FastAPI)
    with pytest.raises(AttributeError):
        _ = main_module.inexistente  # type: ignore[attr-defined]


def test_cors_never_allows_wildcard_in_production() -> None:
    with pytest.raises(ValueError, match="ALLOWED_ORIGINS"):
        settings(app_env="production", secret_key=STRONG, allowed_origins="*")
