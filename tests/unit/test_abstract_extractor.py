from pathlib import Path

import pytest

from app.scraping.abstract_extractor import extract_abstract

pytestmark = pytest.mark.unit

HTML = Path(__file__).resolve().parents[1] / "fixtures" / "html"


def page(name: str) -> str:
    return (HTML / name).read_text(encoding="utf-8")


def test_citation_abstract_wins_and_is_cleaned() -> None:
    assert extract_abstract(page("citation_abstract.html")) == (
        "Este estudo analisa o uso de tecnologias & seus efeitos."
    )


def test_dc_description_takes_the_longest_value() -> None:
    result = extract_abstract(page("dc_description.html"))
    assert result == "A longer English abstract from Dublin Core."


def test_short_og_description_is_ignored() -> None:
    assert extract_abstract(page("og_short.html")) is None


def test_long_og_description_is_used_as_last_meta_resort() -> None:
    result = extract_abstract(page("og_long.html"))
    assert result is not None and result.startswith("Este resumo longo vem da descrição")


def test_json_ld_scholarly_article_inside_graph_and_invalid_json_skipped() -> None:
    assert extract_abstract(page("jsonld.html")) == ("Resumo vindo do JSON-LD do artigo acadêmico.")


def test_page_without_metadata_returns_none() -> None:
    assert extract_abstract(page("nothing.html")) is None


def test_json_ld_description_is_used_when_there_is_no_abstract_field() -> None:
    html = (
        '<script type="application/ld+json">'
        '{"@type": "ScholarlyArticle", "description": "Descrição do artigo."}</script>'
    )
    assert extract_abstract(html) == "Descrição do artigo."


def test_json_ld_of_other_types_is_ignored() -> None:
    html = '<script type="application/ld+json">{"@type": "WebPage", "description": "x"}</script>'
    assert extract_abstract(html) is None


def test_order_of_preference_dc_over_og_and_jsonld() -> None:
    html = (
        '<meta property="og:description" content="' + "o" * 250 + '">'
        '<meta name="dc.description" content="Resumo DC.">'
        '<script type="application/ld+json">{"@type":"ScholarlyArticle","abstract":"JSON"}</script>'
    )
    assert extract_abstract(html) == "Resumo DC."


def test_empty_and_garbage_html() -> None:
    assert extract_abstract("") is None
    assert extract_abstract("<<<não é html>>>") is None


def test_result_is_capped() -> None:
    html = '<meta name="citation_abstract" content="' + "a" * 20000 + '">'
    assert len(extract_abstract(html) or "") == 10_000
