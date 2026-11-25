"""Localiza connection strings nos arquivos do projeto, sem expor credenciais.

Uso::

    python scripts/find_dsn.py            # lista candidatos mascarados
    python scripts/find_dsn.py --testar   # tenta conectar em cada candidato

Mostra apenas host, porta, banco e o formato do usuário (parte antes do ponto).
Nunca imprime senha nem a URL completa.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

RAIZ = Path(__file__).resolve().parents[1]
PADRAO = re.compile(r"postgres(?:ql)?://[^\s\"'<>]+")

ARQUIVOS = [
    ".env",
    "migration_data.sql",
    "migration.log",
    "DOCUMENTACAO.md",
    "Implementations/ImplementationPlan_DeployRailway_08062026.md",
]


def _descrever(origem: str, dsn: str) -> dict | None:
    try:
        url = make_url(dsn)
    except Exception:
        print(f"{origem:45} URL inválida")
        return None
    usuario = (url.username or "").split(".")[0]
    print(
        f"{origem:45} host={url.host} porta={url.port} banco={url.database} "
        f"usuario={usuario or '-'}"
    )
    return {"origem": origem, "dsn": dsn, "host": url.host, "porta": url.port}


def main() -> int:
    testar = "--testar" in sys.argv
    candidatos: list[dict] = []

    print("=== .env ===")
    for chave, valor in dotenv_values(RAIZ / ".env").items():
        if not valor:
            continue
        for dsn in PADRAO.findall(valor):
            item = _descrever(chave, dsn)
            if item:
                item["variavel"] = chave
                candidatos.append(item)

    print("\n=== outros arquivos (primeira ocorrência) ===")
    for arquivo in ARQUIVOS[1:]:
        caminho = RAIZ / arquivo
        if not caminho.exists():
            continue
        texto = caminho.read_text(encoding="utf-8", errors="replace")
        achados = PADRAO.findall(texto)
        if achados:
            _descrever(arquivo, achados[0])

    if not testar:
        print("\n(dica: use --testar para verificar quais conectam)")
        return 0

    print("\n=== teste de conexão (10s) ===")
    for item in candidatos:
        rotulo = item.get("variavel", item["origem"])
        try:
            engine = create_engine(
                item["dsn"], connect_args={"connect_timeout": 10}
            )
            with engine.connect() as conexao:
                banco = conexao.execute(text("select current_database()")).scalar()
            engine.dispose()
            print(f"{rotulo:24} OK conectou (banco={banco})")
        except Exception as exc:
            mensagem = repr(getattr(exc, "orig", exc))
            mensagem = mensagem.replace("\\n", " ")[:180]
            print(f"{rotulo:24} FALHOU: {mensagem}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
