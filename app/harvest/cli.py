"""CLI da colheita: `python -m app.harvest.cli <comando>`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import func, select

from app.connectors.http import make_client
from app.core.config import ConfigError, Settings, get_settings
from app.core.logging import configure_logging
from app.core.loop import run_async
from app.db.session import get_engine, get_sessionmaker
from app.harvest.harvester import HarvestError, HarvestSummary, harvest_source
from app.harvest.oai_client import OaiClient, OaiError
from app.harvest.oai_sources import (
    OaiSourceConfig,
    SourceConfigError,
    get_source,
    load_oai_sources,
)
from app.models import HarvestRun, OaiRecord

EXIT_OK, EXIT_ERROR, EXIT_USAGE = 0, 1, 2


def emit(text: str = "") -> None:
    sys.stdout.write(text + "\n")


def fail(text: str) -> None:
    sys.stderr.write(text + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.harvest.cli", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (("identify", "mostra o Identify da fonte"), ("sets", "lista os sets")):
        item = sub.add_parser(name, help=help_text)
        item.add_argument("slug")
    dump = sub.add_parser("dump", help="grava Identify e uma página de ListRecords (fixtures)")
    dump.add_argument("slug")
    dump.add_argument("--out", type=Path, help="pasta de saída (padrão: tests/fixtures/oai/<slug>)")
    run = sub.add_parser("run", help="colhe uma fonte")
    run.add_argument("slug")
    run.add_argument("--full", action="store_true", help="ignora a data da última colheita")
    run.add_argument("--limit", type=int, help="máximo de registros lidos")
    run.add_argument("--max-pages", type=int, default=100_000)
    run.add_argument("--dry-run", action="store_true", help="não grava no banco")
    run_all = sub.add_parser("run-all", help="colhe todas as fontes habilitadas")
    run_all.add_argument("--full", action="store_true")
    run_all.add_argument("--max-pages", type=int, default=100_000)
    sub.add_parser("status", help="última colheita e total de registros por fonte")
    return parser


def _oai_client(settings: Settings, source: OaiSourceConfig) -> tuple[OaiClient, object]:
    if not settings.contact_email:
        raise HarvestError("CONTACT_EMAIL é obrigatório para falar com as fontes.")
    if not source.has_valid_url:
        raise HarvestError(f"A fonte '{source.slug}' não tem base_url configurada.")
    http = make_client(settings)
    return OaiClient(source.base_url, http, delay_seconds=settings.oai_harvest_delay_seconds), http


async def cmd_identify(settings: Settings, source: OaiSourceConfig) -> int:
    client, http = _oai_client(settings, source)
    try:
        info = await client.identify()
    finally:
        await http.aclose()  # type: ignore[attr-defined]
    emit(json.dumps(info, ensure_ascii=False, indent=2))
    return EXIT_OK


async def cmd_sets(settings: Settings, source: OaiSourceConfig) -> int:
    client, http = _oai_client(settings, source)
    try:
        async for spec, name in client.list_sets():
            emit(f"{spec}\t{name}")
    finally:
        await http.aclose()  # type: ignore[attr-defined]
    return EXIT_OK


async def cmd_dump(settings: Settings, source: OaiSourceConfig, out: Path | None) -> int:
    client, http = _oai_client(settings, source)
    folder = out or Path("tests/fixtures/oai") / source.slug
    folder.mkdir(parents=True, exist_ok=True)
    try:
        (folder / "identify.xml").write_bytes(await client.fetch_raw({"verb": "Identify"}))
        params = {"verb": "ListRecords", "metadataPrefix": source.metadata_prefix}
        if source.set_spec:
            params["set"] = source.set_spec
        (folder / "list_records.xml").write_bytes(await client.fetch_raw(params))
    finally:
        await http.aclose()  # type: ignore[attr-defined]
    emit(f"Gravado em {folder}: identify.xml e list_records.xml (revise antes de commitar).")
    return EXIT_OK


def print_summary(summary: HarvestSummary) -> None:
    mode = " (simulação, nada foi gravado)" if summary.dry_run else ""
    emit(
        f"{summary.source}: {summary.status}{mode} | lidos={summary.records_read} "
        f"gravados={summary.records_upserted} removidos={summary.records_deleted} "
        f"ignorados={summary.records_ignored}"
    )
    for sample in summary.samples:
        emit("  exemplo: " + json.dumps(sample, ensure_ascii=False, default=str)[:400])


async def cmd_run(settings: Settings, source: OaiSourceConfig, args: argparse.Namespace) -> int:
    try:
        summary = await harvest_source(
            source,
            settings,
            full=args.full,
            limit=args.limit,
            dry_run=args.dry_run,
            max_pages=args.max_pages,
        )
    finally:
        await get_engine().dispose()
    print_summary(summary)
    return EXIT_OK


async def cmd_run_all(settings: Settings, sources: list[OaiSourceConfig], args: object) -> int:
    code = EXIT_OK
    try:
        for source in (s for s in sources if s.enabled):
            try:
                summary = await harvest_source(
                    source,
                    settings,
                    full=getattr(args, "full", False),
                    max_pages=getattr(args, "max_pages", 100_000),
                )
                print_summary(summary)
            except HarvestError as exc:
                fail(str(exc))
                code = EXIT_ERROR
    finally:
        await get_engine().dispose()
    return code


async def cmd_status(sources: list[OaiSourceConfig]) -> int:
    try:
        async with get_sessionmaker()() as session:
            for source in sources:
                total = (
                    await session.execute(
                        select(func.count())
                        .select_from(OaiRecord)
                        .where(OaiRecord.source == source.slug)
                    )
                ).scalar_one()
                last = (
                    await session.execute(
                        select(HarvestRun)
                        .where(HarvestRun.source == source.slug)
                        .order_by(HarvestRun.started_at.desc())
                        .limit(1)
                    )
                ).scalar_one_or_none()
                state = "habilitada" if source.enabled else "desabilitada"
                if last is None:
                    emit(f"{source.slug} ({state}): {total} registros | nenhuma colheita")
                else:
                    emit(
                        f"{source.slug} ({state}): {total} registros | última colheita: "
                        f"{last.status} em {last.started_at:%Y-%m-%d %H:%M} "
                        f"(lidos={last.records_read} gravados={last.records_upserted})"
                    )
    finally:
        await get_engine().dispose()
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = get_settings()
        configure_logging(settings.log_level)
        sources = load_oai_sources(settings.oai_sources_file)
        if args.command == "status":
            return run_async(cmd_status(sources))
        if args.command == "run-all":
            return run_async(cmd_run_all(settings, sources, args))
        source = get_source(sources, args.slug)
        if args.command == "identify":
            return run_async(cmd_identify(settings, source))
        if args.command == "sets":
            return run_async(cmd_sets(settings, source))
        if args.command == "dump":
            return run_async(cmd_dump(settings, source, args.out))
        return run_async(cmd_run(settings, source, args))
    except (ConfigError, SourceConfigError) as exc:
        fail(str(exc))
        return EXIT_USAGE
    except (HarvestError, OaiError) as exc:
        fail(str(exc))
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
