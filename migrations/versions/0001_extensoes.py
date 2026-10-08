"""Extensões, função immutable_unaccent e configuração de busca pt_unaccent.

Revision ID: 0001
Revises:
Create Date: 2026-10-08
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    # `unaccent` é STABLE; índices e colunas geradas exigem IMMUTABLE. O wrapper fixa o
    # dicionário (esquema qualificado), o que o torna seguro de declarar IMMUTABLE.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION immutable_unaccent(text) RETURNS text
        LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
        AS $$ SELECT public.unaccent('public.unaccent'::regdictionary, $1) $$
        """
    )
    op.execute("CREATE TEXT SEARCH CONFIGURATION pt_unaccent (COPY = portuguese)")
    op.execute(
        """
        ALTER TEXT SEARCH CONFIGURATION pt_unaccent
        ALTER MAPPING FOR hword, hword_part, word WITH unaccent, portuguese_stem
        """
    )


def downgrade() -> None:
    op.execute("DROP TEXT SEARCH CONFIGURATION IF EXISTS pt_unaccent")
    op.execute("DROP FUNCTION IF EXISTS immutable_unaccent(text)")
    # As extensões ficam: criá-las costuma exigir privilégio e outros bancos podem usá-las.
