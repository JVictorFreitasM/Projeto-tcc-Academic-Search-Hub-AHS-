"""Registro de cada colheita OAI-PMH."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

HARVEST_STATUSES = ("running", "ok", "error", "partial")


class HarvestRun(Base):
    __tablename__ = "harvest_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN (" + ", ".join(f"'{item}'" for item in HARVEST_STATUSES) + ")",
            name="status_allowed",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    source: Mapped[str] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(Text, server_default=text("'running'"))
    records_read: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    records_upserted: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    records_deleted: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    last_resumption_token: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
