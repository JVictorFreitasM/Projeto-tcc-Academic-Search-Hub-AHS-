import asyncio
import time
import uuid

import pytest
from pydantic import ValidationError

from app.connectors.base import SourcePage, SourceQuery, SourceStatus
from app.core.config import Settings
from app.core.errors import UpstreamError, ValidationAppError
from app.schemas.common import RecordType
from app.schemas.record import AuthorOut, RecordOut, SourceRef
from app.schemas.search import SearchParams
from app.services import search_service
from app.services.search_service import NOT_SELECTED, SearchService

pytestmark = pytest.mark.unit


def make_record(
    source: str, n: int, *, year: int | None = 2020, doi: str | None = None
) -> RecordOut:
    return RecordOut(
        id=f"doi:{doi}" if doi else f"src:{source}:{n}",
        title=f"Trabalho {source} número {n} sobre um assunto específico",
        authors=[AuthorOut(name=f"Autor {source}{n} Sobrenome{source}{n}")],
        year=year,
        doi=doi,
        sources=[SourceRef(source=source, source_id=str(n))],
    )


class FakeConnector:
    def __init__(
        self,
        slug: str,
        records: list[RecordOut] | None = None,
        *,
        total: int | None = None,
        status: SourceStatus = SourceStatus.OK,
        delay: float = 0,
        error: Exception | None = None,
        available: tuple[bool, str | None] = (True, None),
        supports_year_sort: bool = True,
        message: str | None = None,
    ) -> None:
        self.slug = slug
        self.name = slug.upper()
        self.records = records if records is not None else [make_record(slug, i) for i in range(10)]
        self.total = total
        self.status = status
        self.delay = delay
        self.error = error
        self.available = available
        self.supports_year_sort = supports_year_sort
        self.message = message
        self.queries: list[SourceQuery] = []

    def is_enabled(self) -> bool:
        return self.available[0]

    async def availability(self) -> tuple[bool, str | None]:
        return self.available

    async def search(self, query: SourceQuery) -> SourcePage:
        self.queries.append(query)
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.error:
            raise self.error
        records = self.records[: query.page_size]
        total = self.total if self.total is not None else len(self.records)
        return SourcePage(records=records, total=total, status=self.status, message=self.message)


def settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


def service(*connectors: FakeConnector, **overrides: object) -> SearchService:
    return SearchService(connectors, settings(**overrides))


def params(**overrides: object) -> SearchParams:
    return SearchParams(**{"q": "educação", **overrides})  # type: ignore[arg-type]


async def test_all_ok_splits_page_interleaves_and_sums_totals() -> None:
    a, b, c = (
        FakeConnector("openalex", total=100),
        FakeConnector("core", total=50),
        FakeConnector("bdtd", total=7),
    )
    response = await service(a, b, c).search(params(page_size=6, page=2))
    assert [q.page_size for q in a.queries + b.queries + c.queries] == [2, 2, 2]  # ceil(6/3)
    assert all(q.page == 2 for q in a.queries)
    assert [r.sources[0].source for r in response.results] == ["openalex", "core", "bdtd"] * 2
    assert response.total_estimated == 157 and response.total_is_estimate is True
    assert {k: v.count for k, v in response.sources_status.items()} == {
        "openalex": 2,
        "core": 2,
        "bdtd": 2,
    }
    assert response.page == 2 and response.page_size == 6 and response.query == "educação"


async def test_cut_to_page_size_when_split_rounds_up() -> None:
    response = await service(FakeConnector("openalex"), FakeConnector("core")).search(
        params(page_size=5)
    )
    assert len(response.results) == 5  # 2 fontes x ceil(5/2)=3 -> 6, cortado em 5


async def test_slow_connector_does_not_delay_beyond_global_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(search_service, "GLOBAL_TIMEOUT_MARGIN", 0.0)
    slow = FakeConnector("openalex", delay=10)
    fast = FakeConnector("core")
    started = time.perf_counter()
    response = await service(slow, fast, source_timeout_seconds=0.2).search(params())
    assert time.perf_counter() - started < 3
    assert response.sources_status["openalex"].status is SourceStatus.TIMEOUT
    assert response.sources_status["core"].status is SourceStatus.OK
    assert response.results and all(r.sources[0].source == "core" for r in response.results)


async def test_failing_source_does_not_stop_the_others() -> None:
    broken = FakeConnector("openalex", error=RuntimeError("senha do banco é hunter2"))
    response = await service(broken, FakeConnector("core")).search(params())
    status = response.sources_status["openalex"]
    assert status.status is SourceStatus.ERROR and status.count == 0
    assert "hunter2" not in (status.message or "")
    assert response.sources_status["core"].status is SourceStatus.OK
    assert len(response.results) > 0


async def test_rate_limited_source_is_reported() -> None:
    limited = FakeConnector(
        "openalex", records=[], status=SourceStatus.RATE_LIMITED, message="Limite atingido."
    )
    response = await service(limited, FakeConnector("core")).search(params())
    assert response.sources_status["openalex"].status is SourceStatus.RATE_LIMITED
    assert response.sources_status["openalex"].message == "Limite atingido."


async def test_all_failing_raises_502_with_sources_status() -> None:
    a = FakeConnector("openalex", error=RuntimeError("x"))
    b = FakeConnector("core", status=SourceStatus.TIMEOUT, records=[])
    with pytest.raises(UpstreamError) as info:
        await service(a, b).search(params())
    assert info.value.status_code == 502
    assert info.value.extra is not None
    assert set(info.value.extra["sources_status"]) == {"openalex", "core"}
    assert info.value.extra["sources_status"]["core"]["status"] == "timeout"


async def test_all_disabled_raises_502() -> None:
    a = FakeConnector("openalex", available=(False, "Chave do OpenAlex não configurada."))
    b = FakeConnector("bdtd", available=(False, "Fonte ainda não colhida"))
    with pytest.raises(UpstreamError) as info:
        await service(a, b).search(params())
    assert info.value.extra is not None
    statuses = info.value.extra["sources_status"]
    assert statuses["bdtd"] == {
        "status": "disabled",
        "count": 0,
        "total": 0,
        "message": "Fonte ainda não colhida",
    }
    assert not a.queries and not b.queries  # nada foi consultado


async def test_unavailable_source_does_not_count_in_k() -> None:
    ok = FakeConnector("openalex")
    off = FakeConnector("core", available=(False, "Chave do CORE não configurada."))
    response = await service(ok, off).search(params(page_size=10))
    assert ok.queries[0].page_size == 10  # k = 1
    assert not off.queries
    assert response.sources_status["core"].status is SourceStatus.DISABLED


async def test_unselected_sources_appear_disabled() -> None:
    a, b = FakeConnector("openalex"), FakeConnector("core")
    response = await service(a, b).search(params(sources=["core"]))
    assert not a.queries
    assert response.sources_status["openalex"].status is SourceStatus.DISABLED
    assert response.sources_status["openalex"].message == NOT_SELECTED
    assert b.queries[0].page_size == 20


async def test_unknown_source_is_a_validation_error() -> None:
    with pytest.raises(ValidationAppError) as info:
        await service(FakeConnector("openalex")).search(params(sources=["foo"]))
    assert "openalex" in info.value.message and info.value.details


async def test_duplicate_between_sources_becomes_one_record_with_two_sources() -> None:
    a = FakeConnector("openalex", records=[make_record("openalex", 1, doi="10.5/x")])
    b = FakeConnector("core", records=[make_record("core", 9, doi="10.5/X")])
    response = await service(a, b).search(params())
    assert len(response.results) == 1
    assert [s.source for s in response.results[0].sources] == ["openalex", "core"]


async def test_year_desc_sorts_page_and_flags_sources_without_support() -> None:
    a = FakeConnector(
        "openalex",
        records=[make_record("openalex", 1, year=2010), make_record("openalex", 2, year=None)],
        supports_year_sort=False,
    )
    b = FakeConnector("core", records=[make_record("core", 3, year=2023)])
    response = await service(a, b).search(params(sort="year_desc"))
    assert [r.year for r in response.results] == [2023, 2010, None]  # nulos por último
    assert "ordena" in (response.sources_status["openalex"].message or "")
    assert response.sources_status["core"].message is None
    assert a.queries[0].sort == "year_desc"


async def test_filters_are_passed_to_sources() -> None:
    a = FakeConnector("openalex")
    await service(a).search(
        params(year_from=2000, year_to=2010, types=[RecordType.THESIS, RecordType.BOOK])
    )
    query = a.queries[0]
    assert (query.year_from, query.year_to) == (2000, 2010)
    assert query.types == (RecordType.THESIS, RecordType.BOOK)
    assert query.q == "educação"


async def test_total_none_falls_back_to_count() -> None:
    class NoTotal(FakeConnector):
        async def search(self, query: SourceQuery) -> SourcePage:
            return SourcePage(records=self.records[:3], total=None)

    response = await service(NoTotal("openalex")).search(params())
    assert response.total_estimated == 3


async def test_favorites_are_marked_for_logged_user() -> None:
    a = FakeConnector("openalex", records=[make_record("openalex", 1), make_record("openalex", 2)])
    seen: dict[str, object] = {}

    async def lookup(user_id: uuid.UUID, ids: list[str]) -> set[str]:
        seen.update(user=user_id, ids=ids)
        return {"src:openalex:2"}

    user = uuid.uuid4()
    svc = SearchService([a], settings(), favorite_lookup=lookup)
    response = await svc.search(params(), user_id=user)
    assert [r.is_favorite for r in response.results] == [False, True]
    assert seen["user"] == user and seen["ids"] == ["src:openalex:1", "src:openalex:2"]
    visitor = await svc.search(params())
    assert not any(r.is_favorite for r in visitor.results)


async def test_duration_only_in_development() -> None:
    dev = await service(FakeConnector("openalex"), app_env="development").search(params())
    assert "duration_ms" in dev.model_dump(mode="json")["sources_status"]["openalex"]
    prod = await service(
        FakeConnector("openalex"), app_env="production", secret_key="k" * 40
    ).search(params())
    assert "duration_ms" not in prod.model_dump(mode="json")["sources_status"]["openalex"]


@pytest.mark.parametrize(
    "bad",
    [
        {"q": "a"},
        {"q": "   x   "},
        {"q": "x" * 201},
        {"year_from": 1800},
        {"year_to": 3000},
        {"year_from": 2020, "year_to": 2010},
        {"page": 0},
        {"page_size": 0},
        {"page_size": 51},
        {"sort": "aleatorio"},
        {"types": ["filme"]},
    ],
)
def test_invalid_params(bad: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        SearchParams(**{"q": "educação", **bad})  # type: ignore[arg-type]


def test_query_is_trimmed() -> None:
    assert SearchParams(q="  educação  ").q == "educação"
