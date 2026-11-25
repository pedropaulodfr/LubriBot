"""Consultas de manutenção.

Correção: as consultas usavam ``join(ManutencaoServico)``, um inner join que
**escondia** manutenções sem serviço vinculado (dado legado ou registro
incompleto). Agora o filtro é direto na manutenção, preservando o ordenamento por
data do comportamento original.
"""

from __future__ import annotations

from lubribot.models import Manutencao, Veiculo
from repository.models import _Session


def get_manutencoes_by_usuario(usuario_id: int) -> list[Manutencao]:
    session = _Session()
    try:
        return (
            session.query(Manutencao)
            .join(Veiculo, Veiculo.id == Manutencao.veiculo_id)
            .filter(Veiculo.usuario_id == usuario_id)
            .order_by(Manutencao.data)
            .all()
        )
    finally:
        session.close()


def get_manutencoes_by_veiculos(veiculo_id: int) -> list[Manutencao]:
    session = _Session()
    try:
        return (
            session.query(Manutencao)
            .filter(Manutencao.veiculo_id == veiculo_id)
            .order_by(Manutencao.data)
            .all()
        )
    finally:
        session.close()
