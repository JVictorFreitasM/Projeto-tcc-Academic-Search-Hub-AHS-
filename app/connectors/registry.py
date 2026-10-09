"""Monta a lista de conectores a partir da configuração."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.connectors.base import Connector
from app.connectors.core_api import CoreConnector
from app.connectors.oai_local import OaiLocalConnector
from app.connectors.openalex import OpenAlexConnector
from app.core.config import Settings
from app.db.session import get_sessionmaker
from app.harvest.oai_sources import SourceConfigError, load_oai_sources

logger = logging.getLogger(__name__)

# Ordem fixa das fontes (6.4 e 5.5); fontes OAI novas entram depois, na ordem do YAML.
SOURCE_ORDER = ("openalex", "core", "scielo", "bdtd", "ufpi", "uespi")


def build_connectors(
    settings: Settings, session_factory: async_sessionmaker[AsyncSession] | None = None
) -> list[Connector]:
    """Cria OpenAlex, CORE e um conector local por fonte declarada no YAML (habilitada ou não)."""
    connectors: list[Connector] = [OpenAlexConnector(settings), CoreConnector(settings)]
    try:
        sources = load_oai_sources(settings.oai_sources_file)
    except SourceConfigError as exc:
        logger.warning("Fontes OAI ignoradas: %s", exc)
        sources = []
    factory = session_factory or get_sessionmaker()
    connectors.extend(
        OaiLocalConnector(s.slug, s.name, factory, enabled=s.enabled) for s in sources
    )
    position = {slug: index for index, slug in enumerate(SOURCE_ORDER)}
    return sorted(connectors, key=lambda c: position.get(c.slug, len(SOURCE_ORDER)))
