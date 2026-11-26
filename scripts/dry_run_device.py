"""Diagnóstico + dry-run de notificações executado no J4 Core (Termux)."""

from __future__ import annotations

import sys
from datetime import date

sys.path.insert(0, "/data/data/com.termux/files/home/lubribot")

from sqlalchemy import text

from lubribot.config.settings import IMPLEMENTACAO, get_settings
from lubribot.database.runtime import get_database
from lubribot.domain.maintenance import (
    calcular_agendamento,
    calcular_vencimento_km,
    esta_na_janela,
    km_vencido,
    montar_conteudo_notificacao,
)
from lubribot.repositories.notification_repository import (
    SQLAlchemyNotificationRepository,
)


def main() -> int:
    cfg = get_settings()
    print(f"config={IMPLEMENTACAO} ambiente={cfg.ambiente_rotulo}")
    print(f"notificacoes_habilitadas={cfg.notificacoes_habilitadas}")

    db = get_database()
    print(f"driver={db.engine.url.drivername}")
    with db.engine.connect() as conexao:
        total = conexao.execute(text("select count(*) from usuarios")).scalar()
        revisao = conexao.execute(text("select version_num from alembic_version")).scalar()
    print(f"db_ok usuarios={total} migracao={revisao}")

    hoje = date.today()
    with db.unit_of_work(commit=False) as sessao:
        candidatos = SQLAlchemyNotificationRepository(sessao).listar_candidatos()

    print(f"candidatos={len(candidatos)}")
    criaria = 0
    for candidato in candidatos:
        agenda = calcular_agendamento(
            candidato.ultima_manutencao_id,
            candidato.ultima_data,
            list(candidato.intervalos_dias),
            padrao=cfg.intervalo_manutencao_padrao_dias,
        )
        proxima_km = calcular_vencimento_km(
            candidato.ultima_km,
            list(candidato.intervalos_km),
            padrao=cfg.intervalo_km_padrao,
        )
        por_data = esta_na_janela(agenda.proxima_data, hoje, candidato.dias_notificacao)
        por_km = km_vencido(candidato.km_atual, proxima_km)
        dispara = por_data or por_km
        criaria += 1 if dispara else 0
        print(
            f"veiculo={candidato.veiculo_id} proxima_data={agenda.proxima_data}"
            f" por_data={por_data} km_atual={candidato.km_atual} proxima_km={proxima_km}"
            f" por_km={por_km} => {'CRIARIA' if dispara else 'nao'}"
        )
        if dispara:
            mensagem = montar_conteudo_notificacao(
                candidato.nome_usuario,
                candidato.descricao,
                agenda.proxima_data if por_data else None,
                proxima_km=proxima_km if por_km else None,
            )
            print(f"  mensagem: {mensagem}")

    print(f"resumo: criaria {criaria} de {len(candidatos)}")
    db.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
