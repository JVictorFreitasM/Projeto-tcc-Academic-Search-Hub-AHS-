import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.api.v1.search import get_search_service
from app.connectors.base import SourcePage, SourceQuery
from app.core.config import Settings, get_settings
from app.core.rate_limit import limiter
from app.core.security import create_access_token, hash_password
from app.db import session as db_session
from app.main import create_app
from app.models import Favorite, User
from app.schemas.record import AuthorOut, RecordOut, SourceRef
from app.services.search_service import SearchService

pytestmark = pytest.mark.integration

SECRET = "s" * 40


def record(n: int = 1, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": f"doi:10.1234/fav{n}",
        "title": f"Letramento digital número {n}",
        "authors": [{"name": "Maria Souza", "orcid": None}],
        "year": 2021,
        "doi": f"10.1234/fav{n}",
        "url": "https://exemplo.org/1",
        "type": "article",
        "sources": [{"source": "openalex", "source_id": f"W{n}", "url": None}],
    }
    return {**data, **overrides}


@pytest.fixture
def env(migrated_db_url: str, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("DATABASE_URL", migrated_db_url)
    monkeypatch.setenv("SECRET_KEY", SECRET)
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
        await session.execute(delete(User).where(User.email.like("%@fav.com")))
        await session.commit()


@pytest.fixture
async def client(
    env: None, db: async_sessionmaker[AsyncSession]
) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        c.app = app  # type: ignore[attr-defined]
        yield c
    await db_session.get_engine().dispose()


async def make_user(
    db: async_sessionmaker[AsyncSession], name: str
) -> tuple[uuid.UUID, dict[str, str]]:
    async with db() as session:
        user = User(
            email=f"{name}.{uuid.uuid4().hex[:6]}@fav.com",
            full_name=name,
            password_hash=hash_password("Senha12345"),
            consent_at=datetime.now(UTC),
            consent_policy_version="1.0",
        )
        session.add(user)
        await session.commit()
        token = create_access_token(user.id, Settings(_env_file=None, secret_key=SECRET))  # type: ignore[call-arg]
        return user.id, {"Authorization": f"Bearer {token}"}


async def test_create_returns_201_with_record_note_and_date(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    _, headers = await make_user(db, "ana")
    response = await client.post(
        "/api/v1/favorites", json={"record": record(), "note": "  ler com calma  "}, headers=headers
    )
    assert response.status_code == 201
    body = response.json()
    assert body["note"] == "ler com calma" and body["created_at"] and uuid.UUID(body["id"])
    assert body["record"]["title"] == "Letramento digital número 1"
    assert body["record"]["is_favorite"] is True


async def test_creating_the_same_favorite_twice_does_not_duplicate(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    user_id, headers = await make_user(db, "ana")
    first = await client.post("/api/v1/favorites", json={"record": record()}, headers=headers)
    second = await client.post(
        "/api/v1/favorites", json={"record": record(), "note": "outra"}, headers=headers
    )
    assert (first.status_code, second.status_code) == (201, 200)
    assert first.json()["id"] == second.json()["id"]
    async with db() as session:
        count = (
            await session.execute(
                select(func.count()).select_from(Favorite).where(Favorite.user_id == user_id)
            )
        ).scalar_one()
    assert count == 1


async def test_without_token_is_401(client: httpx.AsyncClient) -> None:
    fake_id = uuid.uuid4()
    calls = [
        client.post("/api/v1/favorites", json={"record": record()}),
        client.get("/api/v1/favorites"),
        client.patch(f"/api/v1/favorites/{fake_id}", json={"note": "x"}),
        client.delete(f"/api/v1/favorites/{fake_id}"),
    ]
    for call in calls:
        response = await call
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"


async def test_user_b_gets_404_for_user_a_favorite(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    _, headers_a = await make_user(db, "ana")
    _, headers_b = await make_user(db, "bia")
    created = (
        await client.post(
            "/api/v1/favorites", json={"record": record(), "note": "só da Ana"}, headers=headers_a
        )
    ).json()
    fav = created["id"]
    patch = await client.patch(
        f"/api/v1/favorites/{fav}", json={"note": "invadido"}, headers=headers_b
    )
    delete_ = await client.delete(f"/api/v1/favorites/{fav}", headers=headers_b)
    unknown = await client.delete(f"/api/v1/favorites/{uuid.uuid4()}", headers=headers_b)
    assert patch.status_code == delete_.status_code == 404
    assert patch.json() == delete_.json() == unknown.json()  # não revela se o id existe
    assert (await client.get("/api/v1/favorites", headers=headers_b)).json()["items"] == []
    mine = (await client.get("/api/v1/favorites", headers=headers_a)).json()
    assert mine["total"] == 1 and mine["items"][0]["note"] == "só da Ana"


async def test_same_record_can_be_saved_by_two_users(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    _, a = await make_user(db, "ana")
    _, b = await make_user(db, "bia")
    assert (
        await client.post("/api/v1/favorites", json={"record": record()}, headers=a)
    ).status_code == 201
    assert (
        await client.post("/api/v1/favorites", json={"record": record()}, headers=b)
    ).status_code == 201


async def test_note_validation(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    _, headers = await make_user(db, "ana")
    too_long = "a" * 1001
    assert (
        await client.post(
            "/api/v1/favorites", json={"record": record(), "note": too_long}, headers=headers
        )
    ).status_code == 422
    created = await client.post(
        "/api/v1/favorites", json={"record": record(), "note": "a" * 1000}, headers=headers
    )
    assert created.status_code == 201
    fav = created.json()["id"]
    assert (
        await client.patch(f"/api/v1/favorites/{fav}", json={"note": too_long}, headers=headers)
    ).status_code == 422
    cleared = await client.patch(f"/api/v1/favorites/{fav}", json={"note": "   "}, headers=headers)
    assert cleared.status_code == 200 and cleared.json()["note"] is None
    updated = await client.patch(f"/api/v1/favorites/{fav}", json={"note": "nova"}, headers=headers)
    assert updated.json()["note"] == "nova"


@pytest.mark.parametrize("bad_url", ["javascript:alert(1)", "data:text/html,x", "ftp://x.org/a"])
async def test_record_with_invalid_url_is_422(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession], bad_url: str
) -> None:
    _, headers = await make_user(db, "ana")
    response = await client.post(
        "/api/v1/favorites", json={"record": record(url=bad_url)}, headers=headers
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_oversized_record_is_422(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    _, headers = await make_user(db, "ana")
    huge = record(abstract="x" * 30_000)
    response = await client.post("/api/v1/favorites", json={"record": huge}, headers=headers)
    assert response.status_code == 422
    assert "grande demais" in response.json()["error"]["message"]


async def test_limit_of_2000_favorites(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    user_id, headers = await make_user(db, "ana")
    async with db() as session:
        await session.execute(
            text(
                "INSERT INTO favorites (user_id, record_id, record_snapshot) "
                "SELECT :u, 'src:x:' || g, '{}'::jsonb FROM generate_series(1, 2000) g"
            ),
            {"u": user_id},
        )
        await session.commit()
    blocked = await client.post("/api/v1/favorites", json={"record": record()}, headers=headers)
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "favorites_limit_reached"
    assert "2000" in blocked.json()["error"]["message"]


async def test_list_pagination_order_and_search(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    _, headers = await make_user(db, "ana")
    for n in range(1, 6):
        title = "Robótica na escola" if n == 3 else f"Trabalho comum {n}"
        note = "revisar capítulo 100%" if n == 4 else None
        await client.post(
            "/api/v1/favorites",
            json={"record": record(n, title=title), "note": note},
            headers=headers,
        )
    page1 = (await client.get("/api/v1/favorites", params={"page_size": 2}, headers=headers)).json()
    page3 = (
        await client.get("/api/v1/favorites", params={"page_size": 2, "page": 3}, headers=headers)
    ).json()
    assert page1["total"] == 5 and len(page1["items"]) == 2 and len(page3["items"]) == 1
    assert [i["record"]["id"] for i in page1["items"]] == [
        "doi:10.1234/fav5",
        "doi:10.1234/fav4",
    ]  # recentes primeiro
    by_title = (
        await client.get("/api/v1/favorites", params={"q": "robótica"}, headers=headers)
    ).json()
    assert [i["record"]["id"] for i in by_title["items"]] == ["doi:10.1234/fav3"]
    by_note = (await client.get("/api/v1/favorites", params={"q": "100%"}, headers=headers)).json()
    assert [i["record"]["id"] for i in by_note["items"]] == ["doi:10.1234/fav4"]
    wildcard = (await client.get("/api/v1/favorites", params={"q": "%"}, headers=headers)).json()
    assert wildcard["total"] == 1  # % é texto literal, não curinga
    assert (
        await client.get(
            "/api/v1/favorites", params={"q": "'; DROP TABLE favorites;--"}, headers=headers
        )
    ).status_code == 200


async def test_delete_removes_and_returns_204(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    _, headers = await make_user(db, "ana")
    fav = (
        await client.post("/api/v1/favorites", json={"record": record()}, headers=headers)
    ).json()["id"]
    response = await client.delete(f"/api/v1/favorites/{fav}", headers=headers)
    assert response.status_code == 204 and response.content == b""
    assert (await client.get("/api/v1/favorites", headers=headers)).json()["total"] == 0
    assert (await client.delete(f"/api/v1/favorites/{fav}", headers=headers)).status_code == 404


async def test_invalid_favorite_id_is_422(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    _, headers = await make_user(db, "ana")
    assert (await client.delete("/api/v1/favorites/nao-e-uuid", headers=headers)).status_code == 422


class OneSource:
    slug, name, kind, supports_year_sort = "openalex", "OpenAlex", "api", True

    def is_enabled(self) -> bool:
        return True

    async def availability(self) -> tuple[bool, str | None]:
        return True, None

    async def search(self, query: SourceQuery) -> SourcePage:
        records = [
            RecordOut(
                id=f"doi:10.1234/fav{n}",
                title=f"Letramento digital número {n}",
                authors=[AuthorOut(name="Maria Souza")],
                sources=[SourceRef(source="openalex", source_id=str(n))],
            )
            for n in (1, 2)
        ]
        return SourcePage(records=records, total=2)


async def test_search_marks_saved_items_as_favorite(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    _, headers = await make_user(db, "ana")
    await client.post("/api/v1/favorites", json={"record": record(2)}, headers=headers)
    service = SearchService([OneSource()], Settings(_env_file=None))  # type: ignore[call-arg,list-item]
    client.app.dependency_overrides[get_search_service] = lambda: service  # type: ignore[attr-defined]
    body = (await client.get("/api/v1/search", params={"q": "letramento"}, headers=headers)).json()
    assert {r["id"]: r["is_favorite"] for r in body["results"]} == {
        "doi:10.1234/fav1": False,
        "doi:10.1234/fav2": True,
    }
    await client.delete(
        f"/api/v1/favorites/{(await client.get('/api/v1/favorites', headers=headers)).json()['items'][0]['id']}",
        headers=headers,
    )
    again = (await client.get("/api/v1/search", params={"q": "letramento"}, headers=headers)).json()
    assert not any(r["is_favorite"] for r in again["results"])


async def test_deleting_the_user_deletes_the_favorites(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    user_id, headers = await make_user(db, "ana")
    await client.post("/api/v1/favorites", json={"record": record()}, headers=headers)
    async with db() as session:
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()
        left = (
            await session.execute(
                select(func.count()).select_from(Favorite).where(Favorite.user_id == user_id)
            )
        ).scalar_one()
    assert left == 0
