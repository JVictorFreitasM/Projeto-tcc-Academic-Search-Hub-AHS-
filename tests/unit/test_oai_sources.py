from pathlib import Path

import pytest

from app.harvest.oai_sources import SourceConfigError, get_source, load_oai_sources

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]


def write(tmp_path: Path, text: str) -> Path:
    file = tmp_path / "fontes.yml"
    file.write_text(text, encoding="utf-8")
    return file


def test_project_file_has_the_expected_sources() -> None:
    sources = load_oai_sources(ROOT / "config" / "oai_sources.yml")
    assert [s.slug for s in sources] == ["scielo", "bdtd", "ufpi", "uespi", "ufpe"]
    # Só a UFPE tem OAI-PMH funcionando (colhida em 15/10/2026); as demais seguem desligadas.
    assert {s.slug for s in sources if s.enabled} == {"ufpe"}
    assert {s.slug: s.default_type.value for s in sources}["bdtd"] == "thesis"


def test_valid_source(tmp_path: Path) -> None:
    file = write(
        tmp_path,
        """
sources:
  - slug: minha_fonte
    name: Minha fonte
    base_url: https://oai.exemplo.org/oai
    enabled: true
    default_type: thesis
    type_map: {"Trabalho Acadêmico": thesis}
""",
    )
    (source,) = load_oai_sources(file)
    assert source.metadata_prefix == "oai_dc" and source.set_spec is None
    assert source.has_valid_url and not source.uses_plain_http
    assert source.type_map["Trabalho Acadêmico"].value == "thesis"


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("sources:\n  - {slug: 'Fonte Ruim', name: x, base_url: https://a.org}", "slug"),
        ("sources:\n  - {slug: core, name: x, base_url: https://a.org}", "reservado"),
        (
            "sources:\n  - {slug: a, name: x, base_url: https://a.org}\n"
            "  - {slug: a, name: y, base_url: https://b.org}",
            "repetidos",
        ),
        ("sources:\n  - {slug: a, name: x, base_url: TODO-VERIFICAR, enabled: true}", "base_url"),
        (
            "sources:\n  - {slug: a, name: x, base_url: https://a.org, default_type: filme}",
            "default_type",
        ),
        ("sources: [", "YAML"),
    ],
)
def test_invalid_files(tmp_path: Path, body: str, message: str) -> None:
    with pytest.raises(SourceConfigError, match=message):
        load_oai_sources(write(tmp_path, body))


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(SourceConfigError, match="Não foi possível ler"):
        load_oai_sources(tmp_path / "nao_existe.yml")


def test_plain_http_is_detected(tmp_path: Path) -> None:
    (source,) = load_oai_sources(
        write(tmp_path, "sources:\n  - {slug: a, name: x, base_url: 'http://a.org/oai'}")
    )
    assert source.uses_plain_http and source.has_valid_url


def test_get_source(tmp_path: Path) -> None:
    sources = load_oai_sources(write(tmp_path, "sources:\n  - {slug: a, name: x, base_url: u}"))
    assert get_source(sources, "a").slug == "a"
    with pytest.raises(SourceConfigError, match="não existe"):
        get_source(sources, "b")
