import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.cli_security import main
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db import session as db_session
from app.main import create_app
from app.models import SecurityEvent, User
from app.models.security_event import EVENT_TYPES
from app.services.security_events import purge_older_than

pytestmark = pytest.mark.integration

SECRET = "s" * 40
PASSWORD = "Senha12345"


@pytest.fixture
def env(migrated_db_url: str, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("DATABASE_URL", migrated_db_url)
    monkeypatch.setenv("SECRET_KEY", SECRET)
    monkeypatch.setenv("RATE_LIMIT_AUTH", "1000/minute")
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
    async with maker() as session:
        await session.execute(delete(SecurityEvent))
        await session.commit()
    yield maker
    async with maker() as session:
        await session.execute(delete(SecurityEvent))
        await session.execute(delete(User).where(User.email.like("%@eventos.com")))
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


async def run_all_flows(client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> str:
    email = f"fluxo.{uuid.uuid4().hex[:6]}@eventos.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Fluxo",
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
    monkeypatch.setenv("RATE_LIMIT_AUTH", "1/minute")
    get_settings.cache_clear()
    limiter.reset()
    for _ in range(3):
        await client.post(
            "/api/v1/auth/login", json={"email": "x@eventos.com", "password": "Qualquer12345"}
        )
    return email


async def stored_types(db: async_sessionmaker[AsyncSession]) -> set[str]:
    async with db() as session:
        return set((await session.execute(select(SecurityEvent.event_type))).scalars())


async def test_every_event_type_of_the_model_is_produced_by_a_route(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession], monkeypatch: pytest.MonkeyPatch
) -> None:
    await run_all_flows(client, monkeypatch)
    assert await stored_types(db) == set(EVENT_TYPES)


async def test_database_never_contains_clear_ip_email_or_password(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession], monkeypatch: pytest.MonkeyPatch
) -> None:
    email = await run_all_flows(client, monkeypatch)
    async with db() as session:
        rows = (
            (await session.execute(text("SELECT row_to_json(e)::text FROM security_events e")))
            .scalars()
            .all()
        )
    assert rows
    dump = "\n".join(rows)
    for forbidden in (
        "127.0.0.1",
        "::1",
        email,
        "x@eventos.com",
        PASSWORD,
        "NovaSenha789",
        "Mozilla",
    ):
        assert forbidden not in dump, forbidden
    async with db() as session:
        ips = (
            (
                await session.execute(
                    select(SecurityEvent.ip_hash).where(SecurityEvent.ip_hash.is_not(None))
                )
            )
            .scalars()
            .all()
        )
    assert ips and all(len(h) == 64 and all(c in "0123456789abcdef" for c in h) for h in ips)


async def add_events(db: async_sessionmaker[AsyncSession], ages_days: list[int]) -> None:
    now = datetime.now(UTC)
    async with db() as session:
        for index, age in enumerate(ages_days):
            session.add(
                SecurityEvent(
                    event_type="login_failed" if index % 2 == 0 else "rate_limited",
                    ip_hash="ab" * 32,
                    details={"n": index},
                    created_at=now - timedelta(days=age, minutes=index),
                )
            )
        await session.commit()


async def count(db: async_sessionmaker[AsyncSession]) -> int:
    async with db() as session:
        return (await session.execute(select(func.count()).select_from(SecurityEvent))).scalar_one()


async def test_purge_deletes_only_old_events(db: async_sessionmaker[AsyncSession]) -> None:
    await add_events(db, [200, 181, 179, 10, 0])
    async with db() as session:
        removed = await purge_older_than(session, 180)
        await session.commit()
    assert removed == 2 and await count(db) == 3
    async with db() as session:
        assert await purge_older_than(session, 180) == 0  # nada mais antigo
        with pytest.raises(ValueError, match="mínima"):
            await purge_older_than(session, 0)


@pytest.fixture
def cli_env(env: None) -> None:
    return None


def test_cli_events_lists_filters_and_hides_the_full_hash(
    cli_env: None, capsys: pytest.CaptureFixture[str], migrated_db_url: str
) -> None:
    import asyncio

    from sqlalchemy.ext.asyncio import create_async_engine

    async def seed() -> None:
        engine = create_async_engine(migrated_db_url)
        maker = async_sessionmaker(engine)
        async with maker() as session:
            await session.execute(delete(SecurityEvent))
            now = datetime.now(UTC)
            for index, (kind, age) in enumerate(
                [("login_failed", 0), ("rate_limited", 1), ("login_failed", 40)]
            ):
                session.add(
                    SecurityEvent(
                        event_type=kind,
                        ip_hash="cd" * 32,
                        details={"n": index},
                        created_at=now - timedelta(days=age),
                    )
                )
            await session.commit()
        await engine.dispose()

    asyncio.run(seed())  # SelectorEventLoop vem da política definida no conftest
    assert main(["events"]) == 0
    out = capsys.readouterr().out
    assert "3 evento(s)." in out and "login_failed" in out and "rate_limited" in out
    assert "cdcdcdcdcdcd" in out and "cd" * 32 not in out  # só o início do hash
    assert main(["events", "--type", "rate_limited"]) == 0
    assert "1 evento(s)." in capsys.readouterr().out
    since = (datetime.now(UTC) - timedelta(days=5)).date().isoformat()
    assert main(["events", "--since", since]) == 0
    assert "2 evento(s)." in capsys.readouterr().out
    assert main(["events", "--limit", "1"]) == 0
    assert "1 evento(s)." in capsys.readouterr().out


def test_cli_purge_default_and_custom_retention(
    cli_env: None, capsys: pytest.CaptureFixture[str], migrated_db_url: str
) -> None:
    import asyncio

    from sqlalchemy.ext.asyncio import create_async_engine

    async def seed() -> None:
        engine = create_async_engine(migrated_db_url)
        maker = async_sessionmaker(engine)
        async with maker() as session:
            await session.execute(delete(SecurityEvent))
            now = datetime.now(UTC)
            for age in (400, 200, 100, 3):
                session.add(
                    SecurityEvent(
                        event_type="login_failed", details={}, created_at=now - timedelta(days=age)
                    )
                )
            await session.commit()
        await engine.dispose()

    asyncio.run(seed())
    assert main(["purge"]) == 0  # padrão: 180 dias
    assert "2 evento(s) com mais de 180 dias" in capsys.readouterr().out
    assert main(["purge", "--older-than-days", "30"]) == 0
    assert "1 evento(s) com mais de 30 dias" in capsys.readouterr().out
    assert main(["purge", "--older-than-days", "0"]) == 2
    assert "mínima" in capsys.readouterr().err
    assert main(["events"]) == 0
    assert "1 evento(s)." in capsys.readouterr().out


def test_cli_rejects_unknown_event_type(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["events", "--type", "inexistente"])
