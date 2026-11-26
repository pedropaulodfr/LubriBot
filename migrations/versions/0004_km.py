"""Notificação por quilometragem.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-25

Adiciona:
- ``servicos.intervaloKm``: intervalo de troca/revisão em km (opcional);
- ``veiculos.kmAtual``: odômetro informado pelo usuário;
- ``veiculos.kmAtualizadoEm``: quando o odômetro foi informado.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('ALTER TABLE servicos ADD COLUMN IF NOT EXISTS "intervaloKm" integer')
    op.execute('ALTER TABLE veiculos ADD COLUMN IF NOT EXISTS "kmAtual" integer')
    op.execute(
        'ALTER TABLE veiculos ADD COLUMN IF NOT EXISTS "kmAtualizadoEm" timestamptz'
    )


def downgrade() -> None:
    op.execute('ALTER TABLE veiculos DROP COLUMN IF EXISTS "kmAtualizadoEm"')
    op.execute('ALTER TABLE veiculos DROP COLUMN IF EXISTS "kmAtual"')
    op.execute('ALTER TABLE servicos DROP COLUMN IF EXISTS "intervaloKm"')
