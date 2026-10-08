"""Tabelas de domínio (gerada por autogenerate e revisada à mão).

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "harvest_runs",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Text(), server_default=sa.text("'running'"), nullable=False),
        sa.Column("records_read", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("records_upserted", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("records_deleted", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_resumption_token", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('running', 'ok', 'error', 'partial')",
            name=op.f("ck_harvest_runs_status_allowed"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_harvest_runs")),
    )
    op.create_table(
        "oai_records",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("oai_identifier", sa.Text(), nullable=False),
        sa.Column("datestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column(
            "authors",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("doi", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("pdf_url", sa.Text(), nullable=True),
        sa.Column("type", sa.Text(), server_default=sa.text("'other'"), nullable=False),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column(
            "keywords",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "raw_types",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column(
            "harvested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "type IN ('article', 'thesis', 'preprint', 'book', 'other')",
            name=op.f("ck_oai_records_type_allowed"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oai_records")),
        sa.UniqueConstraint(
            "source", "oai_identifier", name="uq_oai_records_source_oai_identifier"
        ),
    )
    op.create_index(
        "ix_oai_records_search_vector",
        "oai_records",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index("ix_oai_records_source", "oai_records", ["source"], unique=False)
    op.create_index("ix_oai_records_type", "oai_records", ["type"], unique=False)
    op.create_index("ix_oai_records_year", "oai_records", ["year"], unique=False)
    # `search_vector` por gatilho (coluna gerada não aceita achatar o JSONB de palavras-chave):
    # título com peso A, palavras-chave com peso B, resumo com peso C.
    op.execute(
        """
        CREATE FUNCTION oai_records_search_vector_update() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('pt_unaccent', coalesce(NEW.title, '')), 'A')
                || setweight(to_tsvector('pt_unaccent', coalesce((
                    SELECT string_agg(k, ' ') FROM jsonb_array_elements_text(NEW.keywords) AS k
                ), '')), 'B')
                || setweight(to_tsvector('pt_unaccent', coalesce(NEW.abstract, '')), 'C');
            RETURN NEW;
        END
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_oai_records_search_vector
        BEFORE INSERT OR UPDATE OF title, abstract, keywords ON oai_records
        FOR EACH ROW EXECUTE FUNCTION oai_records_search_vector_update()
        """
    )
    op.create_table(
        "security_events",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("ip_hash", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "event_type IN ('login_failed', 'login_success', 'rate_limited', 'account_deleted', 'password_changed', 'data_exported', 'account_registered')",
            name=op.f("ck_security_events_event_type_allowed"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_security_events")),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consent_policy_version", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.CheckConstraint("email = lower(email)", name=op.f("ck_users_email_lowercase")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_table(
        "favorites",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("record_id", sa.Text(), nullable=False),
        sa.Column("record_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("char_length(note) <= 1000", name=op.f("ck_favorites_note_max_length")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_favorites_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_favorites")),
        sa.UniqueConstraint("user_id", "record_id", name="uq_favorites_user_id_record_id"),
    )
    op.create_index(
        "ix_favorites_user_id_created_at",
        "favorites",
        ["user_id", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_table(
        "search_history",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("query", sa.String(length=200), nullable=False),
        sa.Column(
            "filters",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("result_count_estimated", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_search_history_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_search_history")),
    )
    op.create_index(
        "ix_search_history_user_id_created_at",
        "search_history",
        ["user_id", sa.literal_column("created_at DESC")],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index("ix_search_history_user_id_created_at", table_name="search_history")
    op.drop_table("search_history")
    op.drop_index("ix_favorites_user_id_created_at", table_name="favorites")
    op.drop_table("favorites")
    op.drop_table("users")
    op.drop_table("security_events")
    op.drop_index("ix_oai_records_year", table_name="oai_records")
    op.drop_index("ix_oai_records_type", table_name="oai_records")
    op.drop_index("ix_oai_records_source", table_name="oai_records")
    op.drop_index("ix_oai_records_search_vector", table_name="oai_records", postgresql_using="gin")
    op.execute("DROP TRIGGER IF EXISTS trg_oai_records_search_vector ON oai_records")
    op.drop_table("oai_records")
    op.execute("DROP FUNCTION IF EXISTS oai_records_search_vector_update()")
    op.drop_table("harvest_runs")
