import pytest

from app.schemas.common import RecordType
from app.services.type_mapping import map_core_type, map_oai_type, map_openalex_type

pytestmark = pytest.mark.unit

A, T, P, B, OTH = (
    RecordType.ARTICLE,
    RecordType.THESIS,
    RecordType.PREPRINT,
    RecordType.BOOK,
    RecordType.OTHER,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("article", A),
        ("dissertation", T),
        ("preprint", P),
        ("book", B),
        ("book-chapter", B),
        ("dataset", OTH),
        ("ARTICLE", A),
        (None, OTH),
    ],
)
def test_openalex(raw: str | None, expected: RecordType) -> None:
    assert map_openalex_type(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("thesis", T),
        ("research article", A),  # valor real do CORE (15/10/2026)
        ("journal article", A),
        ("research", A),
        ("journal", A),
        ("article", A),
        ("book", B),
        ("presentation", OTH),
        ("report", OTH),
        ("slides", OTH),
        ("", OTH),
        (None, OTH),
    ],
)
def test_core(raw: str | None, expected: RecordType) -> None:
    assert map_core_type(raw) == expected


@pytest.mark.parametrize(
    ("raw_types", "default", "expected"),
    [
        (["Dissertação"], OTH, T),
        (["info:eu-repo/semantics/doctoralThesis"], OTH, T),
        (["info:eu-repo/semantics/masterThesis"], OTH, T),
        (["info:eu-repo/semantics/bachelorThesis"], T, OTH),
        (["info:eu-repo/semantics/article"], OTH, A),
        (["info:eu-repo/semantics/book"], OTH, B),
        (["info:eu-repo/semantics/bookPart"], OTH, B),
        (["info:eu-repo/semantics/preprint"], OTH, P),
        (["info:eu-repo/semantics/report"], A, OTH),
        (["info:eu-repo/semantics/conferenceObject"], A, OTH),
        (["Tese"], OTH, T),
        (["Artigo de Periódico"], OTH, A),
        (["Capítulo de livro"], OTH, B),
        (["Monografia"], T, OTH),
        (["TCC"], T, OTH),
        # específico vence "other"
        (["text", "info:eu-repo/semantics/bachelorThesis", "Dissertação"], A, T),
        # nenhum reconhecido -> default da fonte
        (["Texto", "Outro"], T, T),
        (["Texto"], A, A),
        # lista vazia ou valores em branco -> default
        ([], T, T),
        (["", "  "], A, A),
    ],
)
def test_map_oai_type(raw_types: list[str], default: RecordType, expected: RecordType) -> None:
    assert map_oai_type(raw_types, {}, default) == expected


def test_source_type_map_has_precedence_over_builtin() -> None:
    type_map = {"Trabalho Acadêmico": "thesis", "tese": "other"}
    assert map_oai_type(["trabalho academico"], type_map, "other") == T
    assert map_oai_type(["Tese"], type_map, "article") == OTH


def test_default_type_accepts_plain_string() -> None:
    assert map_oai_type([], {}, "thesis") == T
