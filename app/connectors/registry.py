"""Monta a lista de conectores a partir da configuração."""

from __future__ import annotations

from app.connectors.base import Connector
from app.connectors.openalex import OpenAlexConnector
from app.core.config import Settings

# Ordem fixa das fontes (6.4 e 5.5); fontes OAI novas entram depois, na ordem do YAML.
SOURCE_ORDER = ("openalex", "core", "scielo", "bdtd", "ufpi", "uespi")


def build_connectors(settings: Settings) -> list[Connector]:
    """Cria os conectores. O CORE e as fontes OAI são acrescentados nas OS-008 e 010."""
    connectors: list[Connector] = [OpenAlexConnector(settings)]
    return sorted(
        connectors,
        key=lambda c: SOURCE_ORDER.index(c.slug) if c.slug in SOURCE_ORDER else len(SOURCE_ORDER),
    )
