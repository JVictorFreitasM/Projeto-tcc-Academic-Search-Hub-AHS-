import csv
import io
import json
import re

import pytest

from app.schemas.common import RecordType
from app.schemas.record import AuthorOut, RecordOut, SourceRef
from app.services.export_service import (
    bibtex_escape,
    csv_safe,
    to_bibtex,
    to_csv,
    to_json,
    to_ris,
)

pytestmark = pytest.mark.unit


def rec(n: int = 1, **overrides: object) -> RecordOut:
    data: dict[str, object] = {
        "id": f"doi:10.1234/x{n}",
        "title": f"Letramento digital na educação {n}",
        "authors": [AuthorOut(name="Maria Souza"), AuthorOut(name="João Pedro de Albuquerque")],
        "abstract": "Resumo do trabalho.",
        "year": 2021,
        "doi": f"10.1234/x{n}",
        "url": "https://exemplo.org/1",
        "type": RecordType.ARTICLE,
        "language": "pt",
        "keywords": ["educação", "tecnologia"],
        "sources": [SourceRef(source="openalex", source_id=f"W{n}")],
    }
    return RecordOut(**{**data, **overrides})  # type: ignore[arg-type]


def parse_ris(text: str) -> list[dict[str, list[str]]]:
    """Leitor simples de RIS, só para a ida e volta do teste."""
    records: list[dict[str, list[str]]] = []
    current: dict[str, list[str]] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        match = re.match(r"^([A-Z][A-Z0-9])  - ?(.*)$", line)
        assert match, f"linha fora do padrão 'TAG  - valor': {line!r}"
        tag, value = match.groups()
        if tag == "ER":
            records.append(current)
            current = {}
        else:
            current.setdefault(tag, []).append(value)
    assert not current, "registro sem ER"
    return records


# ---------- BibTeX ----------


def test_bibtex_article_entry() -> None:
    text = to_bibtex([rec()])
    assert text.startswith("@article{souza2021letramento,\n")
    assert "  title = {{Letramento digital na educação 1}}," in text
    assert "  author = {Souza, Maria and de Albuquerque, João Pedro}," in text
    for field in ("year = {2021}", "doi = {10.1234/x1}", "url = {https://exemplo.org/1}"):
        assert field in text
    assert "abstract = {Resumo do trabalho.}" in text
    assert "keywords = {educação, tecnologia}" in text and "language = {pt}" in text
    assert text.rstrip().endswith("}")


@pytest.mark.parametrize(
    ("record_type", "entry"),
    [
        (RecordType.ARTICLE, "@article{"),
        (RecordType.THESIS, "@thesis{"),
        (RecordType.BOOK, "@book{"),
        (RecordType.PREPRINT, "@misc{"),
        (RecordType.OTHER, "@misc{"),
    ],
)
def test_bibtex_entry_types(record_type: RecordType, entry: str) -> None:
    assert entry in to_bibtex([rec(type=record_type)])


def test_bibtex_escapes_special_characters() -> None:
    raw = r"Dados & métodos: 50% de {chaves} $x$ #1 a_b ^ ~ \ fim"
    escaped = bibtex_escape(raw)
    assert escaped == (
        r"Dados \& métodos: 50\% de \{chaves\} \$x\$ \#1 a\_b \^{} \~{} \textbackslash{} fim"
    )
    text = to_bibtex([rec(title=raw, abstract=raw)])
    assert escaped in text
    for dangerous in ("& ", "% "):
        assert not re.search(
            rf"(?<!\\){re.escape(dangerous)}", text.split("title")[1].split("\n")[0]
        )


def test_bibtex_keys_are_unique_in_the_file() -> None:
    text = to_bibtex([rec(1), rec(2), rec(3), rec(4)])  # mesma autora, ano e primeira palavra
    keys = re.findall(r"@\w+\{([^,]+),", text)
    assert keys == [
        "souza2021letramento",
        "souza2021letramentoa",
        "souza2021letramentob",
        "souza2021letramentoc",
    ]
    assert len(set(keys)) == 4


def test_bibtex_key_for_record_without_year_authors_or_doi() -> None:
    text = to_bibtex(
        [rec(year=None, doi=None, authors=[], url=None, abstract=None, keywords=[], language=None)]
    )
    assert "@article{anonndletramento," in text
    for missing in ("author", "year", "doi", "url", "abstract", "keywords", "language"):
        assert f"  {missing} = " not in text


def test_bibtex_key_removes_accents_and_symbols() -> None:
    text = to_bibtex(
        [rec(authors=[AuthorOut(name="Ângela Mônica Müller-Çelik")], title="Ação & reação")]
    )
    assert text.startswith("@article{mullercelik2021acao,")


def test_bibtex_author_with_comma_and_single_name_are_kept() -> None:
    text = to_bibtex([rec(authors=[AuthorOut(name="Silva, João"), AuthorOut(name="Madonna")])])
    assert "author = {Silva, João and Madonna}" in text


def test_bibtex_empty_list() -> None:
    assert to_bibtex([]) == ""


# ---------- RIS ----------


def test_ris_round_trip() -> None:
    first = rec(1)
    second = rec(2, type=RecordType.THESIS, abstract=None, keywords=[], authors=[])
    parsed = parse_ris(to_ris([first, second]))
    assert len(parsed) == 2
    a, b = parsed
    assert a["TY"] == ["JOUR"] and a["TI"] == [first.title]
    assert a["AU"] == ["Maria Souza", "João Pedro de Albuquerque"]  # um AU por autor
    assert (
        a["PY"] == ["2021"] and a["DO"] == ["10.1234/x1"] and a["UR"] == ["https://exemplo.org/1"]
    )
    assert a["AB"] == ["Resumo do trabalho."] and a["KW"] == [
        "educação",
        "tecnologia",
    ]  # um KW por palavra
    assert a["LA"] == ["pt"]
    assert b["TY"] == ["THES"] and "AU" not in b and "AB" not in b and "KW" not in b


@pytest.mark.parametrize(
    ("record_type", "tag"),
    [(RecordType.ARTICLE, "JOUR"), (RecordType.THESIS, "THES"), (RecordType.BOOK, "BOOK"),
     (RecordType.PREPRINT, "GEN"), (RecordType.OTHER, "GEN")],
)  # fmt: skip
def test_ris_types(record_type: RecordType, tag: str) -> None:
    assert parse_ris(to_ris([rec(type=record_type)]))[0]["TY"] == [tag]


def test_ris_line_breaks_in_values_do_not_break_the_format() -> None:
    parsed = parse_ris(to_ris([rec(title="Linha um\nLinha dois", abstract="a\r\nb\n\nc")]))
    assert parsed[0]["TI"] == ["Linha um Linha dois"] and parsed[0]["AB"] == ["a b c"]


def test_ris_every_record_ends_with_er() -> None:
    text = to_ris([rec(1), rec(2)])
    assert text.count("ER  - ") == 2 and text.count("TY  - ") == 2


# ---------- JSON ----------


def test_json_round_trip() -> None:
    records = [rec(1), rec(2, title="Título com acentuação — ç ã")]
    text = to_json(records)
    assert "ç ã" in text  # ensure_ascii=False
    assert text.startswith("[\n  {")  # indent=2
    assert [RecordOut.model_validate(item) for item in json.loads(text)] == records


# ---------- CSV ----------


def test_csv_header_and_rows_follow_rfc4180() -> None:
    tricky = rec(
        2,
        title='Aspas "duplas", vírgula',
        authors=[AuthorOut(name="Maria Souza"), AuthorOut(name="Ana\nLima")],
    )
    text = to_csv([rec(1), tricky])
    assert (
        text.splitlines()[0]
        == "id,title,authors,year,doi,url,pdf_url,type,language,keywords,sources"
    )
    assert text.endswith("\r\n")
    rows = list(csv.reader(io.StringIO(text, newline="")))
    assert len(rows) == 3  # cabeçalho + 2 registros (a quebra de linha ficou entre aspas)
    assert rows[2][1] == 'Aspas "duplas", vírgula'
    assert rows[2][2] == "Maria Souza; Ana\nLima"
    assert rows[1][9] == "educação; tecnologia" and rows[1][10] == "openalex:W1"
    assert rows[1][3] == "2021" and rows[1][7] == "article"


def test_csv_neutralizes_formula_injection() -> None:
    attack = '=HYPERLINK("http://malicioso.example","clique")'
    text = to_csv([rec(title=attack, authors=[AuthorOut(name="+cmd|' /C calc'!A0")], doi=None)])
    row = list(csv.reader(io.StringIO(text, newline="")))[1]
    assert row[1] == "'" + attack
    assert row[2].startswith("'+cmd")
    for cell in row:
        assert not cell.startswith(("=", "+", "-", "@", "\t", "\r"))


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@", "\t", "\r"])
def test_csv_safe_prefixes(prefix: str) -> None:
    assert csv_safe(prefix + "x") == "'" + prefix + "x"


def test_csv_safe_leaves_normal_text_alone() -> None:
    assert csv_safe("Texto normal") == "Texto normal"
    assert csv_safe("") == ""
    assert csv_safe("2021") == "2021"


def test_csv_missing_values_are_empty() -> None:
    text = to_csv([rec(year=None, doi=None, url=None, language=None, keywords=[], authors=[])])
    row = list(csv.reader(io.StringIO(text, newline="")))[1]
    assert row[2] == "" and row[3] == "" and row[4] == "" and row[8] == "" and row[9] == ""
