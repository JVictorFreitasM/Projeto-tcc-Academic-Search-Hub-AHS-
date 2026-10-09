"""Leitura e validação de `config/oai_sources.yml` (fontes OAI-PMH)."""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.common import RecordType

PLACEHOLDER_URL = "TODO-VERIFICAR"
RESERVED_SLUGS = frozenset({"openalex", "core"})
_SLUG_RE = re.compile(r"^[a-z0-9_]+$")


class SourceConfigError(ValueError):
    """Arquivo de fontes inválido (a mensagem não inclui credenciais)."""


class OaiSourceConfig(BaseModel):
    slug: str
    name: str = Field(min_length=1)
    base_url: str
    metadata_prefix: str = "oai_dc"
    set_spec: str | None = None
    enabled: bool = False
    default_type: RecordType = RecordType.OTHER
    type_map: dict[str, RecordType] = Field(default_factory=dict)

    @field_validator("slug")
    @classmethod
    def _slug(cls, value: str) -> str:
        if not _SLUG_RE.match(value):
            raise ValueError("slug deve usar apenas a-z, 0-9 e _")
        if value in RESERVED_SLUGS:
            raise ValueError(f"slug '{value}' é reservado")
        return value

    @model_validator(mode="after")
    def _url_required_when_enabled(self) -> OaiSourceConfig:
        if self.enabled and not self.has_valid_url:
            raise ValueError(f"fonte '{self.slug}' habilitada precisa de base_url http(s) válida")
        return self

    @property
    def has_valid_url(self) -> bool:
        return self.base_url.startswith(("https://", "http://")) and " " not in self.base_url

    @property
    def uses_plain_http(self) -> bool:
        return self.base_url.startswith("http://")


class _SourcesFile(BaseModel):
    sources: list[OaiSourceConfig]

    @model_validator(mode="after")
    def _unique_slugs(self) -> _SourcesFile:
        slugs = [item.slug for item in self.sources]
        duplicated = {slug for slug in slugs if slugs.count(slug) > 1}
        if duplicated:
            raise ValueError(f"slugs repetidos: {', '.join(sorted(duplicated))}")
        return self


def load_oai_sources(path: str | Path) -> list[OaiSourceConfig]:
    """Carrega o YAML com `safe_load` e valida cada entrada."""
    file = Path(path)
    try:
        data = yaml.safe_load(file.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SourceConfigError(f"Não foi possível ler {file.name}: {exc.strerror}") from None
    except yaml.YAMLError:
        raise SourceConfigError(f"{file.name} não é um YAML válido") from None
    try:
        return _SourcesFile.model_validate(data or {"sources": []}).sources
    except ValueError as exc:
        raise SourceConfigError(f"{file.name} inválido: {exc}") from None


def get_source(sources: list[OaiSourceConfig], slug: str) -> OaiSourceConfig:
    for item in sources:
        if item.slug == slug:
            return item
    known = ", ".join(item.slug for item in sources) or "nenhuma"
    raise SourceConfigError(f"Fonte '{slug}' não existe. Fontes configuradas: {known}")
