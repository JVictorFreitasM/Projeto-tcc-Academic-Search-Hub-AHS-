"""Monta a lista de conectores a partir da configuração."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.connectors.base import Connector
from app.connectors.bdtd_api import BdtdConnector
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
    """Cria OpenAlex, CORE, BDTD e um conector local por fonte OAI do YAML (habilitada ou não)."""
    connectors: list[Connector] = [
        OpenAlexConnector(settings),
        CoreConnector(settings),
        BdtdConnector(settings),
    ]
    try:
        sources = load_oai_sources(settings.oai_sources_file)
    except SourceConfigError as exc:
        logger.warning("Fontes OAI ignoradas: %s", exc)
        sources = []
    factory = session_factory or get_sessionmaker()
    api_slugs = {c.slug for c in connectors}
    for source in sources:
        if source.slug in api_slugs:  # ex.: `bdtd` no YAML, depois que ela passou a ser por API
            logger.warning(
                "Fonte OAI ignorada: já consultada por API", extra={"source": source.slug}
            )
            continue
        connectors.append(
            OaiLocalConnector(source.slug, source.name, factory, enabled=source.enabled)
        )
    position = {slug: index for index, slug in enumerate(SOURCE_ORDER)}
    return sorted(connectors, key=lambda c: position.get(c.slug, len(SOURCE_ORDER)))
