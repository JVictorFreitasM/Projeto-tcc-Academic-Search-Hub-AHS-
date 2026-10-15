import json
import uuid
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db import session as db_session
from app.main import create_app
from app.models import Favorite, SearchHistory, SecurityEvent, User

pytestmark = pytest.mark.integration

SECRET = "s" * 40
PASSWORD = "Senha12345"


def record(n: int = 1) -> dict[str, Any]:
    return {
        "id": f"doi:10.1234/me{n}",
        "title": f"Trabalho da conta número {n}",
        "authors": [{"name": "Maria Souza", "orcid": None}],
        "year": 2022,
        "doi": f"10.1234/me{n}",
        "type": "article",
        "sources": [{"source": "openalex", "source_id": f"W{n}", "url": None}],
    }


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
async def db(engine: AsyncEngine) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    maker = async_sessionmaker(engine, expire_on_commit=False)
    yield maker
    async with maker() as session:
        await session.execute(delete(SecurityEvent))
        await session.execute(delete(User).where(User.email.like("%@conta.com")))
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


class Account:
    def __init__(self, id_: str, email: str, headers: dict[str, str]) -> None:
        self.id, self.email, self.headers = id_, email, headers


async def sign_up(client: httpx.AsyncClient, name: str = "ana") -> Account:
    email = f"{name}.{uuid.uuid4().hex[:6]}@conta.com"
    created = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": f"{name.title()} da Silva",
            "email": email,
            "password": PASSWORD,
            "accept_privacy_policy": True,
        },
    )
    assert created.status_code == 201
    token = (
        await client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    ).json()
    return Account(
        created.json()["id"], email, {"Authorization": f"Bearer {token['access_token']}"}
    )


async def count(db: async_sessionmaker[AsyncSession], model: type, user_id: str) -> int:
    async with db() as session:
        return (
            await session.execute(
                select(func.count()).select_from(model).where(model.user_id == uuid.UUID(user_id))  # type: ignore[attr-defined]
            )
        ).scalar_one()


async def test_get_me_returns_account_data(client: httpx.AsyncClient) -> None:
    ana = await sign_up(client)
    body = (await client.get("/api/v1/me", headers=ana.headers)).json()
    assert body["email"] == ana.email and body["full_name"] == "Ana da Silva"
    assert body["consent_policy_version"] == "1.0" and body["consent_at"] and body["created_at"]
    assert "password_hash" not in body
    assert (await client.get("/api/v1/me")).status_code == 401


async def test_patch_name_without_password(client: httpx.AsyncClient) -> None:
    ana = await sign_up(client)
    response = await client.patch(
        "/api/v1/me", json={"full_name": "  Ana   Maria  "}, headers=ana.headers
    )
    assert response.status_code == 200 and response.json()["full_name"] == "Ana Maria"


async def test_patch_email_requires_the_current_password(client: httpx.AsyncClient) -> None:
    ana = await sign_up(client)
    new = f"novo.{uuid.uuid4().hex[:6]}@conta.com"
    no_password = await client.patch("/api/v1/me", json={"email": new}, headers=ana.headers)
    wrong = await client.patch(
        "/api/v1/me", json={"email": new, "current_password": "Errada12345"}, headers=ana.headers
    )
    assert no_password.status_code == wrong.status_code == 403
    assert wrong.json()["error"]["code"] == "invalid_password"
    ok = await client.patch(
        "/api/v1/me", json={"email": new.upper(), "current_password": PASSWORD}, headers=ana.headers
    )
    assert ok.status_code == 200 and ok.json()["email"] == new
    login = await client.post("/api/v1/auth/login", json={"email": new, "password": PASSWORD})
    assert login.status_code == 200


async def test_patch_with_a_taken_email_gives_generic_409(client: httpx.AsyncClient) -> None:
    ana = await sign_up(client, "ana")
    bia = await sign_up(client, "bia")
    response = await client.patch(
        "/api/v1/me", json={"email": bia.email, "current_password": PASSWORD}, headers=ana.headers
    )
    assert response.status_code == 409
    assert response.json()["error"]["message"] == "Não foi possível atualizar os dados."
    assert bia.email not in response.text


async def test_patch_validation(client: httpx.AsyncClient) -> None:
    ana = await sign_up(client)
    for payload in ({"email": "sem-arroba"}, {"full_name": "A"}):
        assert (
            await client.patch("/api/v1/me", json=payload, headers=ana.headers)
        ).status_code == 422


async def test_change_password(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    ana = await sign_up(client)
    url = "/api/v1/me/password"
    wrong = await client.post(
        url,
        json={"current_password": "Errada12345", "new_password": "NovaSenha789"},
        headers=ana.headers,
    )
    assert wrong.status_code == 403 and wrong.json()["error"]["code"] == "invalid_password"
    weak = await client.post(
        url,
        json={"current_password": PASSWORD, "new_password": "somenteletras"},
        headers=ana.headers,
    )
    assert weak.status_code == 422
    short = await client.post(
        url, json={"current_password": PASSWORD, "new_password": "curta1"}, headers=ana.headers
    )
    assert short.status_code == 422
    contains_email = await client.post(
        url,
        json={"current_password": PASSWORD, "new_password": f"x1{ana.email}"},
        headers=ana.headers,
    )
    assert contains_email.status_code == 422
    ok = await client.post(
        url,
        json={"current_password": PASSWORD, "new_password": "NovaSenha789"},
        headers=ana.headers,
    )
    assert ok.status_code == 204
    assert (
        await client.post("/api/v1/auth/login", json={"email": ana.email, "password": PASSWORD})
    ).status_code == 401
    assert (
        await client.post(
            "/api/v1/auth/login", json={"email": ana.email, "password": "NovaSenha789"}
        )
    ).status_code == 200
    async with db() as session:
        events = (
            (
                await session.execute(
                    select(SecurityEvent).where(SecurityEvent.event_type == "password_changed")
                )
            )
            .scalars()
            .all()
        )
    assert len(events) == 1 and events[0].user_id == uuid.UUID(ana.id)
    assert "NovaSenha789" not in json.dumps(events[0].details)


async def test_data_export_has_all_own_data_and_nothing_from_others(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    ana = await sign_up(client, "ana")
    bia = await sign_up(client, "bia")
    await client.post(
        "/api/v1/favorites", json={"record": record(1), "note": "nota da ana"}, headers=ana.headers
    )
    await client.post("/api/v1/favorites", json={"record": record(2)}, headers=ana.headers)
    await client.post(
        "/api/v1/favorites", json={"record": record(9), "note": "SÓ DA BIA"}, headers=bia.headers
    )
    async with db() as session:
        for uid, text in ((ana.id, "busca da ana"), (bia.id, "BUSCA DA BIA")):
            session.add(SearchHistory(user_id=uuid.UUID(uid), query=text, filters={}))
        await session.commit()

    response = await client.get("/api/v1/me/data-export", headers=ana.headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["content-disposition"].startswith('attachment; filename="meus-dados-')
    data = response.json()
    assert data["account"]["email"] == ana.email and data["exported_at"]
    assert {f["record"]["id"] for f in data["favorites"]} == {"doi:10.1234/me1", "doi:10.1234/me2"}
    assert [h["query"] for h in data["search_history"]] == ["busca da ana"]
    text = response.text
    assert bia.email not in text and "SÓ DA BIA" not in text and "BUSCA DA BIA" not in text
    assert "password_hash" not in text and "argon2" not in text
    async with db() as session:
        events = (
            (
                await session.execute(
                    select(SecurityEvent).where(SecurityEvent.event_type == "data_exported")
                )
            )
            .scalars()
            .all()
        )
    assert len(events) == 1 and events[0].user_id == uuid.UUID(ana.id)


async def test_delete_account_requires_the_right_password(client: httpx.AsyncClient) -> None:
    ana = await sign_up(client)
    wrong = await client.request(
        "DELETE", "/api/v1/me", json={"password": "Errada12345"}, headers=ana.headers
    )
    assert wrong.status_code == 403 and wrong.json()["error"]["code"] == "invalid_password"
    missing = await client.request("DELETE", "/api/v1/me", json={}, headers=ana.headers)
    assert missing.status_code == 422
    assert (
        await client.get("/api/v1/me", headers=ana.headers)
    ).status_code == 200  # nada foi apagado


async def test_delete_account_removes_everything_keeps_event_without_personal_data(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    ana = await sign_up(client, "ana")
    bia = await sign_up(client, "bia")
    for n in (1, 2):
        await client.post("/api/v1/favorites", json={"record": record(n)}, headers=ana.headers)
    await client.post("/api/v1/favorites", json={"record": record(9)}, headers=bia.headers)
    async with db() as session:
        session.add(SearchHistory(user_id=uuid.UUID(ana.id), query="algo", filters={}))
        await session.commit()
    assert (await count(db, Favorite, ana.id), await count(db, SearchHistory, ana.id)) == (2, 1)

    response = await client.request(
        "DELETE", "/api/v1/me", json={"password": PASSWORD}, headers=ana.headers
    )
    assert response.status_code == 204
    assert (await count(db, Favorite, ana.id), await count(db, SearchHistory, ana.id)) == (0, 0)
    async with db() as session:
        assert await session.get(User, uuid.UUID(ana.id)) is None
        assert await session.get(User, uuid.UUID(bia.id)) is not None  # outro usuário intacto
        events = (
            (
                await session.execute(
                    select(SecurityEvent).where(SecurityEvent.event_type == "account_deleted")
                )
            )
            .scalars()
            .all()
        )
    assert len(events) == 1
    dump = json.dumps({"u": str(events[0].user_id), "d": events[0].details, "h": events[0].ip_hash})
    assert events[0].user_id is None and ana.email not in dump and ana.id not in dump
    assert await count(db, Favorite, bia.id) == 1


async def test_old_token_fails_after_deletion(client: httpx.AsyncClient) -> None:
    ana = await sign_up(client)
    assert (
        await client.request(
            "DELETE", "/api/v1/me", json={"password": PASSWORD}, headers=ana.headers
        )
    ).status_code == 204
    for call in (
        client.get("/api/v1/me", headers=ana.headers),
        client.get("/api/v1/auth/me", headers=ana.headers),
    ):
        assert (await call).status_code == 401
    assert (
        await client.post("/api/v1/auth/login", json={"email": ana.email, "password": PASSWORD})
    ).status_code == 401


async def test_policy_version_change_requires_new_consent(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    ana = await sign_up(client)
    first_login = (
        await client.post("/api/v1/auth/login", json={"email": ana.email, "password": PASSWORD})
    ).json()
    assert first_login["consent_required"] is False

    monkeypatch.setenv("PRIVACY_POLICY_VERSION", "2.0")
    get_settings.cache_clear()
    new_app = create_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=new_app), base_url="http://testserver"
    ) as v2:
        login = (
            await v2.post("/api/v1/auth/login", json={"email": ana.email, "password": PASSWORD})
        ).json()
        assert login["consent_required"] is True
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        assert (await v2.get("/api/v1/me", headers=headers)).json()[
            "consent_policy_version"
        ] == "1.0"
        accepted = await v2.post("/api/v1/me/consent", headers=headers)
        assert accepted.status_code == 200 and accepted.json()["consent_policy_version"] == "2.0"
        again = (
            await v2.post("/api/v1/auth/login", json={"email": ana.email, "password": PASSWORD})
        ).json()
        assert again["consent_required"] is False
    await db_session.get_engine().dispose()


async def test_privacy_policy_is_public(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/privacy")
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "1.0"
    content = body["content"]
    assert content.startswith("# Política de Privacidade")
    assert "{CONTATO_DO_RESPONSAVEL}" not in content  # o marcador foi trocado pelo contato
    assert "João Victor de Freitas Martins" in content and "joaovictorddm@gmail.com" in content
    for topic in ("Quais dados tratamos", "Base legal", "Seus direitos", "Por quanto tempo"):
        assert topic in content
    assert "certificad" not in content.lower()  # não afirma certificações


async def test_all_me_routes_require_login(client: httpx.AsyncClient) -> None:
    calls = [
        client.get("/api/v1/me"),
        client.patch("/api/v1/me", json={"full_name": "Fulano"}),
        client.post(
            "/api/v1/me/password", json={"current_password": "x", "new_password": "Nova12345678"}
        ),
        client.get("/api/v1/me/data-export"),
        client.post("/api/v1/me/consent"),
        client.request("DELETE", "/api/v1/me", json={"password": "x"}),
    ]
    for call in calls:
        assert (await call).status_code == 401
