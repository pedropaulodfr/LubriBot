"""Consultas de veículo.

Correção: ``add_veiculo`` usava parâmetros ``marca``/``ano`` que não existem no
modelo (``fabricante``/``anoModelo``/``anoFabricacao``), então explodiria se
fosse chamado. Agora a assinatura reflete o schema real e a gravação é atômica.
"""

from __future__ import annotations

from lubribot.models import Veiculo
from repository.models import _Session


def get_veiculos_by_usuario(usuario_id: int) -> list[Veiculo]:
    session = _Session()
    try:
        return (
            session.query(Veiculo)
            .filter(Veiculo.usuario_id == usuario_id, Veiculo.status == "Ativo")
            .all()
        )
    finally:
        session.close()


def get_veiculos_by_telegram_id(telegram_id: int) -> list[Veiculo]:
    session = _Session()
    try:
        return (
            session.query(Veiculo)
            .filter(
                Veiculo.usuario.has(telegram_id=telegram_id),
                Veiculo.status == "Ativo",
            )
            .all()
        )
    finally:
        session.close()


def get_veiculo_by_placa(placa: str, usuario_id: int | None = None) -> Veiculo | None:
    """Busca por placa; quando ``usuario_id`` é informado, exige o dono."""
    session = _Session()
    try:
        query = session.query(Veiculo).filter(
            Veiculo.placa == placa.replace("-", "").upper(),
            Veiculo.status == "Ativo",
        )
        if usuario_id is not None:
            query = query.filter(Veiculo.usuario_id == usuario_id)
        return query.first()
    finally:
        session.close()


def add_veiculo(
    usuario_id: int,
    placa: str,
    *,
    tipo: str | None = None,
    fabricante: str | None = None,
    modelo: str | None = None,
    cor: str | None = None,
    ano_modelo: str | None = None,
    ano_fabricacao: str | None = None,
    renavam: str | None = None,
) -> Veiculo:
    """Cria um veículo ativo para o usuário."""
    from lubribot.database.runtime import get_database

    with get_database().unit_of_work() as session:
        veiculo = Veiculo(
            usuario_id=usuario_id,
            placa=placa.replace("-", "").upper(),
            tipo=tipo,
            fabricante=fabricante,
            modelo=modelo,
            cor=cor,
            anoModelo=ano_modelo,
            anoFabricacao=ano_fabricacao,
            renavam=renavam,
            status="Ativo",
        )
        session.add(veiculo)
        session.flush()
        return veiculo
