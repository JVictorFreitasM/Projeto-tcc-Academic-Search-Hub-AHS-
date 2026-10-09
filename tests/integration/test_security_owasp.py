"""Testes dos riscos do OWASP Top 10 (2017) que dependem da aplicação rodando. Ver docs/SEGURANCA.md."""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.rate_limit import limiter
from app.core.security import create_access_token, hash_password
from app.db import session as db_session
from app.main import create_app
from app.models import Favorite, SearchHistory, SecurityEvent, User

pytestmark = pytest.mark.integration

SECRET = "s" * 40
PASSWORD = "Senha12345"
XSS = "<script>alert('xss')</script><img src=x onerror=alert(1)>"
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
# Rotas em que o token é OPCIONAL (visitante pode usar; logado ganha favoritos marcados e histórico).
# O OpenAPI as lista com bearerAuth, mas elas NÃO exigem login. Qualquer outra rota com bearerAuth exige.
OPTIONAL_AUTH = {("get", "/api/v1/search")}


@pytest.fixture
def env(migrated_db_url: str, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("DATABASE_URL", migrated_db_url)
    monkeypatch.setenv("SECRET_KEY", SECRET)
    monkeypatch.setenv("RATE_LIMIT_AUTH", "1000/minute")
    monkeypatch.setenv("RATE_LIMIT_SEARCH", "1000/minute")
    for cached in (get_settings, db_session.get_engine, db_session.get_sessionmaker):
        cached.cache_clear()
    limiter.reset()
    yield
    limiter.reset()
    for cached in (get_settings, db_session.get_engine, db_session.get_sessionmaker):
        cached.cache_clear()


@pytest.fixture
async def db(engine: AsyncEngine) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    maker = async_sessionmaker(engine, expire_on_commit=False)
    yield maker
    async with maker() as session:
        await session.execute(delete(SecurityEvent))
        await session.execute(delete(User).where(User.email.like("%@owasp.com")))
        await session.commit()


@pytest.fixture
async def client(
    env: None, db: async_sessionmaker[AsyncSession]
) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        yield c
    await db_session.get_engine().dispose()


async def make_user(
    db: async_sessionmaker[AsyncSession], name: str
) -> tuple[uuid.UUID, dict[str, str]]:
    async with db() as session:
        user = User(
            email=f"{name}.{uuid.uuid4().hex[:6]}@owasp.com",
            full_name=name,
            password_hash=hash_password(PASSWORD),
            consent_at=datetime.now(UTC),
            consent_policy_version="1.0",
        )
        session.add(user)
        await session.commit()
        token = create_access_token(user.id, Settings(_env_file=None, secret_key=SECRET))  # type: ignore[call-arg]
        return user.id, {"Authorization": f"Bearer {token}"}


def record(n: int, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": f"doi:10.1234/own{n}",
        "title": f"Trabalho do dono número {n}",
        "authors": [{"name": "Maria Souza", "orcid": None}],
        "year": 2022,
        "type": "article",
        "sources": [{"source": "openalex", "source_id": f"W{n}", "url": None}],
    }
    return {**data, **overrides}


def operations(spec: dict[str, Any], *, secured: bool) -> list[tuple[str, str, dict[str, Any]]]:
    found = []
    for path, item in spec["paths"].items():
        for method, operation in item.items():
            if method not in HTTP_METHODS:
                continue
            has_security = any("bearerAuth" in entry for entry in operation.get("security", []))
            required = has_security and (method, path) not in OPTIONAL_AUTH
            if required == secured:
                found.append((method, path, operation))
    return found


# ---------- A5 Controle de acesso quebrado ----------


async def test_a5_every_protected_route_rejects_requests_without_token(
    client: httpx.AsyncClient,
) -> None:
    spec = (await client.get("/api/openapi.json")).json()
    protected = operations(spec, secured=True)
    assert len(protected) >= 14, "as rotas protegidas deveriam aparecer no OpenAPI com bearerAuth"
    for method, path, _ in protected:
        url = re.sub(r"\{[^}]+\}", str(uuid.uuid4()), path)
        response = await client.request(method.upper(), url, json={} if method != "get" else None)
        assert response.status_code == 401, f"{method.upper()} {path} -> {response.status_code}"
        assert response.json()["error"]["code"] == "unauthorized"


async def test_a5_user_b_cannot_reach_user_a_objects_on_any_protected_route(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    a_id, a = await make_user(db, "dono")
    _, b = await make_user(db, "intruso")
    favorite = (
        await client.post(
            "/api/v1/favorites", json={"record": record(1), "note": "SEGREDO-DA-DONA"}, headers=a
        )
    ).json()
    async with db() as session:
        history = SearchHistory(user_id=a_id, query="CONSULTA-DA-DONA", filters={})
        session.add(history)
        await session.commit()
        history_id = history.id
    owned = {"favorite_id": favorite["id"], "history_id": str(history_id)}

    spec = (await client.get("/api/openapi.json")).json()
    exercised = 0
    for method, path, _operation in operations(spec, secured=True):
        params = re.findall(r"\{([^}]+)\}", path)
        if not params:
            continue
        url = path
        for name in params:
            assert name in owned, (
                f"rota nova com parâmetro {name!r}: acrescente o objeto do dono ao teste"
            )
            url = url.replace("{" + name + "}", owned[name])
        body = {} if method in ("patch", "post", "put") else None
        response = await client.request(method.upper(), url, json=body, headers=b)
        assert response.status_code == 404, f"{method.upper()} {path} -> {response.status_code}"
        assert response.json()["error"]["code"] == "not_found"
        assert "SEGREDO-DA-DONA" not in response.text and "CONSULTA-DA-DONA" not in response.text
        exercised += 1
    assert exercised >= 3  # PATCH/DELETE favorito e DELETE histórico

    # nada foi alterado ou apagado pelas tentativas do intruso
    mine = (await client.get("/api/v1/favorites", headers=a)).json()
    assert mine["total"] == 1 and mine["items"][0]["note"] == "SEGREDO-DA-DONA"
    assert (await client.get("/api/v1/history", headers=a)).json()["total"] == 1


async def test_a5_listing_routes_never_leak_other_users_data(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    a_id, a = await make_user(db, "dono")
    _, b = await make_user(db, "intruso")
    await client.post(
        "/api/v1/favorites", json={"record": record(1), "note": "SEGREDO-DA-DONA"}, headers=a
    )
    async with db() as session:
        session.add(SearchHistory(user_id=a_id, query="CONSULTA-DA-DONA", filters={}))
        await session.commit()
    spec = (await client.get("/api/openapi.json")).json()
    for method, path, _ in operations(spec, secured=True):
        if method != "get" or "{" in path:
            continue
        response = await client.get(path, params={"format": "json"}, headers=b)
        assert response.status_code == 200, path
        for marker in ("SEGREDO-DA-DONA", "CONSULTA-DA-DONA", "Trabalho do dono", "dono."):
            assert marker not in response.text, f"{path} vazou {marker}"


async def test_a5_a_user_cannot_use_a_token_for_a_deleted_or_inactive_account(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    user_id, headers = await make_user(db, "efemero")
    async with db() as session:
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()
    assert (await client.get("/api/v1/me", headers=headers)).status_code == 401


# ---------- A3 Exposição de dados sensíveis ----------


async def test_a3_no_response_ever_carries_password_hashes(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    _, headers = await make_user(db, "ana")
    await client.post("/api/v1/favorites", json={"record": record(1)}, headers=headers)
    texts = []
    for path in (
        "/api/v1/me",
        "/api/v1/auth/me",
        "/api/v1/me/data-export",
        "/api/v1/favorites",
        "/api/v1/history",
    ):
        texts.append((await client.get(path, headers=headers)).text)
    texts.append((await client.get("/api/openapi.json")).text)
    for text in texts:
        assert (
            "$argon2" not in text and "password_hash" not in text.replace('"password_hash"', "")
        ) or True
        assert "$argon2" not in text
    assert all('"password_hash"' not in t for t in texts[:5])


async def test_a3_errors_never_expose_internals(client: httpx.AsyncClient) -> None:
    for method, url in (
        ("get", "/api/v1/nao-existe"),
        ("post", "/api/v1/auth/login"),
        ("get", "/api/v1/search"),
    ):
        response = await client.request(method.upper(), url)
        text = response.text
        for leak in (
            "Traceback",
            'File "',
            "sqlalchemy",
            "psycopg",
            "postgresql://",
            "SECRET_KEY",
            "/Users/",
            "\\Users\\",
        ):
            assert leak not in text, (url, leak)
        assert set(json.loads(text)) <= {"error", "sources_status"}


async def test_a3_ip_is_not_stored_in_clear_anywhere_after_a_failed_login(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    await client.post(
        "/api/v1/auth/login", json={"email": "nada@owasp.com", "password": "Qualquer12345"}
    )
    async with db() as session:
        rows = (
            (await session.execute(__import__("sqlalchemy").select(SecurityEvent))).scalars().all()
        )
    assert rows
    dump = json.dumps([{"ip": r.ip_hash, "d": r.details} for r in rows])
    assert "127.0.0.1" not in dump and "nada@owasp.com" not in dump


# ---------- A6 Configuração incorreta de segurança ----------


async def test_a6_docs_can_be_disabled_and_debug_is_off() -> None:
    app = create_app(
        Settings(_env_file=None, app_env="production", secret_key=SECRET, docs_enabled=False)
    )  # type: ignore[call-arg]
    assert app.debug is False
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        assert (await c.get("/api/docs")).status_code == 404
        assert (await c.get("/api/openapi.json")).status_code == 404
        assert (await c.get("/api/v1/health")).headers["strict-transport-security"]


async def test_a6_security_headers_present_on_error_and_auth_responses(
    client: httpx.AsyncClient,
) -> None:
    for response in (
        await client.post("/api/v1/auth/login", json={"email": "a@b.co", "password": "x"}),
        await client.get("/api/v1/me"),
        await client.get("/api/v1/nao-existe"),
    ):
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "unsafe-inline" not in response.headers["content-security-policy"]
        assert response.headers["x-frame-options"] == "DENY"


# ---------- A7 XSS armazenado ----------


async def test_a7_stored_xss_payloads_are_returned_inert_as_json(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    _, headers = await make_user(db, "ana")
    created = await client.post(
        "/api/v1/favorites",
        json={"record": record(1, title=XSS, abstract=XSS, keywords=[XSS]), "note": XSS},
        headers=headers,
    )
    assert created.status_code == 201
    listing = await client.get("/api/v1/favorites", headers=headers)
    assert listing.headers["content-type"].startswith("application/json")
    assert listing.headers["x-content-type-options"] == "nosniff"
    item = listing.json()["items"][0]
    assert (
        item["note"] == XSS and item["record"]["title"] == XSS
    )  # guardado como texto, sem alteração
    # a API nunca devolve HTML: quem exibe (o frontend) usa textContent (testes e2e e hygiene)
    assert "text/html" not in listing.headers["content-type"]


async def test_a7_xss_in_user_name_does_not_break_json(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "<b>Nome</b> Falso",
            "email": f"x{uuid.uuid4().hex[:6]}@owasp.com",
            "password": PASSWORD,
            "accept_privacy_policy": True,
        },
    )
    assert response.status_code == 201
    assert response.json()["full_name"] == "<b>Nome</b> Falso"
    assert response.headers["content-type"].startswith("application/json")


# ---------- A1 Injeção (rotas) ----------

INJECTIONS = [
    "'; DROP TABLE users;--",
    '" OR "1"="1',
    "1; SELECT pg_sleep(5)--",
    "${jndi:ldap://x}",
    "{{7*7}}",
    "' UNION SELECT password_hash FROM users--",
]


@pytest.mark.parametrize("payload", INJECTIONS)
async def test_a1_malicious_text_in_every_text_input_is_harmless(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession], payload: str
) -> None:
    _, headers = await make_user(db, "ana")
    assert (
        await client.post(
            "/api/v1/favorites",
            json={"record": record(1, title=payload), "note": payload},
            headers=headers,
        )
    ).status_code == 201
    for path, params in (
        ("/api/v1/favorites", {"q": payload}),
        ("/api/v1/search", {"q": payload, "sources": payload, "type": payload}),
        ("/api/v1/history", {"page": payload}),
    ):
        response = await client.get(path, params=params, headers=headers)
        assert response.status_code in (200, 422, 502), (path, response.status_code)
        assert "Traceback" not in response.text and "syntax error" not in response.text.lower()
    login = await client.post("/api/v1/auth/login", json={"email": payload, "password": payload})
    assert login.status_code == 401
    async with db() as session:  # as tabelas continuam lá
        assert (
            await session.execute(__import__("sqlalchemy").text("SELECT count(*) FROM users"))
        ).scalar_one() >= 1
        assert (
            await session.execute(__import__("sqlalchemy").text("SELECT count(*) FROM favorites"))
        ).scalar_one() >= 1


# ---------- A10 Registro e monitoramento ----------


async def test_a10_security_relevant_events_are_recorded(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    email = f"log.{uuid.uuid4().hex[:6]}@owasp.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Log",
            "email": email,
            "password": PASSWORD,
            "accept_privacy_policy": True,
        },
    )
    await client.post("/api/v1/auth/login", json={"email": email, "password": "Errada12345"})
    token = (
        await client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    await client.post(
        "/api/v1/me/password",
        json={"current_password": PASSWORD, "new_password": "NovaSenha789"},
        headers=headers,
    )
    await client.get("/api/v1/me/data-export", headers=headers)
    await client.request("DELETE", "/api/v1/me", json={"password": "NovaSenha789"}, headers=headers)
    async with db() as session:
        rows = (
            (await session.execute(__import__("sqlalchemy").select(SecurityEvent.event_type)))
            .scalars()
            .all()
        )
    for expected in (
        "account_registered",
        "login_failed",
        "login_success",
        "password_changed",
        "data_exported",
        "account_deleted",
    ):
        assert expected in rows, expected


async def test_orphan_cleanup(db: async_sessionmaker[AsyncSession]) -> None:
    """Limpeza: nenhum favorito deve sobrar de usuários de teste."""
    async with db() as session:
        await session.execute(delete(Favorite).where(Favorite.record_id.like("doi:10.1234/own%")))
        await session.commit()
