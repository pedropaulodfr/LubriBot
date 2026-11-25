"""Aplica as migrações do LubriBot de forma segura e idempotente.

Uso::

    python scripts/apply_migrations.py                       # STRING_CONNECTION
    python scripts/apply_migrations.py STRING_CONNECTION_LOCAL
    LUBRIBOT_TEST_DATABASE_URL=... python scripts/apply_migrations.py LUBRIBOT_TEST_DATABASE_URL

O que faz:
1. conecta e confere o estado do schema;
2. se o banco já tem as tabelas legadas mas não tem `alembic_version`, marca a
   revisão `0001` (baseline) — **sem recriar tabelas**;
3. se o banco está vazio, aplica tudo do zero;
4. roda `alembic upgrade head`;
5. verifica o resultado (revisão, colunas do outbox, tamanho de status).

Nunca apaga dados. Não imprime credenciais.
"""

from __future__ import annotations

import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

RAIZ = Path(__file__).resolve().parents[1]
load_dotenv(RAIZ / ".env")

TABELAS_LEGADAS = {"usuarios", "veiculos", "manutencoes", "notificacoes"}


def _mascarar(dsn: str) -> str:
    from sqlalchemy.engine import make_url

    url = make_url(dsn)
    return f"{url.drivername}://{url.host}:{url.port}/{url.database}"


def _verificar(engine) -> bool:
    inspetor = inspect(engine)
    tabelas = set(inspetor.get_table_names())
    with engine.connect() as conexao:
        revisao = None
        if "alembic_version" in tabelas:
            revisao = conexao.execute(text("SELECT version_num FROM alembic_version")).scalar()
        colunas = {c["name"] for c in inspetor.get_columns("notificacoes")} if "notificacoes" in tabelas else set()
        outbox = {"chave", "tentativas", "proximaTentativaEm", "enviadaEm"}
        tamanho_status = conexao.execute(
            text(
                "SELECT character_maximum_length FROM information_schema.columns "
                "WHERE table_name = 'notificacoes' AND column_name = 'status'"
            )
        ).scalar()

    print(f"revisão   : {revisao}")
    print(f"outbox    : {'completo' if outbox <= colunas else 'INCOMPLETO ' + str(sorted(outbox - colunas))}")
    print(f"status    : varchar({tamanho_status})")
    ok = revisao == "0002" and outbox <= colunas and tamanho_status and tamanho_status >= 20
    return bool(ok)


def main() -> int:
    nome_variavel = sys.argv[1] if len(sys.argv) > 1 else "STRING_CONNECTION"
    import os

    dsn = os.getenv(nome_variavel)
    if not dsn:
        print(f"[!] variável {nome_variavel} não configurada")
        return 2

    print(f"destino   : {_mascarar(dsn)}")
    engine = create_engine(dsn, pool_pre_ping=True, connect_args={"connect_timeout": 15})
    try:
        with engine.connect() as conexao:
            conexao.execute(text("SELECT 1"))
    except Exception as exc:
        print(f"[!] falha ao conectar: {str(getattr(exc, 'orig', exc))[:300]}")
        return 3

    inspetor = inspect(engine)
    tabelas = set(inspetor.get_table_names())
    config = Config(str(RAIZ / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", dsn.replace("%", "%%"))

    if "alembic_version" not in tabelas:
        if tabelas >= TABELAS_LEGADAS:
            print("[i] schema legado detectado sem alembic_version -> stamp 0001")
            command.stamp(config, "0001")
        else:
            print("[i] banco sem tabelas do LubriBot -> aplicando do zero")
    else:
        print("[i] alembic_version presente -> seguindo para upgrade")

    print("[i] alembic upgrade head")
    command.upgrade(config, "head")

    print("[i] verificando resultado")
    ok = _verificar(engine)
    engine.dispose()
    if ok:
        print("[OK] migrações aplicadas e schema verificado")
        return 0
    print("[!] schema não ficou no estado esperado — não siga para produção")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
