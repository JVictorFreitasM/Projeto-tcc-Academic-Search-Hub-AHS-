"""Busca por autor: coluna `author_vector`, configuração sem radical e gatilho (OS pós-entrega).

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-15

A busca por tema usa `pt_unaccent`, que reduz as palavras ao radical (bom para texto corrido, ruim
para nomes: "Paulo" e "Paula" virariam a mesma coisa). Para autores, a configuração
`unaccent_simple` só tira o acento e põe em minúsculas.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE TEXT SEARCH CONFIGURATION unaccent_simple (COPY = simple)")
    op.execute(
        """
        ALTER TEXT SEARCH CONFIGURATION unaccent_simple
        ALTER MAPPING FOR hword, hword_part, word WITH unaccent, simple
        """
    )
    op.add_column("oai_records", sa.Column("author_vector", postgresql.TSVECTOR(), nullable=True))
    # Os nomes ficam no JSONB `authors` ([{"name": ..., "orcid": ...}]); o gatilho os junta.
    op.execute(
        """
        CREATE FUNCTION oai_records_author_vector_update() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            NEW.author_vector := to_tsvector('unaccent_simple', coalesce((
                SELECT string_agg(a ->> 'name', ' ') FROM jsonb_array_elements(NEW.authors) AS a
            ), ''));
            RETURN NEW;
        END
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_oai_records_author_vector
        BEFORE INSERT OR UPDATE OF authors ON oai_records
        FOR EACH ROW EXECUTE FUNCTION oai_records_author_vector_update()
        """
    )
    # Preenche os registros que já existem (a atualização de `authors` dispara o gatilho).
    op.execute("UPDATE oai_records SET authors = authors")
    op.create_index(
        "ix_oai_records_author_vector",
        "oai_records",
        ["author_vector"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_oai_records_author_vector", table_name="oai_records", postgresql_using="gin")
    op.execute("DROP TRIGGER IF EXISTS trg_oai_records_author_vector ON oai_records")
    op.execute("DROP FUNCTION IF EXISTS oai_records_author_vector_update()")
    op.drop_column("oai_records", "author_vector")
    op.execute("DROP TEXT SEARCH CONFIGURATION IF EXISTS unaccent_simple")
