import csv
import io
import json
import re
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.rate_limit import limiter
from app.core.security import create_access_token, hash_password
from app.db import session as db_session
from app.main import create_app
from app.models import SecurityEvent, User

pytestmark = pytest.mark.integration

SECRET = "s" * 40
EXPECTED = {
    "bibtex": ("application/x-bibtex", "bib"),
    "ris": ("application/x-research-info-systems", "ris"),
    "json": ("application/json", "json"),
    "csv": ("text/csv; charset=utf-8", "csv"),
}


def record(n: int = 1, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": f"doi:10.1234/exp{n}",
        "title": f"Exportação de teste número {n}",
        "authors": [{"name": "Maria Souza", "orcid": None}],
        "year": 2022,
        "doi": f"10.1234/exp{n}",
        "type": "article",
        "sources": [{"source": "openalex", "source_id": f"W{n}", "url": None}],
    }
    return {**data, **overrides}


@pytest.fixture
def env(migrated_db_url: str, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("DATABASE_URL", migrated_db_url)
    monkeypatch.setenv("SECRET_KEY", SECRET)
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
        await session.execute(
            delete(SecurityEvent).where(SecurityEvent.event_type == "data_exported")
        )
        await session.execute(delete(User).where(User.email.like("%@exp.com")))
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
            email=f"{name}.{uuid.uuid4().hex[:6]}@exp.com",
            full_name=name,
            password_hash=hash_password("Senha12345"),
            consent_at=datetime.now(UTC),
            consent_policy_version="1.0",
        )
        session.add(user)
        await session.commit()
        token = create_access_token(user.id, Settings(_env_file=None, secret_key=SECRET))  # type: ignore[call-arg]
        return user.id, {"Authorization": f"Bearer {token}"}


def check_headers(response: httpx.Response, fmt: str) -> None:
    media, extension = EXPECTED[fmt]
    assert response.headers["content-type"].lower().startswith(media.split(";")[0])
    if fmt == "csv":
        assert "charset=utf-8" in response.headers["content-type"].lower()
    disposition = response.headers["content-disposition"]
    assert re.fullmatch(rf'attachment; filename="exportacao-\d{{8}}\.{extension}"', disposition)


@pytest.mark.parametrize("fmt", list(EXPECTED))
async def test_export_search_results_without_login(client: httpx.AsyncClient, fmt: str) -> None:
    response = await client.post(
        "/api/v1/export", json={"format": fmt, "records": [record(1), record(2)]}
    )
    assert response.status_code == 200
    check_headers(response, fmt)
    body = response.content.decode("utf-8")
    assert "Exportação de teste número 1" in body and "Exportação de teste número 2" in body


async def test_post_export_payload_formats_are_correct(client: httpx.AsyncClient) -> None:
    payload = {"records": [record(1)]}
    bib = (await client.post("/api/v1/export", json={"format": "bibtex", **payload})).text
    assert bib.startswith("@article{souza2022exportacao,")
    ris = (await client.post("/api/v1/export", json={"format": "ris", **payload})).text
    assert "TY  - JOUR" in ris and "ER  - " in ris
    js = (await client.post("/api/v1/export", json={"format": "json", **payload})).json()
    assert js[0]["doi"] == "10.1234/exp1"
    rows = list(
        csv.reader(
            io.StringIO(
                (await client.post("/api/v1/export", json={"format": "csv", **payload})).text,
                newline="",
            )
        )
    )
    assert rows[1][4] == "10.1234/exp1"


async def test_more_than_100_records_is_422(client: httpx.AsyncClient) -> None:
    records = [record(i) for i in range(101)]
    response = await client.post("/api/v1/export", json={"format": "json", "records": records})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    exactly = await client.post("/api/v1/export", json={"format": "json", "records": records[:100]})
    assert exactly.status_code == 200 and len(exactly.json()) == 100


@pytest.mark.parametrize("bad", ["pdf", "", "BIBTEX"])
async def test_unknown_format_is_422(client: httpx.AsyncClient, bad: str) -> None:
    response = await client.post("/api/v1/export", json={"format": bad, "records": [record()]})
    assert response.status_code == 422


async def test_export_with_invalid_record_is_422(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/export", json={"format": "json", "records": [record(url="javascript:alert(1)")]}
    )
    assert response.status_code == 422


async def test_csv_export_neutralizes_formulas_end_to_end(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/export",
        json={"format": "csv", "records": [record(title='=HYPERLINK("http://x.example","a")')]},
    )
    row = list(csv.reader(io.StringIO(response.text, newline="")))[1]
    assert row[1].startswith("'=HYPERLINK")


@pytest.mark.parametrize("fmt", list(EXPECTED))
async def test_export_favorites_requires_login_and_returns_only_own(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession], fmt: str
) -> None:
    assert (await client.get("/api/v1/favorites/export", params={"format": fmt})).status_code == 401
    _, a = await make_user(db, "ana")
    _, b = await make_user(db, "bia")
    await client.post("/api/v1/favorites", json={"record": record(1)}, headers=a)
    await client.post("/api/v1/favorites", json={"record": record(2)}, headers=a)
    await client.post("/api/v1/favorites", json={"record": record(9, title="Só da Bia")}, headers=b)
    response = await client.get("/api/v1/favorites/export", params={"format": fmt}, headers=a)
    assert response.status_code == 200
    check_headers(response, fmt)
    text = response.content.decode("utf-8")
    assert "número 1" in text and "número 2" in text and "Só da Bia" not in text


async def test_export_favorites_route_is_not_taken_as_an_id(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    _, headers = await make_user(db, "ana")
    response = await client.get(
        "/api/v1/favorites/export", params={"format": "json"}, headers=headers
    )
    assert response.status_code == 200 and response.json() == []
    assert (
        await client.get("/api/v1/favorites/export", headers=headers)
    ).status_code == 422  # sem formato


async def test_export_favorites_records_event_without_content(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    user_id, headers = await make_user(db, "ana")
    await client.post("/api/v1/favorites", json={"record": record(1)}, headers=headers)
    await client.get("/api/v1/favorites/export", params={"format": "bibtex"}, headers=headers)
    async with db() as session:
        events = (
            (
                await session.execute(
                    select(SecurityEvent).where(
                        SecurityEvent.event_type == "data_exported",
                        SecurityEvent.user_id == user_id,
                    )
                )
            )
            .scalars()
            .all()
        )
    assert len(events) == 1
    assert events[0].details == {} and events[0].ip_hash and len(events[0].ip_hash) == 64
    # exportar resultados de busca (sem login) não gera evento
    await client.post("/api/v1/export", json={"format": "json", "records": [record()]})
    async with db() as session:
        total = len(
            (
                await session.execute(
                    select(SecurityEvent).where(SecurityEvent.event_type == "data_exported")
                )
            )
            .scalars()
            .all()
        )
    assert total == 1


async def test_openapi_documents_both_export_routes(client: httpx.AsyncClient) -> None:
    doc = (await client.get("/api/openapi.json")).json()
    assert "/api/v1/export" in doc["paths"] and "/api/v1/favorites/export" in doc["paths"]
    get_op = doc["paths"]["/api/v1/favorites/export"]["get"]
    assert {"bearerAuth": []} in get_op["security"]
    assert set(get_op["responses"]["200"]["content"]) == {m for m, _ in EXPECTED.values()}
    assert json.dumps(doc)  # documento serializável
