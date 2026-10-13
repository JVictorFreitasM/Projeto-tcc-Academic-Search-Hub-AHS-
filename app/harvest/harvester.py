"""Colheita OAI-PMH de uma fonte para a tabela `oai_records`."""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

import httpx
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.connectors.http import make_client
from app.core.config import Settings
from app.db.session import get_sessionmaker
from app.harvest.mapping import parse_oai_dc
from app.harvest.oai_client import DEFAULT_MAX_PAGES, OaiClient, OaiError, Sleep
from app.harvest.oai_sources import OaiSourceConfig
from app.models import HarvestRun, OaiRecord

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 500
_UPDATE_COLUMNS = (
    "datestamp",
    "title",
    "authors",
    "abstract",
    "year",
    "doi",
    "url",
    "pdf_url",
    "type",
    "language",
    "keywords",
    "raw_types",
)


class HarvestError(Exception):
    """Erro de colheita com mensagem pronta para o usuário (sem dados sensíveis)."""


@dataclass
class HarvestSummary:
    source: str
    status: str = "running"
    records_read: int = 0
    records_upserted: int = 0
    records_deleted: int = 0
    records_ignored: int = 0
    dry_run: bool = False
    run_id: uuid.UUID | None = None
    samples: list[dict[str, Any]] = field(default_factory=list)


def _require_run(run_id: uuid.UUID | None) -> uuid.UUID:
    """Fora do modo de simulação sempre existe um registro de colheita."""
    if run_id is None:
        raise HarvestError("Colheita sem registro de execução.")
    return run_id


async def last_ok_date(session: AsyncSession, slug: str) -> date | None:
    """Data de início da última colheita bem-sucedida da fonte."""
    started = (
        await session.execute(
            select(func.max(HarvestRun.started_at)).where(
                HarvestRun.source == slug, HarvestRun.status == "ok"
            )
        )
    ).scalar_one()
    return started.astimezone(UTC).date() if started else None


async def _flush(
    session_factory: async_sessionmaker[AsyncSession],
    slug: str,
    rows: dict[str, dict[str, Any]],
    deleted_ids: set[str],
    run_id: uuid.UUID,
    summary: HarvestSummary,
    token: str | None,
) -> None:
    async with session_factory() as session:
        if rows:
            stmt = insert(OaiRecord).values(list(rows.values()))
            stmt = stmt.on_conflict_do_update(
                index_elements=["source", "oai_identifier"],
                set_={
                    **{col: getattr(stmt.excluded, col) for col in _UPDATE_COLUMNS},
                    "deleted": False,
                    "harvested_at": func.now(),
                },
            )
            await session.execute(stmt)
        if deleted_ids:
            await session.execute(
                update(OaiRecord)
                .where(OaiRecord.source == slug, OaiRecord.oai_identifier.in_(deleted_ids))
                .values(deleted=True)
            )
        await session.execute(
            update(HarvestRun)
            .where(HarvestRun.id == run_id)
            .values(
                records_read=summary.records_read,
                records_upserted=summary.records_upserted,
                records_deleted=summary.records_deleted,
                last_resumption_token=token,
            )
        )
        await session.commit()


async def harvest_source(
    source: OaiSourceConfig,
    settings: Settings,
    *,
    full: bool = False,
    limit: int | None = None,
    dry_run: bool = False,
    max_pages: int = DEFAULT_MAX_PAGES,
    batch_size: int = DEFAULT_BATCH_SIZE,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    http_client: httpx.AsyncClient | None = None,
    sleep: Sleep = asyncio.sleep,
) -> HarvestSummary:
    """Colhe a fonte. Incremental por padrão; `full` ignora a data da última colheita."""
    if not settings.contact_email:
        raise HarvestError("CONTACT_EMAIL é obrigatório para colher (identifica o cliente).")
    if not source.has_valid_url:
        raise HarvestError(f"A fonte '{source.slug}' não tem base_url configurada.")
    if not dry_run and not source.enabled:
        raise HarvestError(f"A fonte '{source.slug}' está com enabled: false.")

    factory = session_factory or get_sessionmaker()
    summary = HarvestSummary(source=source.slug, dry_run=dry_run)
    own_client = http_client is None
    client = http_client or make_client(settings)
    oai = OaiClient(
        source.base_url, client, delay_seconds=settings.oai_harvest_delay_seconds, sleep=sleep
    )

    from_date: date | None = None
    run_id: uuid.UUID | None = None
    if not dry_run:
        async with factory() as session:
            if not full:
                from_date = await last_ok_date(session, source.slug)
            run = HarvestRun(source=source.slug, status="running")
            session.add(run)
            await session.flush()
            run_id = run.id
            await session.commit()
        summary.run_id = run_id

    rows: dict[str, dict[str, Any]] = {}
    deleted_ids: set[str] = set()
    limited = False
    try:
        async for raw in oai.list_records(
            source.metadata_prefix, source.set_spec, from_date, max_pages=max_pages
        ):
            if limit is not None and summary.records_read >= limit:
                limited = True
                break
            summary.records_read += 1
            if raw.deleted:
                summary.records_deleted += 1
                deleted_ids.add(raw.identifier)
                rows.pop(raw.identifier, None)
                continue
            row = parse_oai_dc(raw, source)
            if row is None:
                summary.records_ignored += 1
                continue
            deleted_ids.discard(raw.identifier)
            rows[raw.identifier] = row
            summary.records_upserted += 1
            if dry_run:
                if len(summary.samples) < 3:
                    summary.samples.append(row)
                rows.clear()
            elif len(rows) >= batch_size:
                await _flush(
                    factory,
                    source.slug,
                    rows,
                    deleted_ids,
                    _require_run(run_id),
                    summary,
                    oai.last_resumption_token,
                )
                rows, deleted_ids = {}, set()
        if not dry_run:
            await _flush(
                factory,
                source.slug,
                rows,
                deleted_ids,
                _require_run(run_id),
                summary,
                oai.last_resumption_token,
            )
    except OaiError as exc:
        await _finish(factory, run_id, "error", str(exc), summary)
        raise HarvestError(f"Colheita de '{source.slug}' falhou: {exc}") from None
    except Exception as exc:
        logger.error("Falha inesperada na colheita", extra={"source": source.slug}, exc_info=exc)
        await _finish(factory, run_id, "error", f"{type(exc).__name__}", summary)
        raise HarvestError(f"Colheita de '{source.slug}' falhou: erro interno.") from None
    finally:
        if own_client:
            await client.aclose()

    status = "partial" if (summary.records_ignored or limited) else "ok"
    await _finish(factory, run_id, status, None, summary)
    return summary


async def _finish(
    factory: async_sessionmaker[AsyncSession],
    run_id: uuid.UUID | None,
    status: str,
    message: str | None,
    summary: HarvestSummary,
) -> None:
    summary.status = status
    if run_id is None:
        return
    async with factory() as session:
        await session.execute(
            update(HarvestRun)
            .where(HarvestRun.id == run_id)
            .values(
                status=status,
                finished_at=datetime.now(UTC),
                error_message=message[:500] if message else None,
            )
        )
        await session.commit()
