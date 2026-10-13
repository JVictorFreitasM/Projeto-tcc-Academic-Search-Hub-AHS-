"""CLI administrativa dos eventos de segurança: `python -m app.cli_security <comando>`.

Não há painel nem rota de administração na API (fora do escopo): a consulta é por aqui.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, date, datetime

from app.core.loop import run_async
from app.db.session import get_engine, get_sessionmaker
from app.models.security_event import EVENT_TYPES
from app.services.security_events import DEFAULT_RETENTION_DAYS, list_events, purge_older_than

HASH_PREVIEW = 12


def emit(text: str = "") -> None:
    sys.stdout.write(text + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli_security", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    events = sub.add_parser("events", help="lista eventos (mais recentes primeiro)")
    events.add_argument("--type", choices=EVENT_TYPES, help="filtra pelo tipo")
    events.add_argument("--since", type=date.fromisoformat, help="a partir de AAAA-MM-DD")
    events.add_argument("--limit", type=int, default=50)
    purge = sub.add_parser("purge", help="apaga eventos antigos (retenção)")
    purge.add_argument(
        "--older-than-days",
        type=int,
        default=DEFAULT_RETENTION_DAYS,
        help=f"padrão: {DEFAULT_RETENTION_DAYS} (escolha do projeto, não exigência legal)",
    )
    return parser


async def cmd_events(event_type: str | None, since: date | None, limit: int) -> int:
    since_dt = datetime(since.year, since.month, since.day, tzinfo=UTC) if since else None
    try:
        async with get_sessionmaker()() as session:
            rows = await list_events(session, event_type=event_type, since=since_dt, limit=limit)
    finally:
        await get_engine().dispose()
    emit("data (UTC)\ttipo\tip (hash)\tdetalhes")
    for row in rows:
        digest = (row.ip_hash or "-")[:HASH_PREVIEW]
        details = json.dumps(row.details, ensure_ascii=False, sort_keys=True)
        emit(f"{row.created_at:%Y-%m-%d %H:%M:%S}\t{row.event_type}\t{digest}\t{details}")
    emit(f"{len(rows)} evento(s).")
    return 0


async def cmd_purge(days: int) -> int:
    try:
        async with get_sessionmaker()() as session:
            removed = await purge_older_than(session, days)
            await session.commit()
    finally:
        await get_engine().dispose()
    emit(f"{removed} evento(s) com mais de {days} dias apagado(s).")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "events":
            return run_async(cmd_events(args.type, args.since, args.limit))
        return run_async(cmd_purge(args.older_than_days))
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
