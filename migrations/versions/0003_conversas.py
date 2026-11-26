"""Conversas em andamento por chat (retomada após restart).

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-25
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS conversas (
            chat_id bigint PRIMARY KEY,
            fluxo varchar(32) NOT NULL,
            etapa varchar(64),
            dados jsonb,
            "atualizadoEm" timestamptz DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_conversas_fluxo ON conversas (fluxo)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS conversas")
