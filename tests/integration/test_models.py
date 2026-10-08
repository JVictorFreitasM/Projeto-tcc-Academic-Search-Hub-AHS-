import pytest
from alembic import command
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Favorite, OaiRecord, SearchHistory, SecurityEvent, User
from tests.factories import (
    make_favorite,
    make_harvest_run,
    make_history,
    make_oai_record,
    make_security_event,
    make_user,
)
from tests.integration.conftest import alembic_config

pytestmark = pytest.mark.integration

DOMAIN_TABLES = {
    "users",
    "favorites",
    "search_history",
    "security_events",
    "oai_records",
    "harvest_runs",
}


async def count(session: AsyncSession, model: type) -> int:
    return (await session.execute(select(func.count()).select_from(model))).scalar_one()


async def test_all_six_tables_exist(session: AsyncSession) -> None:
    rows = await session.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    )
    assert {row[0] for row in rows} >= DOMAIN_TABLES


def test_downgrade_to_0001_removes_the_six_tables(migrated_db_url: str) -> None:
    import psycopg

    config = alembic_config(migrated_db_url)
    sync_url = migrated_db_url.replace("postgresql+psycopg", "postgresql")
    command.downgrade(config, "0001")
    try:
        with psycopg.connect(sync_url) as conn:
            rows = conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            ).fetchall()
            assert DOMAIN_TABLES.isdisjoint({row[0] for row in rows})
    finally:
        command.upgrade(config, "head")


def test_models_match_migrations(migrated_db_url: str) -> None:
    """`alembic check` falha se os modelos tiverem mudanças sem migração."""
    command.check(alembic_config(migrated_db_url))


async def test_duplicate_favorite_fails(session: AsyncSession) -> None:
    user = make_user()
    session.add(user)
    await session.flush()
    session.add(make_favorite(user.id, record_id="doi:10.1/x"))
    await session.flush()
    session.add(make_favorite(user.id, record_id="doi:10.1/x"))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_same_record_for_two_users_is_allowed(session: AsyncSession) -> None:
    first, second = make_user(), make_user()
    session.add_all([first, second])
    await session.flush()
    session.add_all(
        [
            make_favorite(first.id, record_id="doi:10.1/x"),
            make_favorite(second.id, record_id="doi:10.1/x"),
        ]
    )
    await session.flush()


async def test_deleting_user_cascades_but_keeps_security_events(session: AsyncSession) -> None:
    user = make_user()
    session.add(user)
    await session.flush()
    session.add_all(
        [
            make_favorite(user.id),
            make_favorite(user.id),
            make_history(user.id),
            make_security_event(user_id=user.id, event_type="account_deleted"),
        ]
    )
    await session.flush()
    before = (
        await count(session, Favorite),
        await count(session, SearchHistory),
        await count(session, SecurityEvent),
    )
    assert before[0] >= 2 and before[1] >= 1 and before[2] >= 1

    await session.execute(delete(User).where(User.id == user.id))

    assert await count(session, Favorite) == before[0] - 2
    assert await count(session, SearchHistory) == before[1] - 1
    assert await count(session, SecurityEvent) == before[2]


async def test_uppercase_email_is_rejected_by_database(session: AsyncSession) -> None:
    session.add(make_user(email="Maiuscula@Exemplo.com"))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_duplicate_email_is_rejected(session: AsyncSession) -> None:
    session.add(make_user(email="repetido@exemplo.com"))
    await session.flush()
    session.add(make_user(email="repetido@exemplo.com"))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_user_requires_consent(session: AsyncSession) -> None:
    session.add(make_user(consent_at=None))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_note_over_1000_characters_is_rejected(session: AsyncSession) -> None:
    user = make_user()
    session.add(user)
    await session.flush()
    session.add(make_favorite(user.id, note="a" * 1001))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_note_with_1000_characters_is_accepted(session: AsyncSession) -> None:
    user = make_user()
    session.add(user)
    await session.flush()
    session.add(make_favorite(user.id, note="a" * 1000))
    await session.flush()


async def test_unknown_event_type_is_rejected(session: AsyncSession) -> None:
    session.add(make_security_event(event_type="algo_estranho"))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_security_event_survives_without_user_row(session: AsyncSession) -> None:
    session.add(make_security_event(user_id=None))
    await session.flush()


async def test_query_over_200_characters_is_rejected(session: AsyncSession) -> None:
    user = make_user()
    session.add(user)
    await session.flush()
    session.add(make_history(user.id, query="q" * 201))
    with pytest.raises(Exception, match=r"(?i)value too long|DataError|too long"):
        await session.flush()


async def test_oai_record_unique_per_source_and_identifier(session: AsyncSession) -> None:
    session.add(make_oai_record(source="bdtd", oai_identifier="oai:x:1"))
    await session.flush()
    session.add(make_oai_record(source="bdtd", oai_identifier="oai:x:1"))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_same_identifier_in_two_sources_is_allowed(session: AsyncSession) -> None:
    session.add(make_oai_record(source="bdtd", oai_identifier="oai:x:2"))
    session.add(make_oai_record(source="uespi", oai_identifier="oai:x:2"))
    await session.flush()


async def test_oai_record_type_is_restricted(session: AsyncSession) -> None:
    session.add(make_oai_record(type="monografia"))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_harvest_run_status_is_restricted(session: AsyncSession) -> None:
    session.add(make_harvest_run(status="quebrado"))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_harvest_run_defaults(session: AsyncSession) -> None:
    run = make_harvest_run()
    session.add(run)
    await session.flush()
    await session.refresh(run)
    assert run.records_read == 0
    assert run.finished_at is None


async def search_ids(session: AsyncSession, query: str) -> set[str]:
    rows = await session.execute(
        text(
            "SELECT oai_identifier FROM oai_records "
            "WHERE search_vector @@ to_tsquery('pt_unaccent', :q)"
        ),
        {"q": query},
    )
    return {row[0] for row in rows}


async def test_search_vector_finds_title_without_accent(session: AsyncSession) -> None:
    session.add(make_oai_record(oai_identifier="oai:sv:1", title="Educação"))
    session.add(make_oai_record(oai_identifier="oai:sv:2", title="Matemática"))
    await session.flush()
    found = await search_ids(session, "educacao")
    assert "oai:sv:1" in found
    assert "oai:sv:2" not in found


async def test_search_vector_includes_abstract_and_keywords(session: AsyncSession) -> None:
    session.add(
        make_oai_record(
            oai_identifier="oai:sv:3",
            title="Sem relação",
            abstract="Estudo sobre hidrografia regional",
            keywords=["Letramento digital", "Ribeirão"],
        )
    )
    await session.flush()
    assert "oai:sv:3" in await search_ids(session, "hidrografia")
    assert "oai:sv:3" in await search_ids(session, "letramento")
    assert "oai:sv:3" in await search_ids(session, "ribeirao")


async def test_search_vector_weights_title_a_keywords_b_abstract_c(session: AsyncSession) -> None:
    session.add(
        make_oai_record(
            oai_identifier="oai:sv:4",
            title="Alfa",
            abstract="Gama",
            keywords=["Beta"],
        )
    )
    await session.flush()
    row = await session.execute(
        text("SELECT search_vector::text FROM oai_records WHERE oai_identifier = 'oai:sv:4'")
    )
    vector = row.scalar_one()
    # O stemmer reduz as palavras ('beta' -> 'bet', 'gama' -> 'gam'); o que importa é o peso.
    assert "'alfa':1A" in vector
    assert "'bet':2B" in vector
    assert "'gam':3C" in vector


async def test_search_vector_is_recomputed_on_update(session: AsyncSession) -> None:
    record = make_oai_record(oai_identifier="oai:sv:5", title="Antigo título")
    session.add(record)
    await session.flush()
    assert "oai:sv:5" in await search_ids(session, "antigo")
    record.title = "Novo assunto"
    await session.flush()
    assert "oai:sv:5" not in await search_ids(session, "antigo")
    assert "oai:sv:5" in await search_ids(session, "assunto")


async def test_gin_index_is_usable_for_search(session: AsyncSession) -> None:
    """Com volume e ANALYZE, o plano usa o índice GIN (seqscan desligado só para o teste)."""
    await session.execute(
        text(
            "INSERT INTO oai_records (source, oai_identifier, title, type) "
            "SELECT 'volume', 'oai:vol:' || g, "
            "'Título número ' || g || ' sobre assunto' || (g % 50), 'other' "
            "FROM generate_series(1, 3000) g"
        )
    )
    await session.execute(text("ANALYZE oai_records"))
    await session.execute(text("SET LOCAL enable_seqscan = off"))
    plan = await session.execute(
        text(
            "EXPLAIN SELECT id FROM oai_records "
            "WHERE search_vector @@ websearch_to_tsquery('pt_unaccent', 'assunto7')"
        )
    )
    text_plan = "\n".join(row[0] for row in plan)
    assert "ix_oai_records_search_vector" in text_plan


async def test_oai_record_model_count(session: AsyncSession) -> None:
    session.add(make_oai_record())
    await session.flush()
    assert await count(session, OaiRecord) >= 1
