"""Baseline: schema legado do LubriBot (Fase 0).

Esta revisão representa o schema que já existe em produção/QA no momento da
modernização. Ela é criada para instalações novas e serve de ponto de partida
para o versionamento.

**Banco já existente:** não rode ``upgrade`` direto. Marque a revisão como
aplicada e siga para a próxima:

    alembic stamp 0001
    alembic upgrade head

Revision ID: 0001
Revises:
Create Date: 2026-11-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.Integer()),
        sa.Column("perfil", sa.String(12)),
        sa.Column("primeiroNome", sa.String(50)),
        sa.Column("ultimoNome", sa.String(50)),
        sa.Column("usuarioNome", sa.String(50)),
        sa.Column("CPF", sa.String(14)),
        sa.Column("foto", sa.String(1000)),
        sa.Column("email", sa.String(50)),
        sa.Column("telefone", sa.String(11)),
        sa.Column("status", sa.String(8)),
    )

    op.create_table(
        "veiculos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id")),
        sa.Column("tipo", sa.String(20)),
        sa.Column("placa", sa.String(7)),
        sa.Column("renavam", sa.String(11)),
        sa.Column("fabricante", sa.String(50)),
        sa.Column("modelo", sa.String(50)),
        sa.Column("anoModelo", sa.String(4)),
        sa.Column("anoFabricacao", sa.String(4)),
        sa.Column("cor", sa.String(20)),
        sa.Column("status", sa.String(8)),
    )

    op.create_table(
        "servicos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("descricao", sa.String(50)),
        sa.Column("status", sa.String(8)),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id")),
    )

    op.create_table(
        "produtos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("descricao", sa.String(50)),
        sa.Column("status", sa.String(8)),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id")),
    )

    op.create_table(
        "usuarioparametros",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id")),
        sa.Column("receberNotificacoes", sa.Boolean()),
        sa.Column("diasNotificacao", sa.Integer()),
    )

    op.create_table(
        "veiculodica",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("veiculo_id", sa.Integer(), sa.ForeignKey("veiculos.id")),
        sa.Column("texto", sa.Text()),
        sa.Column("datacriacao", sa.Date()),
    )

    op.create_table(
        "veiculodiagnosticos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("veiculo_id", sa.Integer(), sa.ForeignKey("veiculos.id")),
        sa.Column("problema", sa.Text()),
        sa.Column("diagnostico", sa.Text()),
        sa.Column("datacriacao", sa.Date()),
        sa.Column("resolvido", sa.Boolean()),
        sa.Column("util", sa.Boolean()),
    )

    op.create_table(
        "manutencoes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("data", sa.Date()),
        sa.Column("veiculo_id", sa.Integer(), sa.ForeignKey("veiculos.id")),
        sa.Column("km", sa.Integer()),
        sa.Column("observacao", sa.String(100)),
        sa.Column("status", sa.String(10)),
        sa.Column("custo", sa.Float()),
        sa.Column("imagem", sa.Text()),
        sa.Column("imagemNotaServico", sa.Text()),
    )

    op.create_table(
        "manutencaoservicos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("manutencao_id", sa.Integer(), sa.ForeignKey("manutencoes.id")),
        sa.Column("servico_id", sa.Integer(), sa.ForeignKey("servicos.id")),
    )

    op.create_table(
        "manutencaoprodutos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("manutencao_id", sa.Integer(), sa.ForeignKey("manutencoes.id")),
        sa.Column("produto_id", sa.Integer(), sa.ForeignKey("produtos.id")),
    )

    op.create_table(
        "servicoprodutos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("servico_id", sa.Integer(), sa.ForeignKey("servicos.id")),
        sa.Column("produto_id", sa.Integer(), sa.ForeignKey("produtos.id")),
    )

    op.create_table(
        "notificacoes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataNotificacao", sa.Date()),
        sa.Column("tipoNotificacao", sa.String(20)),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id")),
        sa.Column("servico_id", sa.Integer(), sa.ForeignKey("servicos.id")),
        sa.Column("manutencao_id", sa.Integer(), sa.ForeignKey("manutencoes.id")),
        sa.Column("veiculo_id", sa.Integer(), sa.ForeignKey("veiculos.id")),
        sa.Column("titulo", sa.String(100)),
        sa.Column("conteudo", sa.Text()),
        sa.Column("status", sa.String(8)),
    )


def downgrade() -> None:
    for tabela in (
        "notificacoes",
        "servicoprodutos",
        "manutencaoprodutos",
        "manutencaoservicos",
        "manutencoes",
        "veiculodiagnosticos",
        "veiculodica",
        "usuarioparametros",
        "produtos",
        "servicos",
        "veiculos",
        "usuarios",
    ):
        op.drop_table(tabela)
