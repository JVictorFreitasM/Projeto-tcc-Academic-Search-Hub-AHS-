import random
import time

import pytest

from app.schemas.common import RecordType
from app.schemas.record import AuthorOut, RecordOut, SourceRef
from app.services.dedup import deduplicate, merge, title_key
from app.services.normalize import build_record_id

pytestmark = pytest.mark.unit

LONG_TITLE = "Letramento digital na educação básica brasileira"


def rec(
    source: str,
    source_id: str,
    title: str = LONG_TITLE,
    *,
    doi: str | None = None,
    year: int | None = 2021,
    authors: list[str] | None = None,
    **extra: object,
) -> RecordOut:
    names = ["Maria Souza"] if authors is None else authors
    return RecordOut(
        id=build_record_id(doi, source, source_id),
        title=title,
        authors=[AuthorOut(name=n) for n in names],
        year=year,
        doi=doi,
        sources=[SourceRef(source=source, source_id=source_id)],
        **extra,  # type: ignore[arg-type]
    )


def test_same_doi_in_openalex_and_core_with_different_case() -> None:
    a = rec("openalex", "W1", doi="10.1234/ABC")
    b = rec(
        "core", "9", title="Outro título qualquer", doi="https://doi.org/10.1234/abc", year=None
    )
    result = deduplicate([a, b])
    assert len(result) == 1
    assert result[0].id == "doi:10.1234/abc"
    assert [s.source for s in result[0].sources] == ["openalex", "core"]


def test_same_title_without_doi_in_core_and_uespi() -> None:
    a = rec("core", "1")
    b = rec("uespi", "oai:u:7", title="LETRAMENTO DIGITAL, na Educação Básica Brasileira!")
    (merged,) = deduplicate([a, b])
    assert {s.source for s in merged.sources} == {"core", "uespi"}
    assert merged.id == "src:core:1"


def test_short_titles_without_doi_are_not_merged() -> None:
    a = rec("core", "1", title="Introdução")
    b = rec("bdtd", "2", title="Introdução")
    assert title_key(a) is None
    assert len(deduplicate([a, b])) == 2


def test_same_title_different_years_are_not_merged() -> None:
    assert len(deduplicate([rec("core", "1", year=2019), rec("bdtd", "2", year=2020)])) == 2


def test_missing_year_or_author_never_merges_by_title() -> None:
    assert len(deduplicate([rec("core", "1", year=None), rec("bdtd", "2", year=None)])) == 2
    assert len(deduplicate([rec("core", "1", authors=[]), rec("bdtd", "2", authors=[])])) == 2


def test_different_first_author_is_not_merged() -> None:
    a = rec("core", "1", authors=["Maria Souza"])
    b = rec("bdtd", "2", authors=["Pedro Lima"])
    assert len(deduplicate([a, b])) == 2


def test_different_dois_with_same_title_are_not_merged() -> None:
    a = rec("openalex", "W1", doi="10.1/aaa")
    b = rec("core", "2", doi="10.1/bbb")
    assert len(deduplicate([a, b])) == 2


def test_three_sources_for_the_same_work() -> None:
    a = rec("openalex", "W1", doi="10.5/x")
    b = rec("core", "2", doi="10.5/X")
    c = rec("scielo", "oai:s:3", doi="doi:10.5/x")
    (merged,) = deduplicate([a, b, c])
    assert [s.source for s in merged.sources] == ["openalex", "core", "scielo"]


def test_record_without_doi_inherits_doi_from_duplicate_found_by_title() -> None:
    first = rec("uespi", "oai:u:1")  # sem DOI
    second = rec("openalex", "W2", doi="10.7/novo")
    (merged,) = deduplicate([first, second])
    assert merged.doi == "10.7/novo"
    assert merged.id == "doi:10.7/novo"  # id recalculado
    # e um terceiro, só com o DOI, também se junta ao grupo
    third = rec("core", "3", title="Totalmente diferente do resto", doi="10.7/NOVO", year=1999)
    assert len(deduplicate([first, second, third])) == 1


def test_merge_rules() -> None:
    base = rec(
        "core",
        "1",
        abstract="curto",
        url=None,
        pdf_url=None,
        type=RecordType.OTHER,
        keywords=["Educação", "TIC"],
        language=None,
    )
    other = rec(
        "bdtd",
        "2",
        abstract="um resumo bem mais longo",
        url="https://b.org/2",
        pdf_url="https://b.org/2.pdf",
        type=RecordType.THESIS,
        keywords=["educação", "Escola"],
        language="pt",
        authors=["Maria Souza", "João Lima"],
    )
    merged = merge(base, other)
    assert merged.abstract == "um resumo bem mais longo"
    assert (merged.url, merged.pdf_url, merged.language) == (
        "https://b.org/2",
        "https://b.org/2.pdf",
        "pt",
    )
    assert merged.type is RecordType.THESIS  # base era "other", o outro é específico
    assert merged.keywords == ["Educação", "TIC", "Escola"]  # união sem repetir
    assert [a.name for a in merged.authors] == ["Maria Souza", "João Lima"]  # lista mais completa


def test_type_of_first_is_kept_unless_it_is_other() -> None:
    first = rec("core", "1", type=RecordType.ARTICLE)
    second = rec("bdtd", "2", type=RecordType.THESIS)
    assert merge(first, second).type is RecordType.ARTICLE


def test_authors_tie_prefers_the_one_with_orcid() -> None:
    base = rec("core", "1")
    other = rec("bdtd", "2")
    other.authors = [AuthorOut(name="Maria Souza", orcid="0000-0002-1825-0097")]
    assert merge(base, other).authors[0].orcid == "0000-0002-1825-0097"


def test_sources_are_not_repeated() -> None:
    a = rec("core", "1")
    (merged,) = deduplicate([a, a.model_copy(deep=True)])
    assert len(merged.sources) == 1


def test_order_of_first_occurrence_is_kept() -> None:
    items = [
        rec("core", "1", title="Primeiro trabalho distinto sobre física", authors=["A Alfa"]),
        rec("core", "2", title="Segundo trabalho distinto sobre química", authors=["B Beta"]),
        rec("bdtd", "3", title="Primeiro trabalho distinto sobre física", authors=["A Alfa"]),
        rec("core", "4", title="Terceiro trabalho distinto sobre biologia", authors=["C Gama"]),
    ]
    assert [r.title.split()[0] for r in deduplicate(items)] == ["Primeiro", "Segundo", "Terceiro"]


def test_inputs_are_not_mutated() -> None:
    a, b = rec("core", "1"), rec("bdtd", "2")
    deduplicate([a, b])
    assert len(a.sources) == 1 and a.id == "src:core:1"


def test_empty_and_single() -> None:
    assert deduplicate([]) == []
    single = rec("core", "1")
    assert deduplicate([single]) == [single]


def _random_records(seed: int, count: int) -> list[RecordOut]:
    rng = random.Random(seed)  # noqa: S311 (dados de teste, não é criptografia)
    out: list[RecordOut] = []
    for i in range(count):
        work = rng.randrange(count // 3 + 1)
        use_doi = rng.random() < 0.5
        out.append(
            rec(
                rng.choice(["openalex", "core", "bdtd", "uespi"]),
                f"id{i}",
                title=f"Trabalho sintético número {work} sobre assunto diverso",
                doi=f"10.1/work{work}" if use_doi else None,
                year=2000 + work % 20,
                authors=[f"Autor{work} Sobrenome{work}"],
                abstract=("x" * rng.randrange(5)) or None,
            )
        )
    return out


@pytest.mark.parametrize("seed", range(10))
def test_idempotent(seed: int) -> None:
    once = deduplicate(_random_records(seed, 300))
    twice = deduplicate(once)
    assert [r.model_dump() for r in twice] == [r.model_dump() for r in once]


def test_5000_records_finish_quickly() -> None:
    records = _random_records(42, 5000)
    started = time.perf_counter()
    result = deduplicate(records)
    elapsed = time.perf_counter() - started
    assert 0 < len(result) < len(records)
    assert elapsed < 30  # só garante que não é quadrático; não é uma promessa de desempenho
