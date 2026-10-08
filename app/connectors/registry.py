"""Monta a lista de conectores a partir da configuração."""

from __future__ import annotations

from app.connectors.base import Connector
from app.core.config import Settings

# Ordem fixa das fontes (6.4 e 5.5); fontes OAI novas entram depois, na ordem do YAML.
SOURCE_ORDER = ("openalex", "core", "scielo", "bdtd", "ufpi", "uespi")


def build_connectors(settings: Settings) -> list[Connector]:
    """Cria os conectores. Os conectores reais são acrescentados nas OS-007, 008 e 010."""
    connectors: list[Connector] = []
    return sorted(
        connectors,
        key=lambda c: SOURCE_ORDER.index(c.slug) if c.slug in SOURCE_ORDER else len(SOURCE_ORDER),
    )
