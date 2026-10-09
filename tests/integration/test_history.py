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
from app.models import SearchHistory, User
from app.schemas.common import RecordType
from app.schemas.record import RecordOut, SourceRef
from app.schemas.search import SearchParams
from app.services import history_service
from app.services.search_service import SearchService

pytestmark = pytest.mark.integration

SECRET = "s" * 40


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
        await session.execute(delete(User).where(User.email.like("%@hist.com")))
        await session.commit()


class OneSource:
    slug, name, kind, supports_year_sort = "openalex", "OpenAlex", "api", True

    def is_enabled(self) -> bool:
        return True

    async def availability(self) -> tuple[bool, str | None]:
        return True, None

    async def search(self, query: SourceQuery) -> SourcePage:
        record = RecordOut(
            id="src:openalex:1",
            title="Um trabalho",
            sources=[SourceRef(source="openalex", source_id="1")],
        )
        return SourcePage(records=[record], total=42)


@pytest.fixture
async def client(
    env: None, db: async_sessionmaker[AsyncSession]
) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app()
    service = SearchService([OneSource()], Settings(_env_file=None))  # type: ignore[call-arg,list-item]
    app.dependency_overrides[get_search_service] = lambda: service
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
            email=f"{name}.{uuid.uuid4().hex[:6]}@hist.com",
            full_name=name,
            password_hash=hash_password("Senha12345"),
            consent_at=datetime.now(UTC),
            consent_policy_version="1.0",
        )
        session.add(user)
        await session.commit()
        token = create_access_token(user.id, Settings(_env_file=None, secret_key=SECRET))  # type: ignore[call-arg]
        return user.id, {"Authorization": f"Bearer {token}"}


async def history_rows(
    db: async_sessionmaker[AsyncSession], user_id: uuid.UUID
) -> list[SearchHistory]:
    async with db() as session:
        rows = await session.execute(
            select(SearchHistory)
            .where(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.created_at, SearchHistory.id)
        )
        return list(rows.scalars())


def params(q: str = "educação", **overrides: Any) -> SearchParams:
    return SearchParams(q=q, **overrides)


async def test_visitor_search_records_nothing(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession], engine: AsyncEngine
) -> None:
    async with db() as session:
        before = (
            await session.execute(select(func.count()).select_from(SearchHistory))
        ).scalar_one()
    assert (await client.get("/api/v1/search", params={"q": "educação"})).status_code == 200
    async with db() as session:
        after = (
            await session.execute(select(func.count()).select_from(SearchHistory))
        ).scalar_one()
    assert after == before


async def test_logged_user_search_is_recorded_after_the_response(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    user_id, headers = await make_user(db, "ana")
    response = await client.get(
        "/api/v1/search",
        params={"q": "educação", "year_from": 2020, "type": "thesis,article", "sort": "year_desc"},
        headers=headers,
    )
    assert response.status_code == 200
    (row,) = await history_rows(db, user_id)
    assert row.query == "educação" and row.result_count_estimated == 42
    assert row.filters == {
        "sources": None,
        "year_from": 2020,
        "year_to": None,
        "types": ["article", "thesis"],
        "sort": "year_desc",
    }


async def test_repeated_search_in_sequence_is_recorded_once(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    user_id, headers = await make_user(db, "ana")
    for _ in range(3):
        await client.get("/api/v1/search", params={"q": "educação"}, headers=headers)
    await client.get(
        "/api/v1/search", params={"q": "educação", "page": 2}, headers=headers
    )  # outra página
    assert len(await history_rows(db, user_id)) == 1


async def test_same_query_with_other_filters_or_after_another_query_is_recorded(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    user_id, headers = await make_user(db, "ana")
    await client.get("/api/v1/search", params={"q": "educação"}, headers=headers)
    await client.get("/api/v1/search", params={"q": "educação", "year_from": 2020}, headers=headers)
    await client.get("/api/v1/search", params={"q": "saúde"}, headers=headers)
    await client.get("/api/v1/search", params={"q": "educação"}, headers=headers)  # A, B, C, A
    assert [r.query for r in await history_rows(db, user_id)] == [
        "educação",
        "educação",
        "saúde",
        "educação",
    ]


async def test_the_201st_search_removes_the_oldest(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    user_id, _ = await make_user(db, "ana")
    async with db() as session:
        await session.execute(
            text(
                "INSERT INTO search_history (user_id, query, filters, created_at) "
                "SELECT :u, 'consulta ' || g, '{}'::jsonb, now() - make_interval(secs => 1000 - g) "
                "FROM generate_series(1, 200) g"
            ),
            {"u": user_id},
        )
        await session.commit()
    assert len(await history_rows(db, user_id)) == 200
    assert await history_service.record_search(user_id, params("a 201ª"), 5, db) is True
    rows = await history_rows(db, user_id)
    assert len(rows) == 200
    assert rows[0].query == "consulta 2"  # a "consulta 1" (mais antiga) saiu
    assert rows[-1].query == "a 201ª"


async def test_user_only_sees_own_history(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    _, a = await make_user(db, "ana")
    _, b = await make_user(db, "bia")
    await client.get("/api/v1/search", params={"q": "da ana"}, headers=a)
    await client.get("/api/v1/search", params={"q": "da bia"}, headers=b)
    mine = (await client.get("/api/v1/history", headers=a)).json()
    assert [i["query"] for i in mine["items"]] == ["da ana"] and mine["total"] == 1
    other = (await client.get("/api/v1/history", headers=b)).json()
    assert [i["query"] for i in other["items"]] == ["da bia"]


async def test_history_requires_login(client: httpx.AsyncClient) -> None:
    for call in (
        client.get("/api/v1/history"),
        client.delete("/api/v1/history"),
        client.delete(f"/api/v1/history/{uuid.uuid4()}"),
    ):
        assert (await call).status_code == 401


async def test_list_is_paginated_most_recent_first(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    user_id, headers = await make_user(db, "ana")
    for q in ("um", "dois", "tres", "quatro", "cinco"):
        await history_service.record_search(user_id, params(q + "!"), 1, db)
    first = (await client.get("/api/v1/history", params={"page_size": 2}, headers=headers)).json()
    last = (
        await client.get("/api/v1/history", params={"page_size": 2, "page": 3}, headers=headers)
    ).json()
    assert [i["query"] for i in first["items"]] == ["cinco!", "quatro!"] and first["total"] == 5
    assert [i["query"] for i in last["items"]] == ["um!"]


async def test_delete_one_and_clear_all_only_touch_own_rows(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    a_id, a = await make_user(db, "ana")
    b_id, b = await make_user(db, "bia")
    for q in ("um!", "dois!"):
        await history_service.record_search(a_id, params(q), 1, db)
    await history_service.record_search(b_id, params("da bia!"), 1, db)
    items = (await client.get("/api/v1/history", headers=a)).json()["items"]
    target = items[0]["id"]

    assert (
        await client.delete(f"/api/v1/history/{target}", headers=b)
    ).status_code == 404  # de outra pessoa
    assert (await client.delete(f"/api/v1/history/{target}", headers=a)).status_code == 204
    assert (await client.delete(f"/api/v1/history/{target}", headers=a)).status_code == 404
    assert len(await history_rows(db, a_id)) == 1

    assert (await client.delete("/api/v1/history", headers=a)).status_code == 204
    assert await history_rows(db, a_id) == []
    assert len(await history_rows(db, b_id)) == 1


async def test_history_failure_does_not_change_the_search_status(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession], monkeypatch: pytest.MonkeyPatch
) -> None:
    _, headers = await make_user(db, "ana")

    async def broken(*args: Any, **kwargs: Any) -> bool:
        raise RuntimeError("banco indisponível")

    monkeypatch.setattr(history_service, "record_search", broken)
    response = await client.get("/api/v1/search", params={"q": "educação"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["results"]


async def test_filters_ignore_source_order_and_page() -> None:
    a = params(sources=["core", "openalex"], types=[RecordType.THESIS, RecordType.ARTICLE])
    b = params(sources=["openalex", "core"], types=[RecordType.ARTICLE, RecordType.THESIS], page=3)
    assert history_service.filters_of(a) == history_service.filters_of(b)


async def test_deleting_the_user_deletes_the_history(
    client: httpx.AsyncClient, db: async_sessionmaker[AsyncSession]
) -> None:
    user_id, headers = await make_user(db, "ana")
    await client.get("/api/v1/search", params={"q": "educação"}, headers=headers)
    assert len(await history_rows(db, user_id)) == 1
    async with db() as session:
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()
    assert await history_rows(db, user_id) == []
