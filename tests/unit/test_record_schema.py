import pytest
from pydantic import ValidationError

from app.schemas.record import RecordOut, SourceRef

pytestmark = pytest.mark.unit


def make(**overrides: object) -> RecordOut:
    data: dict[str, object] = {"id": "src:bdtd:1", "title": "Um título"}
    return RecordOut(**{**data, **overrides})  # type: ignore[arg-type]


def test_minimal_record_is_valid() -> None:
    record = make()
    assert record.type.value == "other"
    assert record.authors == [] and record.keywords == [] and record.sources == []
    assert record.is_favorite is False
    assert record.abstract is None and record.year is None and record.doi is None


@pytest.mark.parametrize("field", ["url", "pdf_url"])
@pytest.mark.parametrize(
    "bad", ["javascript:alert(1)", "data:text/html,x", "ftp://x.org/a", "exemplo.org", ""]
)
def test_rejects_non_http_urls(field: str, bad: str) -> None:
    with pytest.raises(ValidationError):
        make(**{field: bad})


def test_accepts_http_and_https_urls() -> None:
    record = make(url="https://exemplo.org/a", pdf_url="http://exemplo.org/a.pdf")
    assert record.url == "https://exemplo.org/a"


def test_source_ref_rejects_javascript_url() -> None:
    with pytest.raises(ValidationError):
        SourceRef(source="core", source_id="1", url="javascript:alert(1)")


@pytest.mark.parametrize("year", [999, 2101, 0, -5])
def test_rejects_year_out_of_range(year: int) -> None:
    with pytest.raises(ValidationError):
        make(year=year)


@pytest.mark.parametrize("year", [1000, 2021, 2100, None])
def test_accepts_year_in_range(year: int | None) -> None:
    assert make(year=year).year == year


def test_title_is_required_and_normalized() -> None:
    with pytest.raises(ValidationError):
        make(title="   ")
    assert make(title="  Muitos   espaços \n aqui ").title == "Muitos espaços aqui"


@pytest.mark.parametrize("language", ["PT", "por", "p", "pt-BR"])
def test_rejects_bad_language(language: str) -> None:
    with pytest.raises(ValidationError):
        make(language=language)


def test_rejects_unknown_type() -> None:
    with pytest.raises(ValidationError):
        make(type="monografia")


def test_json_schema_has_example() -> None:
    assert RecordOut.model_json_schema()["examples"][0]["id"] == "doi:10.1000/exemplo"
