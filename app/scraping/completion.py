"""Completa o resumo de registros que vieram sem ele (raspagem complementar, D8)."""

from __future__ import annotations

import asyncio
import logging

from app.schemas.record import RecordOut
from app.scraping.abstract_extractor import extract_abstract
from app.scraping.polite_scraper import PoliteScraper

logger = logging.getLogger(__name__)

MAX_PER_SEARCH = 5
OVERALL_TIMEOUT_SECONDS = 15.0


async def complete_abstracts(
    records: list[RecordOut],
    scraper: PoliteScraper,
    *,
    limit: int = MAX_PER_SEARCH,
    overall_timeout: float = OVERALL_TIMEOUT_SECONDS,
) -> list[RecordOut]:
    """Devolve a lista com o resumo preenchido onde foi possível.

    Só mexe em registros com `abstract` vazio e `url` http/https, no máximo `limit` por busca.
    Qualquer falha é silenciosa (log INFO) e nunca altera o estado das fontes.
    """
    pending = [i for i, r in enumerate(records) if not r.abstract and r.url][:limit]
    if not pending:
        return records
    completed = list(records)

    async def work() -> None:
        for index in pending:
            record = records[index]
            try:
                html = await scraper.fetch(record.url or "")
                abstract = extract_abstract(html) if html else None
            except Exception:
                logger.info("Raspagem do resumo falhou", extra={"record_id": record.id})
                continue
            if abstract:
                completed[index] = record.model_copy(update={"abstract": abstract})
                logger.info("Resumo completado por raspagem", extra={"record_id": record.id})

    try:
        await asyncio.wait_for(work(), timeout=overall_timeout)
    except TimeoutError:
        logger.info("Raspagem interrompida pelo tempo limite")
    return completed
