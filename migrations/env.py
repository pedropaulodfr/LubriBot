"""Ambiente do Alembic.

A URL do banco vem da mesma configuração da aplicação (``Settings``), nunca de um
valor fixo no repositório. Para rodar offline (gerar SQL sem conectar), use::

    alembic upgrade head --sql
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from lubribot.models import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _url_do_banco() -> str:
    """Prioriza ALEMBIC_DATABASE_URL; senão usa a configuração da aplicação."""
    explicita = os.getenv("ALEMBIC_DATABASE_URL")
    if explicita:
        return explicita
    from lubribot.config.settings import get_settings

    return get_settings().database_url


def run_migrations_offline() -> None:
    """Emite o SQL sem abrir conexão."""
    url = config.get_main_option("sqlalchemy.url") or _url_do_banco()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa as migrações numa conexão real."""
    secao = config.get_section(config.config_ini_section) or {}
    url = config.get_main_option("sqlalchemy.url") or _url_do_banco()
    secao["sqlalchemy.url"] = url.replace("%", "%%")

    connectable = engine_from_config(
        secao,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
