"""Diagnóstico do banco (somente leitura, sem expor credenciais).

Uso::

    python scripts/db_status.py                  # usa STRING_CONNECTION
    python scripts/db_status.py STRING_CONNECTION_LOCAL

Mostra apenas host/porta/banco (nunca usuário/senha), a revisão do Alembic e o
estado das tabelas/colunas que a modernização toca.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

RAIZ = Path(__file__).resolve().parents[1]
load_dotenv(RAIZ / ".env")


def _resumir_url(url_texto: str) -> str:
    url = make_url(url_texto)
    return f"{url.drivername}://{url.host}:{url.port}/{url.database}"


def _conectar(nome_variavel: str):
    dsn = os.getenv(nome_variavel)
    if not dsn:
        print(f"[!] {nome_variavel} não configurada no .env")
        return None
    print(f"variável : {nome_variavel}")
    print(f"destino  : {_resumir_url(dsn)}")
    engine = create_engine(dsn, pool_pre_ping=True, connect_args={"connect_timeout": 10})
    with engine.connect() as conexao:
        conexao.execute(text("SELECT 1"))
    return engine


def main() -> int:
    nome_variavel = sys.argv[1] if len(sys.argv) > 1 else "STRING_CONNECTION"
    engine = _conectar(nome_variavel)
    if engine is None:
        return 2

    inspetor = inspect(engine)
    tabelas = sorted(inspetor.get_table_names())
    print(f"tabelas  : {len(tabelas)}")

    with engine.connect() as conexao:
        revisao = None
        if "alembic_version" in tabelas:
            revisao = conexao.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar()
        print(f"alembic  : {revisao or 'SEM alembic_version (schema legado)'}")

        if "notificacoes" in tabelas:
            colunas = {c["name"] for c in inspetor.get_columns("notificacoes")}
            esperadas = {
                "chave",
                "tentativas",
                "criadaEm",
                "proximaTentativaEm",
                "enviadaEm",
                "ultimoErro",
            }
            faltando = esperadas - colunas
            print(f"outbox   : {'completo' if not faltando else 'faltando ' + ', '.join(sorted(faltando))}")
            tipo_status = conexao.execute(
                text(
                    "SELECT character_maximum_length FROM information_schema.columns "
                    "WHERE table_name = 'notificacoes' AND column_name = 'status'"
                )
            ).scalar()
            print(f"status   : varchar({tipo_status})")

        if "servicos" in tabelas:
            colunas_servico = {c["name"] for c in inspetor.get_columns("servicos")}
            print(f"intervalo: {'OK' if 'intervaloDias' in colunas_servico else 'AUSENTE'}")

        indices = [i["name"] for i in inspetor.get_indexes("notificacoes")] if "notificacoes" in tabelas else []
        print(f"índices  : {len(indices)} em notificacoes")

        contagens = {}
        for tabela in ("usuarios", "veiculos", "manutencoes", "notificacoes", "servicos"):
            if tabela in tabelas:
                contagens[tabela] = conexao.execute(
                    text(f'SELECT count(*) FROM "{tabela}"')
                ).scalar()
        print(f"registros: {contagens}")

    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
