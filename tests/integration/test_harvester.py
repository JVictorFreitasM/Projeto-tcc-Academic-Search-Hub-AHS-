from collections.abc import AsyncIterator

import httpx
import pytest
import respx
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.harvest.harvester import HarvestError, harvest_source
from app.harvest.oai_sources import OaiSourceConfig
from app.models import HarvestRun, OaiRecord
from app.schemas.common import RecordType
from tests.oai_support import OAI_URL, oai_server, xml_response

pytestmark = pytest.mark.integration

SLUG = "exemplo"


class Sleeper:
    async def __call__(self, seconds: float) -> None:
        return None


def settings(**overrides: object) -> Settings:
    data: dict[str, object] = {"contact_email": "dev@exemplo.com", "oai_harvest_delay_seconds": 0}
    return Settings(_env_file=None, **{**data, **overrides})  # type: ignore[arg-type]


def source(**overrides: object) -> OaiSourceConfig:
    data: dict[str, object] = {
        "slug": SLUG,
        "name": "Exemplo",
        "base_url": OAI_URL,
        "enabled": True,
        "default_type": RecordType.THESIS,
    }
    return OaiSourceConfig(**{**data, **overrides})  # type: ignore[arg-type]


@pytest.fixture
async def factory(engine: AsyncEngine) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """A colheita confirma (commit) por conta própria: limpamos a fonte de teste antes e depois."""
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def clean() -> None:
        async with maker() as session:
            await session.execute(delete(OaiRecord).where(OaiRecord.source == SLUG))
            await session.execute(delete(HarvestRun).where(HarvestRun.source == SLUG))
            await session.commit()

    await clean()
    yield maker
    await clean()


async def count_records(factory: async_sessionmaker[AsyncSession], **filters: object) -> int:
    async with factory() as session:
        query = select(func.count()).select_from(OaiRecord).where(OaiRecord.source == SLUG)
        for key, value in filters.items():
            query = query.where(getattr(OaiRecord, key) == value)
        return (await session.execute(query)).scalar_one()


async def run(factory: async_sessionmaker[AsyncSession], **kwargs: object):  # type: ignore[no-untyped-def]
    return await harvest_source(
        kwargs.pop("source", None) or source(),  # type: ignore[arg-type]
        kwargs.pop("settings", None) or settings(),  # type: ignore[arg-type]
        session_factory=factory,
        sleep=Sleeper(),
        **kwargs,  # type: ignore[arg-type]
    )


@respx.mock
async def test_two_pages_are_harvested_and_run_is_recorded(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    respx.get(OAI_URL).mock(side_effect=oai_server)
    summary = await run(factory)
    # 4 registros lidos; o de id 4 não tem título e é ignorado -> parcial
    assert (summary.records_read, summary.records_upserted, summary.records_ignored) == (4, 3, 1)
    assert summary.status == "partial"
    assert await count_records(factory) == 3

    async with factory() as session:
        run_row = (
            await session.execute(select(HarvestRun).where(HarvestRun.source == SLUG))
        ).scalar_one()
        assert run_row.status == "partial" and run_row.finished_at is not None
        assert (run_row.records_read, run_row.records_upserted) == (4, 3)
        first = (
            await session.execute(
                select(OaiRecord).where(OaiRecord.oai_identifier == "oai:exemplo:1")
            )
        ).scalar_one()
    assert first.title == "Educação digital no ensino médio"
    assert first.type == "thesis" and first.year == 2020 and first.doi == "10.1234/abc.2020"
    assert first.url == "http://repo.exemplo.org/handle/1/1"
    assert first.pdf_url == "http://repo.exemplo.org/bitstream/handle/1/1/arquivo.pdf"
    assert first.keywords == ["Educação", "Tecnologia"]
    assert first.authors[0] == {"name": "João P. Silva", "orcid": None}


@respx.mock
async def test_running_twice_does_not_duplicate(factory: async_sessionmaker[AsyncSession]) -> None:
    respx.get(OAI_URL).mock(side_effect=oai_server)
    await run(factory, full=True)
    await run(factory, full=True)
    assert await count_records(factory) == 3
    async with factory() as session:
        runs = (
            await session.execute(
                select(func.count()).select_from(HarvestRun).where(HarvestRun.source == SLUG)
            )
        ).scalar_one()
    assert runs == 2


@respx.mock
async def test_deleted_header_marks_record_deleted(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    respx.get(OAI_URL).mock(side_effect=oai_server)
    await run(factory)
    assert await count_records(factory, deleted=False) == 3
    respx.get(OAI_URL).mock(return_value=xml_response("deleted_record.xml"))
    summary = await run(factory, full=True)
    assert summary.records_deleted == 1
    assert await count_records(factory, deleted=True) == 1
    assert await count_records(factory, deleted=False) == 2


@respx.mock
async def test_harvest_again_undeletes_when_record_returns(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    respx.get(OAI_URL).mock(return_value=xml_response("list_records_page1.xml"))
    respx.get(OAI_URL, params={"resumptionToken": "tok-2"}).mock(
        return_value=xml_response("list_records_page2.xml")
    )
    respx.get(OAI_URL).mock(side_effect=oai_server)
    await run(factory)
    respx.get(OAI_URL).mock(return_value=xml_response("deleted_record.xml"))
    await run(factory, full=True)
    respx.get(OAI_URL).mock(side_effect=oai_server)
    await run(factory, full=True)
    assert await count_records(factory, deleted=True) == 0


@respx.mock
async def test_incremental_uses_date_of_last_ok_run(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    route = respx.get(OAI_URL).mock(return_value=xml_response("deleted_record.xml"))
    clean_source = source()
    # primeira vez: sem colheita anterior, sem "from"
    await run(factory, source=clean_source)
    assert "from" not in route.calls[0].request.url.params
    async with factory() as session:
        await session.execute(
            text("UPDATE harvest_runs SET status = 'ok' WHERE source = :s"), {"s": SLUG}
        )
        await session.commit()
    await run(factory, source=clean_source)
    assert "from" in route.calls[1].request.url.params
    await run(factory, source=clean_source, full=True)
    assert "from" not in route.calls[2].request.url.params


@respx.mock
async def test_limit_stops_early_and_marks_partial(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    respx.get(OAI_URL).mock(side_effect=oai_server)
    summary = await run(factory, limit=2)
    assert summary.records_read == 2 and summary.status == "partial"
    assert await count_records(factory) == 2


@respx.mock
async def test_dry_run_writes_nothing_and_returns_samples(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    respx.get(OAI_URL).mock(side_effect=oai_server)
    summary = await run(factory, dry_run=True, source=source(enabled=False))
    assert summary.dry_run and summary.records_upserted == 3
    assert 0 < len(summary.samples) <= 3
    assert await count_records(factory) == 0
    async with factory() as session:
        runs = (
            await session.execute(
                select(func.count()).select_from(HarvestRun).where(HarvestRun.source == SLUG)
            )
        ).scalar_one()
    assert runs == 0


@respx.mock
async def test_batches_commit_progress(factory: async_sessionmaker[AsyncSession]) -> None:
    respx.get(OAI_URL).mock(side_effect=oai_server)
    summary = await run(factory, batch_size=1)
    assert summary.records_upserted == 3 and await count_records(factory) == 3


async def test_contact_email_is_required(factory: async_sessionmaker[AsyncSession]) -> None:
    with pytest.raises(HarvestError, match="CONTACT_EMAIL"):
        await run(factory, settings=settings(contact_email=""))


async def test_disabled_source_refuses_real_run(factory: async_sessionmaker[AsyncSession]) -> None:
    with pytest.raises(HarvestError, match="enabled: false"):
        await run(factory, source=source(enabled=False))


async def test_source_without_url_is_refused(factory: async_sessionmaker[AsyncSession]) -> None:
    with pytest.raises(HarvestError, match="base_url"):
        await run(factory, source=source(enabled=False, base_url="TODO-VERIFICAR"), dry_run=True)


@respx.mock
async def test_protocol_error_marks_run_as_error(factory: async_sessionmaker[AsyncSession]) -> None:
    respx.get(OAI_URL).mock(return_value=xml_response("bad_resumption_token.xml"))
    with pytest.raises(HarvestError, match="badResumptionToken"):
        await run(factory)
    async with factory() as session:
        run_row = (
            await session.execute(select(HarvestRun).where(HarvestRun.source == SLUG))
        ).scalar_one()
    assert run_row.status == "error" and "badResumptionToken" in (run_row.error_message or "")


@respx.mock
async def test_xxe_response_marks_run_as_error(factory: async_sessionmaker[AsyncSession]) -> None:
    respx.get(OAI_URL).mock(return_value=xml_response("malicious_dtd.xml"))
    with pytest.raises(HarvestError, match="recusado"):
        await run(factory)
    assert await count_records(factory) == 0


@respx.mock
async def test_user_agent_identifies_contact(factory: async_sessionmaker[AsyncSession]) -> None:
    route = respx.get(OAI_URL).mock(return_value=xml_response("no_records_match.xml"))
    await run(factory)
    assert "dev@exemplo.com" in route.calls[0].request.headers["User-Agent"]


@respx.mock
async def test_search_vector_is_filled_for_harvested_rows(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    respx.get(OAI_URL).mock(side_effect=oai_server)
    await run(factory)
    async with factory() as session:
        found = (
            await session.execute(
                text(
                    "SELECT count(*) FROM oai_records WHERE source = :s "
                    "AND search_vector @@ websearch_to_tsquery('pt_unaccent', 'educacao')"
                ),
                {"s": SLUG},
            )
        ).scalar_one()
    assert found == 1


def test_httpx_client_type() -> None:
    assert httpx.AsyncClient is not None
