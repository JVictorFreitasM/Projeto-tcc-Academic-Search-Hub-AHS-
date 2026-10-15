"""Índice local dos registros colhidos por OAI-PMH (todas as fontes)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, deferred, mapped_column

from app.db.base import Base
from app.schemas.common import RECORD_TYPE_VALUES


class OaiRecord(Base):
    __tablename__ = "oai_records"
    __table_args__ = (
        UniqueConstraint("source", "oai_identifier", name="uq_oai_records_source_oai_identifier"),
        CheckConstraint(
            "type IN (" + ", ".join(f"'{item}'" for item in RECORD_TYPE_VALUES) + ")",
            name="type_allowed",
        ),
        Index("ix_oai_records_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_oai_records_author_vector", "author_vector", postgresql_using="gin"),
        Index("ix_oai_records_source", "source"),
        Index("ix_oai_records_year", "year"),
        Index("ix_oai_records_type", "type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    source: Mapped[str] = mapped_column(Text)
    oai_identifier: Mapped[str] = mapped_column(Text)
    datestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    title: Mapped[str] = mapped_column(Text)
    authors: Mapped[list[Any]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    abstract: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    doi: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    pdf_url: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str] = mapped_column(Text, server_default=text("'other'"))
    language: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[list[Any]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    raw_types: Mapped[list[Any]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    # Mantida por gatilho no banco (migração 0002): título peso A, palavras-chave B, resumo C.
    search_vector: Mapped[str | None] = deferred(mapped_column(TSVECTOR))
    # Nomes dos autores, sem acento e sem radical; mantida por gatilho (migração 0003).
    author_vector: Mapped[str | None] = deferred(mapped_column(TSVECTOR))
    harvested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
