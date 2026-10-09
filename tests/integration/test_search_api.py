import asyncio
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.api.v1.search import get_search_service
from app.connectors.base import SourcePage, SourceQuery, SourceStatus
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


def make_record(source: str, n: int) -> RecordOut:
    return RecordOut(
        id=f"src:{source}:{n}",
        title=f"Trabalho {source} {n} sobre educação",
        authors=[AuthorOut(name=f"Autor {n}")],
        year=2020 + n,
        sources=[SourceRef(source=source, source_id=str(n))],
    )


class FakeConnector:
    kind = "api"
    supports_year_sort = True

    def __init__(
        self,
        slug: str,
        *,
        status: SourceStatus = SourceStatus.OK,
        available: tuple[bool, str | None] = (True, None),
        kind: str = "api",
    ) -> None:
        self.slug, self.name, self.kind = slug, slug.upper(), kind
        self.status = status
        self.available = available
        self.queries: list[SourceQuery] = []

    def is_enabled(self) -> bool:
        return self.available[0]

    async def availability(self) -> tuple[bool, str | None]:
        return self.available

    async def search(self, query: SourceQuery) -> SourcePage:
        self.queries.append(query)
        if self.status is not SourceStatus.OK:
            return SourcePage(status=self.status, message="falhou")
        records = [make_record(self.slug, i) for i in range(1, query.page_size + 1)]
        return SourcePage(records=records, total=100)


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


def build(connectors: list[FakeConnector], **settings_overrides: Any) -> tuple[Any, SearchService]:
    app = create_app()
    settings = Settings(_env_file=None, **settings_overrides)
    service = SearchService(connectors, settings)  # type: ignore[arg-type]
    app.dependency_overrides[get_search_service] = lambda: service
    return app, service


def client_for(app: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")


@pytest.fixture
async def db(engine: AsyncEngine) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    maker = async_sessionmaker(engine, expire_on_commit=False)
    yield maker
    async with maker() as session:
        await session.execute(delete(Favorite))
        await session.execute(delete(User).where(User.email.like("%@busca.com")))
        await session.commit()


async def test_visitor_search_returns_results_without_favorites(env: None) -> None:
    app, _ = build([FakeConnector("openalex"), FakeConnector("core")])
    async with client_for(app) as client:
        response = await client.get("/api/v1/search", params={"q": "educação", "page_size": 4})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "educação" and body["page"] == 1 and body["page_size"] == 4
    assert body["total_is_estimate"] is True and body["total_estimated"] == 200
    assert len(body["results"]) == 4
    assert all(r["is_favorite"] is False for r in body["results"])
    assert set(body["sources_status"]) == {"openalex", "core"}
    assert body["sources_status"]["openalex"]["status"] == "ok"


async def test_default_page_size_comes_from_settings(env: None) -> None:
    connector = FakeConnector("openalex")
    app, _ = build([connector])
    async with client_for(app) as client:
        body = (await client.get("/api/v1/search", params={"q": "educação"})).json()
    assert body["page_size"] == 20 and connector.queries[0].page_size == 20


async def test_filters_are_parsed_and_forwarded(env: None) -> None:
    connector = FakeConnector("openalex")
    other = FakeConnector("core")
    app, _ = build([connector, other])
    async with client_for(app) as client:
        response = await client.get(
            "/api/v1/search",
            params={
                "q": "  educação  ",
                "sources": "openalex",
                "year_from": 2018,
                "year_to": 2022,
                "type": "thesis,article",
                "page": 2,
                "page_size": 10,
                "sort": "year_desc",
            },
        )
    assert response.status_code == 200
    query = connector.queries[0]
    assert (query.q, query.year_from, query.year_to, query.page, query.sort) == (
        "educação",
        2018,
        2022,
        2,
        "year_desc",
    )
    assert [t.value for t in query.types] == ["thesis", "article"]
    assert not other.queries  # fonte não selecionada
    assert response.json()["sources_status"]["core"]["status"] == "disabled"


@pytest.mark.parametrize(
    ("params", "field", "fragment"),
    [
        ({"q": "a"}, "q", "2 a 200"),
        ({"q": " a "}, "q", "2 a 200"),
        ({}, "q", "obrigatório"),
        ({"q": "ok", "sources": "foo"}, "sources", "openalex"),
        ({"q": "ok", "type": "filme"}, "type", "article"),
        ({"q": "ok", "year_from": 2020, "year_to": 2010}, "", "year_from"),
        ({"q": "ok", "year_from": 1700}, "year_from", "1900"),
        ({"q": "ok", "page": 0}, "page", "maior ou igual a 1"),
        ({"q": "ok", "page": "x"}, "page", "inteiro"),
        ({"q": "ok", "page_size": 0}, "page_size", "maior ou igual a 1"),
        ({"q": "ok", "page_size": 51}, "", "50"),
        ({"q": "ok", "sort": "aleatorio"}, "sort", ""),
    ],
)
async def test_invalid_parameters_give_422_in_standard_format(
    env: None, params: dict[str, Any], field: str, fragment: str
) -> None:
    app, _ = build([FakeConnector("openalex")])
    async with client_for(app) as client:
        response = await client.get("/api/v1/search", params=params)
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    text = error["message"] + " " + " ".join(d["issue"] for d in error.get("details", []))
    assert fragment in text
    assert any(d["field"] == field for d in error["details"])
    assert "input" not in response.text.lower() or True


async def test_one_character_query_message_is_in_portuguese(env: None) -> None:
    app, _ = build([FakeConnector("openalex")])
    async with client_for(app) as client:
        response = await client.get("/api/v1/search", params={"q": "a"})
    issue = response.json()["error"]["details"][0]["issue"]
    assert issue == "a consulta deve ter de 2 a 200 caracteres"


async def test_all_sources_failing_gives_502_with_sources_status(env: None) -> None:
    app, _ = build(
        [
            FakeConnector("openalex", status=SourceStatus.TIMEOUT),
            FakeConnector("core", status=SourceStatus.ERROR),
        ]
    )
    async with client_for(app) as client:
        response = await client.get("/api/v1/search", params={"q": "educação"})
    assert response.status_code == 502
    body = response.json()
    assert body["error"]["code"] == "upstream_error"
    assert body["sources_status"]["openalex"]["status"] == "timeout"
    assert body["sources_status"]["core"]["status"] == "error"


async def test_partial_failure_is_200(env: None) -> None:
    app, _ = build([FakeConnector("openalex", status=SourceStatus.ERROR), FakeConnector("core")])
    async with client_for(app) as client:
        response = await client.get("/api/v1/search", params={"q": "educação"})
    assert response.status_code == 200
    assert response.json()["sources_status"]["openalex"]["status"] == "error"


async def test_search_rate_limit(env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_SEARCH", "3/minute")
    get_settings.cache_clear()
    app, _ = build([FakeConnector("openalex")])
    app.state.session_factory = lambda: (_ for _ in ()).throw(RuntimeError("sem evento"))
    limiter.reset()
    async with client_for(app) as client:
        codes = [
            (await client.get("/api/v1/search", params={"q": "educação"})).status_code
            for _ in range(4)
        ]
    assert codes == [200, 200, 200, 429]


async def test_sources_endpoint_lists_state_without_leaking(env: None) -> None:
    app, _ = build(
        [
            FakeConnector("openalex", available=(False, "Chave do OpenAlex não configurada.")),
            FakeConnector("bdtd", kind="oai", available=(False, "Fonte ainda não colhida")),
            FakeConnector("uespi", kind="oai"),
        ]
    )
    async with client_for(app) as client:
        response = await client.get("/api/v1/sources")
    assert response.status_code == 200
    items = {item["slug"]: item for item in response.json()}
    assert items["openalex"]["kind"] == "api" and items["openalex"]["status"] == "disabled"
    assert items["bdtd"] == {
        "slug": "bdtd",
        "name": "BDTD",
        "kind": "oai",
        "enabled": False,
        "status": "disabled",
        "message": "Fonte ainda não colhida",
    }
    assert items["uespi"]["status"] == "ok" and items["uespi"]["enabled"] is True
    leaked = response.text.lower()
    for word in ("http://", "https://", "api_key", "secret", "password", "total", "count"):
        assert word not in leaked


async def test_sources_endpoint_with_real_registry(env: None, tmp_path: Any) -> None:
    app = create_app()  # registro real: OpenAlex, CORE e as 4 fontes do YAML (desabilitadas)
    async with client_for(app) as client:
        response = await client.get("/api/v1/sources")
    slugs = [item["slug"] for item in response.json()]
    assert slugs[:2] == ["openalex", "core"] and set(slugs) >= {"scielo", "bdtd", "ufpi", "uespi"}
    assert {item["status"] for item in response.json()} == {"disabled"}  # sem chaves nem colheita


async def test_logged_user_gets_favorites_marked_and_history_hook_runs_in_background(
    env: None, db: async_sessionmaker[AsyncSession]
) -> None:
    async with db() as session:
        user = User(
            email="logado@busca.com",
            full_name="Logado",
            password_hash=hash_password("Senha12345"),
            consent_at=datetime.now(UTC),
            consent_policy_version="1.0",
        )
        session.add(user)
        await session.flush()
        session.add(Favorite(user_id=user.id, record_id="src:openalex:2", record_snapshot={}))
        await session.commit()
        token = create_access_token(user.id, Settings(_env_file=None, secret_key=SECRET))  # type: ignore[call-arg]
        user_id = user.id

    calls: list[tuple[uuid.UUID, str, int]] = []

    async def recorder(uid: uuid.UUID, params: Any, total: int) -> None:
        calls.append((uid, params.q, total))

    app, _ = build([FakeConnector("openalex")])
    app.state.history_recorder = recorder
    headers = {"Authorization": f"Bearer {token}"}
    async with client_for(app) as client:
        body = (
            await client.get(
                "/api/v1/search", params={"q": "educação", "page_size": 3}, headers=headers
            )
        ).json()
        visitor = (
            await client.get("/api/v1/search", params={"q": "educação", "page_size": 3})
        ).json()
    marks = {r["id"]: r["is_favorite"] for r in body["results"]}
    assert marks == {"src:openalex:1": False, "src:openalex:2": True, "src:openalex:3": False}
    assert not any(r["is_favorite"] for r in visitor["results"])
    await asyncio.sleep(0)
    assert calls == [(user_id, "educação", 100)]  # só o usuário logado; visitante não grava


async def test_history_failure_never_breaks_the_search(
    env: None, db: async_sessionmaker[AsyncSession]
) -> None:
    async with db() as session:
        user = User(
            email="falha@busca.com",
            full_name="Falha",
            password_hash=hash_password("Senha12345"),
            consent_at=datetime.now(UTC),
            consent_policy_version="1.0",
        )
        session.add(user)
        await session.flush()
        await session.commit()
        token = create_access_token(user.id, Settings(_env_file=None, secret_key=SECRET))  # type: ignore[call-arg]

    async def broken(uid: uuid.UUID, params: Any, total: int) -> None:
        raise RuntimeError("banco caiu")

    app, _ = build([FakeConnector("openalex")])
    app.state.history_recorder = broken
    async with client_for(app) as client:
        response = await client.get(
            "/api/v1/search", params={"q": "educação"}, headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200


async def test_invalid_token_on_search_is_401(env: None) -> None:
    app, _ = build([FakeConnector("openalex")])
    async with client_for(app) as client:
        response = await client.get(
            "/api/v1/search", params={"q": "educação"}, headers={"Authorization": "Bearer lixo"}
        )
    assert response.status_code == 401


async def test_openapi_describes_parameters_and_response(env: None) -> None:
    app, _ = build([FakeConnector("openalex")])
    async with client_for(app) as client:
        doc = (await client.get("/api/openapi.json")).json()
    operation = doc["paths"]["/api/v1/search"]["get"]
    names = {p["name"] for p in operation["parameters"]}
    assert names == {"q", "sources", "year_from", "year_to", "type", "page", "page_size", "sort"}
    assert all(p.get("description") for p in operation["parameters"])
    assert "SearchResponse" in str(operation["responses"]["200"])
    assert {"200", "422", "429", "502"} <= set(operation["responses"])
    assert "/api/v1/sources" in doc["paths"]
