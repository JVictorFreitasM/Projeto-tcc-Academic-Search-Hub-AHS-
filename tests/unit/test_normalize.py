import pytest

from app.services.normalize import (
    build_record_id,
    clean_text,
    normalize_author,
    normalize_doi,
    normalize_language,
    normalize_title,
    parse_year,
    safe_url,
    surname,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("10.1000/ABC.123 ", "10.1000/abc.123"),
        ("https://doi.org/10.1000/XYZ", "10.1000/xyz"),
        ("http://dx.doi.org/10.1000/xyz", "10.1000/xyz"),
        ("doi:10.1000/xyz", "10.1000/xyz"),
        ("DOI: 10.1000/xyz", "10.1000/xyz"),
        ("  10.1000/xyz.  ", "10.1000/xyz"),
        ("11.1000/xyz", None),
        ("isbn:123", None),
        ("10.1000", None),
        ("10.1000/com espaco", None),
        ("", None),
        (None, None),
    ],
)
def test_normalize_doi(raw: str | None, expected: str | None) -> None:
    assert normalize_doi(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Um <i>título</i> com <b>tags</b>", "Um título com tags"),
        ("Ciência &amp; Tecnologia", "Ciência & Tecnologia"),
        ("linha 1\n\n   linha   2\t3", "linha 1 linha 2 3"),
        ("a &lt;script&gt;x&lt;/script&gt; b", "a x b"),
        ("5 < 7 e 9 > 3", "5 < 7 e 9 > 3"),
        ("<p>Parágrafo</p><br/>fim", "Parágrafo fim"),
        ("com\x00controle", "com controle"),
        ("", ""),
        (None, ""),
    ],
)
def test_clean_text(raw: str | None, expected: str) -> None:
    assert clean_text(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("A Educação, no Brasil!", "a educacao no brasil"),
        ("  <i>Título</i>   Duplo  ", "titulo duplo"),
        ("Ciência & Tecnologia", "ciencia tecnologia"),
        ("", ""),
        (None, ""),
    ],
)
def test_normalize_title(raw: str | None, expected: str) -> None:
    assert normalize_title(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2021", 2021),
        (2021, 2021),
        ("2021-05-03", 2021),
        ("2021-05", 2021),
        ("[2019]", 2019),
        ("publicado em 1998.", 1998),
        ("0999", None),
        ("2101", None),
        (999, None),
        (12345, None),
        ("12345", None),
        ("sem ano", None),
        ("", None),
        (None, None),
        (True, None),
    ],
)
def test_parse_year(raw: object, expected: int | None) -> None:
    assert parse_year(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("SILVA, João P.", "João P. Silva"),
        ("Souza, Maria", "Maria Souza"),
        ("Maria   Souza", "Maria Souza"),
        ("Silva, João, Jr.", "Silva, João, Jr."),
        ("Madonna", "Madonna"),
        ("  ", ""),
    ],
)
def test_normalize_author_name(raw: str, expected: str) -> None:
    if expected == "":
        with pytest.raises(ValueError, match="at least 1 character"):
            normalize_author(raw)
    else:
        assert normalize_author(raw).name == expected


def test_normalize_author_orcid() -> None:
    author = normalize_author("Maria Souza", "https://orcid.org/0000-0002-1825-0097")
    assert author.orcid == "0000-0002-1825-0097"
    assert normalize_author("Maria Souza", "").orcid is None
    assert normalize_author("Maria Souza").orcid is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Maria Souza", "souza"),
        ("SILVA, João P.", "silva"),
        ("Álvaro de Albuquerque", "albuquerque"),
        ("Madonna", "madonna"),
        ("", ""),
        (None, ""),
    ],
)
def test_surname(raw: str | None, expected: str) -> None:
    assert surname(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("por", "pt"),
        ("eng", "en"),
        ("spa", "es"),
        ("pt-BR", "pt"),
        ("pt_BR", "pt"),
        ("EN", "en"),
        ("xx", None),
        ("klingon", None),
        ("", None),
        (None, None),
    ],
)
def test_normalize_language(raw: str | None, expected: str | None) -> None:
    assert normalize_language(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://exemplo.org/a?b=1", "https://exemplo.org/a?b=1"),
        ("  http://exemplo.org  ", "http://exemplo.org"),
        ("javascript:alert(1)", None),
        ("JAVASCRIPT:alert(1)", None),
        ("data:text/html,<script>", None),
        ("ftp://exemplo.org/x", None),
        ("//exemplo.org/x", None),
        ("https://", None),
        ("https://exemplo.org/com espaço", None),
        ("", None),
        (None, None),
    ],
)
def test_safe_url(raw: str | None, expected: str | None) -> None:
    assert safe_url(raw) == expected


def test_build_record_id() -> None:
    assert build_record_id("10.1000/X", "bdtd", "abc") == "doi:10.1000/x"
    assert build_record_id("https://doi.org/10.1000/x", "core", "1") == "doi:10.1000/x"
    assert build_record_id(None, "bdtd", "abc") == "src:bdtd:abc"
    assert build_record_id("não é doi", "bdtd", "abc") == "src:bdtd:abc"


def test_safe_url_unescapes_html_ampersands_from_the_sources() -> None:
    """Visto no OpenAlex (15/10/2026): `...sci_arttext&amp;pid=...` quebra o parâmetro `pid`."""
    assert (
        safe_url("http://scielo.pt/scielo.php?script=sci_arttext&amp;pid=S1645-72502005000100014")
        == "http://scielo.pt/scielo.php?script=sci_arttext&pid=S1645-72502005000100014"
    )
    assert safe_url("https://x.org/a?b=1&c=2") == "https://x.org/a?b=1&c=2"  # já correto: igual
    assert safe_url("javascript:alert(1)&amp;x") is None  # continua recusando esquemas perigosos
