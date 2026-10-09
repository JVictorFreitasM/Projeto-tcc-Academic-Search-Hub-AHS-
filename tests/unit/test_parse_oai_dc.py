import pytest
from defusedxml.ElementTree import fromstring

from app.harvest.mapping import parse_datestamp, parse_oai_dc
from app.harvest.oai_client import OaiRecordRaw, parse_record_element
from app.harvest.oai_sources import OaiSourceConfig
from app.schemas.common import RecordType

pytestmark = pytest.mark.unit

NS = (
    'xmlns="http://www.openarchives.org/OAI/2.0/" '
    'xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/"'
)


def source(**overrides: object) -> OaiSourceConfig:
    data: dict[str, object] = {
        "slug": "bdtd",
        "name": "BDTD",
        "base_url": "https://oai.exemplo.org/oai",
        "default_type": RecordType.THESIS,
    }
    return OaiSourceConfig(**{**data, **overrides})  # type: ignore[arg-type]


def raw_from(
    dc_xml: str, identifier: str = "oai:x:1", datestamp: str = "2026-01-02"
) -> OaiRecordRaw:
    xml = (
        f"<record {NS}><header><identifier>{identifier}</identifier>"
        f"<datestamp>{datestamp}</datestamp></header>"
        f"<metadata><oai_dc:dc>{dc_xml}</oai_dc:dc></metadata></record>"
    )
    parsed = parse_record_element(fromstring(xml))
    assert parsed is not None
    return parsed


def parse(dc_xml: str, **overrides: object) -> dict:  # type: ignore[type-arg]
    row = parse_oai_dc(raw_from(dc_xml), source(**overrides))
    assert row is not None
    return row


def test_title_repeated_in_two_languages_uses_first() -> None:
    row = parse("<dc:title>Título em português</dc:title><dc:title>English title</dc:title>")
    assert row["title"] == "Título em português"


def test_longest_description_is_the_abstract_and_html_is_cleaned() -> None:
    row = parse(
        "<dc:title>T</dc:title><dc:description>Curto</dc:description>"
        "<dc:description>Um resumo &lt;b&gt;mais longo&lt;/b&gt; &amp; completo</dc:description>"
    )
    assert row["abstract"] == "Um resumo mais longo & completo"


def test_only_doi_gives_doi_url_and_no_pdf() -> None:
    row = parse("<dc:title>T</dc:title><dc:identifier>doi:10.1234/ABC</dc:identifier>")
    assert row["doi"] == "10.1234/abc"
    assert row["url"] == "https://doi.org/10.1234/abc"
    assert row["pdf_url"] is None


def test_doi_url_is_not_used_as_landing_page_when_other_link_exists() -> None:
    row = parse(
        "<dc:title>T</dc:title><dc:identifier>https://doi.org/10.1/x</dc:identifier>"
        "<dc:identifier>http://repo.org/handle/1/2</dc:identifier>"
    )
    assert row["url"] == "http://repo.org/handle/1/2"
    assert row["doi"] == "10.1/x" or row["doi"] is None  # 10.1/x tem registrante curto demais


def test_only_pdf_link() -> None:
    row = parse(
        "<dc:title>T</dc:title><dc:identifier>http://repo.org/files/a.PDF?x=1</dc:identifier>"
    )
    assert row["pdf_url"] == "http://repo.org/files/a.PDF?x=1"
    assert row["url"] is None


def test_bitstream_link_is_pdf() -> None:
    row = parse(
        "<dc:title>T</dc:title><dc:relation>http://repo.org/bitstream/handle/1/2/arquivo</dc:relation>"
    )
    assert row["pdf_url"] == "http://repo.org/bitstream/handle/1/2/arquivo"


def test_unsafe_links_are_dropped() -> None:
    row = parse(
        "<dc:title>T</dc:title><dc:identifier>javascript:alert(1)</dc:identifier>"
        "<dc:identifier>ftp://x.org/a</dc:identifier>"
    )
    assert row["url"] is None and row["pdf_url"] is None


def test_without_date_year_is_none_and_first_valid_date_wins() -> None:
    assert parse("<dc:title>T</dc:title>")["year"] is None
    row = parse(
        "<dc:title>T</dc:title><dc:date>sem data</dc:date><dc:date>2019-03</dc:date><dc:date>2021</dc:date>"
    )
    assert row["year"] == 2019


def test_missing_dc_type_uses_default_type() -> None:
    row = parse("<dc:title>T</dc:title>")
    assert row["type"] == "thesis" and row["raw_types"] == []
    row = parse("<dc:title>T</dc:title>", default_type=RecordType.ARTICLE)
    assert row["type"] == "article"


def test_type_mapping_and_raw_types() -> None:
    row = parse(
        "<dc:title>T</dc:title><dc:type>info:eu-repo/semantics/bachelorThesis</dc:type>"
        "<dc:type>Monografia</dc:type>",
        default_type=RecordType.THESIS,
    )
    assert row["type"] == "other"
    assert row["raw_types"] == ["info:eu-repo/semantics/bachelorThesis", "Monografia"]
    row = parse(
        "<dc:title>T</dc:title><dc:type>Trabalho Acadêmico</dc:type>",
        type_map={"trabalho academico": "thesis"},
        default_type=RecordType.OTHER,
    )
    assert row["type"] == "thesis"


def test_authors_keywords_language() -> None:
    row = parse(
        "<dc:title>T</dc:title><dc:creator>SILVA, João P.</dc:creator><dc:creator> </dc:creator>"
        "<dc:subject>Educação</dc:subject><dc:subject>educação</dc:subject><dc:subject>Física</dc:subject>"
        "<dc:language>por</dc:language>"
    )
    assert row["authors"] == [{"name": "João P. Silva", "orcid": None}]
    assert row["keywords"] == ["Educação", "Física"]
    assert row["language"] == "pt"


def test_record_without_title_is_ignored() -> None:
    assert parse_oai_dc(raw_from("<dc:creator>Alguém</dc:creator>"), source()) is None
    assert parse_oai_dc(OaiRecordRaw("oai:x:2", None, False, dc=None), source()) is None


def test_identifier_source_and_datestamp() -> None:
    row = parse("<dc:title>T</dc:title>")
    assert row["source"] == "bdtd" and row["oai_identifier"] == "oai:x:1"
    assert row["datestamp"].isoformat() == "2026-01-02T00:00:00+00:00"
    assert row["deleted"] is False


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-05-03", "2026-05-03T00:00:00+00:00"),
        ("2026-05-03T10:20:30Z", "2026-05-03T10:20:30+00:00"),
        ("lixo", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_datestamp(value: str | None, expected: str | None) -> None:
    result = parse_datestamp(value)
    assert (result.isoformat() if result else None) == expected


def test_deleted_header_has_no_dc() -> None:
    xml = (
        f'<record {NS}><header status="deleted"><identifier>oai:x:9</identifier></header></record>'
    )
    parsed = parse_record_element(fromstring(xml))
    assert parsed is not None and parsed.deleted and parsed.dc is None
