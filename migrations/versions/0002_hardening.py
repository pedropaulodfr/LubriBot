"""Hardening: índices, colunas do outbox e regra de manutenção versionada.

O que esta revisão faz (tudo idempotente com ``IF NOT EXISTS``, seguro para rodar
em banco que já tem dados):

1. alarga ``notificacoes.status`` de ``varchar(8)`` para ``varchar(20)`` — o
   código gravava ``Cancelada`` (9 caracteres) e estourava no Postgres;
2. cria ``servicos.intervaloDias`` (nullable) — a coluna era citada no código e na
   documentação, mas não existia;
3. adiciona as colunas de controle do outbox em ``notificacoes``
   (``chave``, ``tentativas``, timestamps, ``ultimoErro``);
4. preenche ``chave`` das notificações legadas e desduplica sem apagar registros
   (duplicatas viram ``legacy:<id>``, preservando o histórico);
5. cria os índices que faltavam e o índice único de idempotência.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-24
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_INDICES = (
    ("ix_usuarios_telegram_id", "usuarios", "telegram_id"),
    ("ix_usuarios_status", "usuarios", "status"),
    ("ix_veiculos_usuario_id", "veiculos", "usuario_id"),
    ("ix_veiculos_placa", "veiculos", "placa"),
    ("ix_veiculos_status", "veiculos", "status"),
    ("ix_usuarioparametros_usuario_id", "usuarioparametros", "usuario_id"),
    ("ix_veiculodica_veiculo_id", "veiculodica", "veiculo_id"),
    ("ix_veiculodiagnosticos_veiculo_id", "veiculodiagnosticos", "veiculo_id"),
    ("ix_veiculodiagnosticos_datacriacao", "veiculodiagnosticos", "datacriacao"),
    ("ix_manutencoes_veiculo_id", "manutencoes", "veiculo_id"),
    ("ix_manutencoes_data", "manutencoes", "data"),
    ("ix_manutencoes_status", "manutencoes", "status"),
    ("ix_manutencaoservicos_manutencao_id", "manutencaoservicos", "manutencao_id"),
    ("ix_manutencaoprodutos_manutencao_id", "manutencaoprodutos", "manutencao_id"),
    ("ix_servicos_usuario_id", "servicos", "usuario_id"),
    ("ix_servicos_status", "servicos", "status"),
    ("ix_produtos_usuario_id", "produtos", "usuario_id"),
    ("ix_produtos_status", "produtos", "status"),
    ("ix_notificacoes_status", "notificacoes", "status"),
    ("ix_notificacoes_usuario_id", "notificacoes", "usuario_id"),
    ("ix_notificacoes_manutencao_id", "notificacoes", "manutencao_id"),
)


def upgrade() -> None:
    # 1) status de notificação precisa caber "Cancelada" (9) e "Pendente" (8)
    op.execute("ALTER TABLE notificacoes ALTER COLUMN status TYPE varchar(20)")

    # 2) intervalo de manutenção por serviço
    op.execute("ALTER TABLE servicos ADD COLUMN IF NOT EXISTS \"intervaloDias\" integer")

    # 3) colunas de outbox
    op.execute("ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS chave varchar(120)")
    op.execute(
        "ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS tentativas integer NOT NULL DEFAULT 0"
    )
    op.execute(
        "ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS \"criadaEm\" timestamptz DEFAULT now()"
    )
    op.execute(
        "ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS \"ultimaTentativaEm\" timestamptz"
    )
    op.execute(
        "ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS \"proximaTentativaEm\" timestamptz"
    )
    op.execute(
        "ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS \"enviadaEm\" timestamptz"
    )
    op.execute("ALTER TABLE notificacoes ADD COLUMN IF NOT EXISTS \"ultimoErro\" text")

    # 4) backfill e desduplicação sem perda de registro
    op.execute(
        """
        UPDATE notificacoes
           SET chave = "tipoNotificacao" || ':' || manutencao_id
         WHERE chave IS NULL
           AND manutencao_id IS NOT NULL
           AND "tipoNotificacao" IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE notificacoes AS n
           SET chave = 'legacy:' || n.id
         WHERE n.chave IS NOT NULL
           AND n.id <> (
               SELECT MIN(x.id) FROM notificacoes AS x WHERE x.chave = n.chave
           )
        """
    )

    # 5) índices
    for nome, tabela, coluna in _INDICES:
        op.execute(f'CREATE INDEX IF NOT EXISTS {nome} ON {tabela} ({coluna})')
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_notificacoes_chave ON notificacoes (chave)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_servicoprodutos_par ON servicoprodutos (servico_id, produto_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_notificacoes_chave")
    for nome, _tabela, _coluna in _INDICES:
        op.execute(f"DROP INDEX IF EXISTS {nome}")
    op.execute("DROP INDEX IF EXISTS ix_servicoprodutos_par")

    op.execute("ALTER TABLE notificacoes DROP COLUMN IF EXISTS \"ultimoErro\"")
    op.execute("ALTER TABLE notificacoes DROP COLUMN IF EXISTS \"enviadaEm\"")
    op.execute("ALTER TABLE notificacoes DROP COLUMN IF EXISTS \"proximaTentativaEm\"")
    op.execute("ALTER TABLE notificacoes DROP COLUMN IF EXISTS \"ultimaTentativaEm\"")
    op.execute("ALTER TABLE notificacoes DROP COLUMN IF EXISTS \"criadaEm\"")
    op.execute("ALTER TABLE notificacoes DROP COLUMN IF EXISTS tentativas")
    op.execute("ALTER TABLE notificacoes DROP COLUMN IF EXISTS chave")
    op.execute("ALTER TABLE servicos DROP COLUMN IF EXISTS \"intervaloDias\"")
    # Antes de encolher a coluna, normaliza valores que não caberiam em 8 chars.
    op.execute(
        "UPDATE notificacoes SET status = 'Pendente' WHERE length(status) > 8"
    )
    op.execute("ALTER TABLE notificacoes ALTER COLUMN status TYPE varchar(8)")
