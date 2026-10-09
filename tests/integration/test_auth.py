import json
import logging
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta

import httpx
import jwt
import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.core.security import hash_password
from app.db import session as db_session
from app.main import create_app
from app.models import SecurityEvent, User

pytestmark = pytest.mark.integration

SECRET = "s" * 40
PASSWORD = "Senha12345"


def user_payload(**overrides: object) -> dict[str, object]:
    n = uuid.uuid4().hex[:8]
    data: dict[str, object] = {
        "full_name": "Maria de Souza",
        "email": f"maria.{n}@exemplo.com",
        "password": PASSWORD,
        "accept_privacy_policy": True,
    }
    return {**data, **overrides}


@pytest.fixture
def env(migrated_db_url: str, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("DATABASE_URL", migrated_db_url)
    monkeypatch.setenv("SECRET_KEY", SECRET)
    monkeypatch.setenv("RATE_LIMIT_AUTH", "1000/minute")
    monkeypatch.setenv("PRIVACY_POLICY_VERSION", "1.0")
    for cached in (get_settings, db_session.get_engine, db_session.get_sessionmaker):
        cached.cache_clear()
    limiter.reset()
    yield
    limiter.reset()
    for cached in (get_settings, db_session.get_engine, db_session.get_sessionmaker):
        cached.cache_clear()


@pytest.fixture
async def client(env: None) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    await db_session.get_engine().dispose()


@pytest.fixture
async def db(engine: AsyncEngine) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Sessões próprias para conferir e limpar o que a API confirmou no banco."""
    maker = async_sessionmaker(engine, expire_on_commit=False)
    yield maker
    async with maker() as session:
        await session.execute(delete(SecurityEvent))
        await session.execute(delete(User).where(User.email.like("%@exemplo.com")))
        await session.commit()


async def register(client: httpx.AsyncClient, **overrides: object) -> dict:  # type: ignore[type-arg]
    payload = user_payload(**overrides)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    # só a resposta da API mais o e-mail enviado: a senha enviada não entra no retorno
    return {"email_sent": payload["email"], **response.json()}


async def login(client: httpx.AsyncClient, email: str, password: str = PASSWORD) -> httpx.Response:
    return await client.post("/api/v1/auth/login", json={"email": email, "password": password})


async def events(db: async_sessionmaker[AsyncSession], event_type: str) -> list[SecurityEvent]:
    async with db() as session:
        rows = await session.execute(
            select(SecurityEvent).where(SecurityEvent.event_type == event_type)
        )
        return list(rows.scalars())


async def test_register_returns_user_without_hash_and_stores_consent(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    created = await register(client, email="  MARIA@Exemplo.com ")
    assert created["email"] == "maria@exemplo.com"  # normalizado em minúsculas
    assert set(created) >= {"id", "full_name", "email", "created_at", "consent_at"}
    body = json.dumps(created)
    assert "password_hash" not in body and "argon2" not in body
    async with db() as session:
        user = (
            await session.execute(select(User).where(User.email == "maria@exemplo.com"))
        ).scalar_one()
    assert user.consent_at is not None and user.consent_policy_version == "1.0"
    assert user.password_hash.startswith("$argon2id$") and PASSWORD not in user.password_hash
    registered = await events(db, "account_registered")
    assert len(registered) == 1 and registered[0].user_id == user.id


async def test_register_without_accepting_policy_is_422(client: httpx.AsyncClient) -> None:
    for value in (False, None):
        payload = user_payload(accept_privacy_policy=value)
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "validation_error"
    missing = user_payload()
    del missing["accept_privacy_policy"]
    assert (await client.post("/api/v1/auth/register", json=missing)).status_code == 422


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"password": "curta1"}, "password"),
        ({"password": "somenteletrasaqui"}, ""),
        ({"password": "1234567890123"}, ""),
        ({"password": "x" * 129 + "1"}, "password"),
        ({"email": "sem-arroba"}, "email"),
        ({"email": "a@b"}, "email"),
        ({"full_name": "A"}, "full_name"),
        ({"full_name": "x" * 121}, "full_name"),
    ],
)
async def test_register_validation(
    client: httpx.AsyncClient, overrides: dict[str, object], field: str
) -> None:
    response = await client.post("/api/v1/auth/register", json=user_payload(**overrides))
    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == field
    assert PASSWORD not in response.text


async def test_password_cannot_contain_the_email(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json=user_payload(email="joao@exemplo.com", password="xxjoao@exemplo.com9"),
    )
    assert response.status_code == 422


async def test_duplicate_email_gives_generic_409(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    first = await register(client)
    second = await client.post(
        "/api/v1/auth/register", json=user_payload(email=str(first["email"]).upper())
    )
    assert second.status_code == 409
    error = second.json()["error"]
    assert error["message"] == "Não foi possível concluir o cadastro."
    assert "e-mail" not in error["message"].lower() and "existe" not in error["message"].lower()


async def test_login_success_and_me(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    created = await register(client)
    response = await login(client, str(created["email"]))
    assert response.status_code == 200
    token = response.json()
    assert token["token_type"] == "bearer" and token["expires_in"] == 3600
    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token['access_token']}"}
    )
    assert me.status_code == 200 and me.json()["email"] == created["email"]
    assert "password_hash" not in me.text
    assert len(await events(db, "login_success")) == 1
    async with db() as session:
        user = await session.get(User, uuid.UUID(str(created["id"])))
        assert user is not None and user.last_login_at is not None


async def test_wrong_password_and_unknown_email_look_identical(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    created = await register(client)
    wrong = await login(client, str(created["email"]), "SenhaErrada99")
    unknown = await login(client, "ninguem@exemplo.com", PASSWORD)
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["error"] == unknown.json()["error"]
    assert wrong.json()["error"]["message"] == "E-mail ou senha inválidos."
    failed = await events(db, "login_failed")
    assert len(failed) == 2  # o evento sobrevive ao 401


async def test_inactive_user_cannot_login_or_use_token(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    created = await register(client)
    token = (await login(client, str(created["email"]))).json()["access_token"]
    async with db() as session:
        await session.execute(
            text("UPDATE users SET is_active = false WHERE id = :i"), {"i": created["id"]}
        )
        await session.commit()
    assert (await login(client, str(created["email"]))).status_code == 401
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 401


def token_for(user_id: str, **overrides: object) -> str:
    now = datetime.now(UTC)
    claims: dict[str, object] = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "iss": "academic-search-hub",
        "jti": "x",
    }
    return jwt.encode({**claims, **overrides}, SECRET, algorithm="HS256")


async def test_me_requires_a_valid_token(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    created = await register(client)
    uid = str(created["id"])
    good = (await login(client, str(created["email"]))).json()["access_token"]
    head, payload, sig = good.split(".")
    now = datetime.now(UTC)
    unsigned = jwt.encode(
        {
            "sub": uid,
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "iss": "academic-search-hub",
            "jti": "x",
        },
        key=None,
        algorithm="none",
    )
    bad_tokens = {
        "ausente": None,
        "adulterado": f"{head}.{payload}x.{sig}",
        "alg none": unsigned,
        "expirado": token_for(uid, exp=now - timedelta(seconds=10)),
        "iss errado": token_for(uid, iss="outro"),
        "usuario inexistente": token_for(str(uuid.uuid4())),
    }
    for name, token in bad_tokens.items():
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401, name
        assert response.json()["error"]["code"] == "unauthorized", name
    assert (
        await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {good}"})
    ).status_code == 200


async def test_sixth_login_in_a_minute_is_429_and_records_event(
    client: httpx.AsyncClient,
    db: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RATE_LIMIT_AUTH", "5/minute")
    get_settings.cache_clear()
    limiter.reset()
    statuses = [
        (await login(client, "ninguem@exemplo.com", "Errada12345")).status_code for _ in range(5)
    ]
    assert statuses == [401] * 5
    blocked = await login(client, "ninguem@exemplo.com", "Errada12345")
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"
    limited = await events(db, "rate_limited")
    assert len(limited) == 1
    assert limited[0].ip_hash and "127.0.0.1" not in limited[0].ip_hash
    assert limited[0].details == {"path": "/api/v1/auth/login"}
    registration = await client.post("/api/v1/auth/register", json=user_payload())
    assert registration.status_code == 201 or registration.status_code == 429


async def test_ip_is_never_stored_in_clear_and_events_have_no_email(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    created = await register(client)
    await login(client, str(created["email"]))
    await login(client, str(created["email"]), "Errada12345")
    async with db() as session:
        rows = (await session.execute(select(SecurityEvent))).scalars().all()
    assert rows
    for row in rows:
        dump = json.dumps({"ip": row.ip_hash, "d": row.details, "t": row.event_type})
        assert "127.0.0.1" not in dump and str(created["email"]) not in dump
        assert row.ip_hash and len(row.ip_hash) == 64  # HMAC-SHA256 em hexadecimal


async def test_password_never_appears_in_logs_or_responses(
    client: httpx.AsyncClient,
    db: async_sessionmaker[AsyncSession],
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.DEBUG):
        created = await register(client, password="Segredo-Unico-98765")
        wrong = await login(client, str(created["email"]), "Segredo-Errado-12345")
        ok = await login(client, str(created["email"]), "Segredo-Unico-98765")
    everything = wrong.text + ok.text + json.dumps(created, default=str)
    everything += " ".join(r.getMessage() for r in caplog.records)
    assert "Segredo-Unico-98765" not in everything and "Segredo-Errado-12345" not in everything


async def test_rehash_on_login_when_parameters_are_weaker(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    from argon2 import PasswordHasher

    created = await register(client)
    weak = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1).hash(PASSWORD)
    async with db() as session:
        await session.execute(
            text("UPDATE users SET password_hash = :h WHERE id = :i"),
            {"h": weak, "i": created["id"]},
        )
        await session.commit()
    assert (await login(client, str(created["email"]))).status_code == 200
    async with db() as session:
        user = await session.get(User, uuid.UUID(str(created["id"])))
        assert user is not None
        assert user.password_hash != weak and user.password_hash.startswith("$argon2id$")


async def test_login_with_existing_hash_helper_user(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    async with db() as session:
        session.add(
            User(
                email="direto@exemplo.com",
                full_name="Direto",
                password_hash=hash_password(PASSWORD),
                consent_at=datetime.now(UTC),
                consent_policy_version="1.0",
            )
        )
        await session.commit()
    assert (await login(client, "DIRETO@exemplo.com")).status_code == 200


async def test_openapi_declares_bearer_auth_on_me(client: httpx.AsyncClient) -> None:
    doc = (await client.get("/api/openapi.json")).json()
    assert "bearerAuth" in doc["components"]["securitySchemes"]
    me = doc["paths"]["/api/v1/auth/me"]["get"]
    assert {"bearerAuth": []} in me["security"]
    assert {"/api/v1/auth/register", "/api/v1/auth/login"} <= set(doc["paths"])
