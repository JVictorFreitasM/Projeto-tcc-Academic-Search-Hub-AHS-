from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.connectors.base import SourceQuery, SourceStatus
from app.connectors.oai_local import NOT_HARVESTED, STOPWORDS_ONLY, OaiLocalConnector
from app.connectors.registry import build_connectors
from app.core.config import Settings
from app.models import OaiRecord, User
from app.schemas.common import RecordType
from tests.factories import make_oai_record

pytestmark = pytest.mark.integration

SOURCES = ("bdtd", "uespi", "vazia")


@pytest.fixture
async def factory(engine: AsyncEngine) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """O conector abre as próprias sessões; por isso os dados são confirmados e limpos no fim."""
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def clean() -> None:
        async with maker() as session:
            await session.execute(delete(OaiRecord).where(OaiRecord.source.in_(SOURCES)))
            await session.commit()

    await clean()
    yield maker
    await clean()


async def seed(factory: async_sessionmaker[AsyncSession], *records: OaiRecord) -> None:
    async with factory() as session:
        session.add_all(records)
        await session.commit()


def conn(factory: async_sessionmaker[AsyncSession], slug: str = "bdtd", enabled: bool = True):  # type: ignore[no-untyped-def]
    return OaiLocalConnector(slug, slug.upper(), factory, enabled=enabled)


def titles(page) -> list[str]:  # type: ignore[no-untyped-def]
    return [r.title for r in page.records]


async def test_accent_and_no_accent_give_same_result(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    await seed(
        factory,
        make_oai_record(title="Educação inclusiva", oai_identifier="o:1"),
        make_oai_record(title="Física quântica", oai_identifier="o:2"),
    )
    with_accent = await conn(factory).search(SourceQuery(q="educação"))
    without = await conn(factory).search(SourceQuery(q="educacao"))
    assert titles(with_accent) == titles(without) == ["Educação inclusiva"]
    assert with_accent.total == 1 and with_accent.status is SourceStatus.OK


async def test_two_sources_do_not_mix(factory: async_sessionmaker[AsyncSession]) -> None:
    await seed(
        factory,
        make_oai_record(source="bdtd", title="Educação em rede", oai_identifier="o:1"),
        make_oai_record(source="uespi", title="Educação popular", oai_identifier="o:1"),
    )
    bdtd = await conn(factory, "bdtd").search(SourceQuery(q="educacao"))
    uespi = await conn(factory, "uespi").search(SourceQuery(q="educacao"))
    assert titles(bdtd) == ["Educação em rede"] and bdtd.total == 1
    assert titles(uespi) == ["Educação popular"] and uespi.total == 1
    assert bdtd.records[0].sources[0].source == "bdtd"
    assert uespi.records[0].sources[0].source == "uespi"


async def test_year_and_type_filters(factory: async_sessionmaker[AsyncSession]) -> None:
    await seed(
        factory,
        make_oai_record(title="Ensino 2015", year=2015, type="thesis", oai_identifier="o:1"),
        make_oai_record(title="Ensino 2020", year=2020, type="article", oai_identifier="o:2"),
        make_oai_record(title="Ensino 2022", year=2022, type="thesis", oai_identifier="o:3"),
        make_oai_record(title="Ensino sem ano", year=None, type="thesis", oai_identifier="o:4"),
    )
    c = conn(factory)
    both = await c.search(SourceQuery(q="ensino", year_from=2018, year_to=2021))
    assert titles(both) == ["Ensino 2020"]
    from_only = await c.search(SourceQuery(q="ensino", year_from=2020))
    assert sorted(titles(from_only)) == ["Ensino 2020", "Ensino 2022"]
    to_only = await c.search(SourceQuery(q="ensino", year_to=2015))
    assert titles(to_only) == ["Ensino 2015"]  # registro sem ano fica de fora
    thesis = await c.search(SourceQuery(q="ensino", types=(RecordType.THESIS,)))
    assert sorted(titles(thesis)) == ["Ensino 2015", "Ensino 2022", "Ensino sem ano"]
    assert thesis.total == 3
    none = await c.search(SourceQuery(q="ensino", types=(RecordType.BOOK,)))
    assert none.records == [] and none.total == 0
    unfiltered = await c.search(SourceQuery(q="ensino"))
    assert unfiltered.total == 4  # sem filtro de ano, o registro sem ano aparece


async def test_deleted_records_never_appear(factory: async_sessionmaker[AsyncSession]) -> None:
    await seed(
        factory,
        make_oai_record(title="Removido da fonte", deleted=True, oai_identifier="o:1"),
        make_oai_record(title="Ativo na fonte", oai_identifier="o:2"),
    )
    page = await conn(factory).search(SourceQuery(q="fonte"))
    assert titles(page) == ["Ativo na fonte"] and page.total == 1


async def test_year_desc_puts_nulls_last_and_relevance_orders_title_first(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    await seed(
        factory,
        make_oai_record(title="Robótica 2010", year=2010, oai_identifier="o:1"),
        make_oai_record(title="Robótica sem ano", year=None, oai_identifier="o:2"),
        make_oai_record(title="Robótica 2023", year=2023, oai_identifier="o:3"),
        make_oai_record(
            title="Outro assunto", abstract="robótica no resumo", year=2030, oai_identifier="o:4"
        ),
    )
    c = conn(factory)
    by_year = await c.search(SourceQuery(q="robótica", sort="year_desc"))
    assert titles(by_year) == [
        "Outro assunto",
        "Robótica 2023",
        "Robótica 2010",
        "Robótica sem ano",
    ]
    by_relevance = await c.search(SourceQuery(q="robótica"))
    # título (peso A) vence resumo (peso C), mesmo com ano mais recente
    assert titles(by_relevance)[-1] == "Outro assunto"
    assert by_relevance.records[0].year == 2023  # empate de relevância: ano mais recente primeiro


async def test_pagination_and_total(factory: async_sessionmaker[AsyncSession]) -> None:
    await seed(
        factory,
        *[
            make_oai_record(title=f"Pesquisa {i}", year=2000 + i, oai_identifier=f"o:{i}")
            for i in range(7)
        ],
    )
    c = conn(factory)
    first = await c.search(SourceQuery(q="pesquisa", page=1, page_size=3, sort="year_desc"))
    third = await c.search(SourceQuery(q="pesquisa", page=3, page_size=3, sort="year_desc"))
    assert first.total == 7 and third.total == 7
    assert len(first.records) == 3 and len(third.records) == 1
    assert first.records[0].year == 2006 and third.records[0].year == 2000


@pytest.mark.parametrize(
    "malicious",
    ["'; DROP TABLE users;--", '" OR 1=1 --', "a' UNION SELECT password_hash FROM users --"],
)
async def test_malicious_text_causes_no_sql_error(
    factory: async_sessionmaker[AsyncSession], malicious: str
) -> None:
    await seed(factory, make_oai_record(title="Qualquer título", oai_identifier="o:1"))
    page = await conn(factory).search(SourceQuery(q=malicious))
    assert page.status is SourceStatus.OK
    async with factory() as session:
        assert (await session.get(User, __import__("uuid").uuid4())) is None  # tabela intacta


async def test_source_without_records_is_disabled_with_message(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    c = conn(factory, "vazia")
    assert c.is_enabled() is True
    assert await c.availability() == (False, NOT_HARVESTED)
    page = await c.search(SourceQuery(q="qualquer"))
    assert page.status is SourceStatus.DISABLED and page.message == NOT_HARVESTED


async def test_source_disabled_in_yaml(factory: async_sessionmaker[AsyncSession]) -> None:
    await seed(factory, make_oai_record(title="Existe", oai_identifier="o:1"))
    c = conn(factory, enabled=False)
    assert c.is_enabled() is False
    page = await c.search(SourceQuery(q="existe"))
    assert page.status is SourceStatus.DISABLED


async def test_source_with_only_deleted_records_counts_as_not_harvested(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    await seed(factory, make_oai_record(title="Apagado", deleted=True, oai_identifier="o:1"))
    assert await conn(factory).availability() == (False, NOT_HARVESTED)


async def test_available_source(factory: async_sessionmaker[AsyncSession]) -> None:
    await seed(factory, make_oai_record(title="Existe", oai_identifier="o:1"))
    assert await conn(factory).availability() == (True, None)


async def test_only_stopwords_gives_empty_page_with_explanation(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    await seed(factory, make_oai_record(title="Existe", oai_identifier="o:1"))
    page = await conn(factory).search(SourceQuery(q="de a o"))
    assert page.status is SourceStatus.OK and page.records == [] and page.message == STOPWORDS_ONLY


async def test_quoted_phrase_and_exclusion(factory: async_sessionmaker[AsyncSession]) -> None:
    await seed(
        factory,
        make_oai_record(title="Ensino médio integrado", oai_identifier="o:1"),
        make_oai_record(title="Ensino de nível médio e técnico", oai_identifier="o:2"),
        make_oai_record(title="Ensino fundamental", oai_identifier="o:3"),
    )
    c = conn(factory)
    phrase = await c.search(SourceQuery(q='"ensino médio"'))
    assert titles(phrase) == ["Ensino médio integrado"]
    excluded = await c.search(SourceQuery(q="ensino -fundamental"))
    assert sorted(titles(excluded)) == ["Ensino de nível médio e técnico", "Ensino médio integrado"]


async def test_conversion_to_record_out(factory: async_sessionmaker[AsyncSession]) -> None:
    await seed(
        factory,
        make_oai_record(
            title="Trabalho completo",
            oai_identifier="oai:x:99",
            authors=[{"name": "Maria Souza", "orcid": None}, {"nome": "inválido"}],
            abstract="Resumo",
            year=2021,
            doi="10.1234/ABC",
            url="http://repo.org/1",
            pdf_url="javascript:alert(1)",
            keywords=["a", "b"],
            language="pt",
            type="article",
        ),
    )
    (record,) = (await conn(factory).search(SourceQuery(q="completo"))).records
    assert record.id == "doi:10.1234/abc"
    assert [a.name for a in record.authors] == ["Maria Souza"]
    assert record.pdf_url is None and record.url == "http://repo.org/1"
    assert record.type is RecordType.ARTICLE and record.keywords == ["a", "b"]
    assert record.sources[0].model_dump() == {
        "source": "bdtd",
        "source_id": "oai:x:99",
        "url": "http://repo.org/1",
    }


async def test_record_without_doi_uses_source_id(factory: async_sessionmaker[AsyncSession]) -> None:
    await seed(factory, make_oai_record(title="Sem doi", oai_identifier="oai:x:5"))
    (record,) = (await conn(factory).search(SourceQuery(q="doi"))).records
    assert record.id == "src:bdtd:oai:x:5"


def test_registry_creates_one_connector_per_yaml_source(
    tmp_path: Path, factory: async_sessionmaker[AsyncSession]
) -> None:
    file = tmp_path / "fontes.yml"
    file.write_text(
        "sources:\n"
        "  - {slug: uespi, name: UESPI, base_url: 'https://a.org/oai', enabled: true}\n"
        "  - {slug: bdtd, name: BDTD, base_url: TODO-VERIFICAR, enabled: false}\n"
        "  - {slug: nova, name: Nova, base_url: TODO-VERIFICAR}\n",
        encoding="utf-8",
    )
    settings = Settings(_env_file=None, oai_sources_file=str(file))  # type: ignore[call-arg]
    connectors = build_connectors(settings, factory)
    assert [c.slug for c in connectors] == ["openalex", "core", "bdtd", "uespi", "nova"]
    flags = {c.slug: c.is_enabled() for c in connectors}
    assert flags == {
        "openalex": False,
        "core": False,
        "bdtd": False,
        "uespi": True,
        "nova": False,
    }


def test_registry_survives_invalid_yaml(
    tmp_path: Path, factory: async_sessionmaker[AsyncSession]
) -> None:
    file = tmp_path / "ruim.yml"
    file.write_text("sources: [", encoding="utf-8")
    settings = Settings(_env_file=None, oai_sources_file=str(file))  # type: ignore[call-arg]
    assert [c.slug for c in build_connectors(settings, factory)] == ["openalex", "core"]


# ---------- busca por autor (campo `author`) ----------


def authored(title: str, *names: str, **extra):  # type: ignore[no-untyped-def]
    return make_oai_record(
        title=title,
        authors=[{"name": name, "orcid": None} for name in names],
        **extra,
    )


async def test_author_search_finds_by_full_name_surname_and_in_any_order(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    await seed(
        factory,
        authored("Pedagogia do oprimido", "Freire, Paulo", oai_identifier="a:1"),
        authored("Outro assunto", "Maria Silva", oai_identifier="a:2"),
    )
    c = conn(factory)
    for typed in ("Paulo Freire", "Freire", "freire paulo", "Freire, Paulo", "PAULO"):
        page = await c.search(SourceQuery(q=typed, field="author"))
        assert titles(page) == ["Pedagogia do oprimido"], typed
        assert page.total == 1 and page.status is SourceStatus.OK
    nobody = await c.search(SourceQuery(q="Ninguém Conhecido", field="author"))
    assert nobody.records == [] and nobody.total == 0


async def test_author_search_ignores_accents_but_does_not_stem_names(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    await seed(
        factory,
        authored("Livro 1", "Maria José Conceição", oai_identifier="a:1"),
        authored("Livro 2", "Paula Souza", oai_identifier="a:2"),
        authored("Livro 3", "Paulo Souza", oai_identifier="a:3"),
    )
    c = conn(factory)
    accent = await c.search(SourceQuery(q="maria jose conceicao", field="author"))
    assert titles(accent) == ["Livro 1"]
    # "Paulo" não pode virar "Paula" (o tema usa radical; o autor, não)
    paulo = await c.search(SourceQuery(q="Paulo Souza", field="author"))
    assert titles(paulo) == ["Livro 3"]


async def test_author_search_looks_only_at_authors_and_theme_search_only_at_text(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    await seed(
        factory,
        authored("Paulo Freire e a educação popular", "Fulano de Tal", oai_identifier="a:1"),
        authored("Letramento", "Paulo Freire", keywords=["educação"], oai_identifier="a:2"),
    )
    c = conn(factory)
    by_author = await c.search(SourceQuery(q="Freire", field="author"))
    assert titles(by_author) == ["Letramento"]  # o nome no título não conta
    by_theme = await c.search(SourceQuery(q="Freire"))
    assert titles(by_theme) == ["Paulo Freire e a educação popular"]  # o autor não conta
    default = await c.search(SourceQuery(q="Freire", field="all"))
    assert titles(default) == titles(by_theme)


async def test_author_search_finds_any_of_several_authors_and_respects_filters_and_sort(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    await seed(
        factory,
        authored(
            "Artigo 2015",
            "Ana Lima",
            "Bruno Costa",
            year=2015,
            type="article",
            oai_identifier="a:1",
        ),
        authored("Tese 2020", "Bruno Costa", year=2020, type="thesis", oai_identifier="a:2"),
        authored(
            "Tese 2023", "Carla Dias", "Bruno Costa", year=2023, type="thesis", oai_identifier="a:3"
        ),
        authored("Sem ano", "Bruno Costa", year=None, type="thesis", oai_identifier="a:4"),
    )
    c = conn(factory)
    everything = await c.search(SourceQuery(q="Bruno Costa", field="author"))
    assert everything.total == 4  # o segundo autor da lista também vale
    ranged = await c.search(SourceQuery(q="Bruno Costa", field="author", year_from=2018))
    assert sorted(titles(ranged)) == ["Tese 2020", "Tese 2023"]
    thesis = await c.search(SourceQuery(q="Bruno", field="author", types=(RecordType.THESIS,)))
    assert thesis.total == 3
    newest = await c.search(SourceQuery(q="Bruno Costa", field="author", sort="year_desc"))
    assert titles(newest) == ["Tese 2023", "Tese 2020", "Artigo 2015", "Sem ano"]
    paged = await c.search(SourceQuery(q="Bruno Costa", field="author", page_size=2, page=2))
    assert len(paged.records) == 2 and paged.total == 4


async def test_author_search_follows_changes_to_the_authors_and_backfill_works(
    factory: async_sessionmaker[AsyncSession], engine: AsyncEngine
) -> None:
    await seed(factory, authored("Obra", "Nome Antigo", oai_identifier="a:1"))
    c = conn(factory)
    assert titles(await c.search(SourceQuery(q="Antigo", field="author"))) == ["Obra"]
    async with factory() as session:  # o gatilho refaz o vetor quando `authors` muda
        row = (
            await session.execute(select(OaiRecord).where(OaiRecord.source == "bdtd"))
        ).scalar_one()
        row.authors = [{"name": "Nome Novo", "orcid": None}]
        await session.commit()
    assert (await c.search(SourceQuery(q="Antigo", field="author"))).records == []
    assert titles(await c.search(SourceQuery(q="Novo", field="author"))) == ["Obra"]
    # preenchimento retroativo da migração: `UPDATE ... SET authors = authors` refaz o vetor
    async with engine.begin() as connection:  # confirma antes de consultar de outra sessão
        await connection.execute(
            text("UPDATE oai_records SET author_vector = NULL WHERE source = 'bdtd'")
        )
    assert (await c.search(SourceQuery(q="Novo", field="author"))).records == []
    async with engine.begin() as connection:
        await connection.execute(
            text("UPDATE oai_records SET authors = authors WHERE source = 'bdtd'")
        )
    assert titles(await c.search(SourceQuery(q="Novo", field="author"))) == ["Obra"]


async def test_author_search_with_malicious_text_causes_no_sql_error(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    await seed(factory, authored("Obra", "Alguém", oai_identifier="a:1"))
    page = await conn(factory).search(SourceQuery(q="'; DROP TABLE users;--", field="author"))
    assert page.status is SourceStatus.OK
    async with factory() as session:
        assert (await session.execute(select(func.count()).select_from(User))).scalar_one() >= 0


async def test_author_search_with_only_stop_punctuation_is_an_empty_ok_page(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    await seed(factory, authored("Obra", "Alguém", oai_identifier="a:1"))
    page = await conn(factory).search(SourceQuery(q="!!! ---", field="author"))
    assert page.status is SourceStatus.OK and page.records == []
    assert page.message == STOPWORDS_ONLY
