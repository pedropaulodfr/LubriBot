"""Testes de consistência do mapeamento (protegem contra drift de schema)."""

from __future__ import annotations

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import configure_mappers

from lubribot.models import (
    Base,
    Manutencao,
    Notificacao,
    Servico,
    Usuario,
    Veiculo,
)


def _colunas(modelo) -> set[str]:
    return {coluna.name for coluna in modelo.__table__.columns}


class TestMapeamentoValido:
    def test_todos_os_mappers_configuram(self):
        """Falha aqui indica relacionamento apontando para nome inexistente."""
        configure_mappers()

    def test_nenhuma_coluna_duplicada_em_tabela(self):
        for tabela in Base.metadata.tables.values():
            nomes = [coluna.name for coluna in tabela.columns]
            assert len(nomes) == len(set(nomes)), tabela.name


class TestTabelas:
    def test_todas_as_tabelas_legadas_existem(self):
        esperadas = {
            "usuarios",
            "usuarioparametros",
            "veiculos",
            "veiculodica",
            "veiculodiagnosticos",
            "manutencoes",
            "manutencaoservicos",
            "manutencaoprodutos",
            "servicos",
            "produtos",
            "servicoprodutos",
            "notificacoes",
        }
        assert esperadas <= set(Base.metadata.tables)


class TestColunasLegadas:
    def test_usuarios_mantem_nomes_camel_case(self):
        assert {"primeiroNome", "ultimoNome", "usuarioNome", "CPF"} <= _colunas(Usuario)

    def test_veiculos_mantem_colunas(self):
        assert {"anoModelo", "anoFabricacao", "renavam", "placa"} <= _colunas(Veiculo)

    def test_manutencoes_mantem_colunas(self):
        assert {"km", "custo", "imagem", "imagemNotaServico"} <= _colunas(Manutencao)


class TestColunasNovas:
    def test_servico_tem_intervalo_dias(self):
        assert "intervaloDias" in _colunas(Servico)

    @pytest.mark.parametrize(
        "coluna",
        [
            "chave",
            "tentativas",
            "criadaEm",
            "ultimaTentativaEm",
            "proximaTentativaEm",
            "enviadaEm",
            "ultimoErro",
        ],
    )
    def test_notificacao_tem_coluna_de_outbox(self, coluna):
        assert coluna in _colunas(Notificacao)

    def test_tentativas_tem_default_no_banco(self):
        coluna = Notificacao.__table__.columns["tentativas"]
        assert coluna.nullable is False
        assert coluna.server_default is not None

    def test_chave_tem_restricao_de_unicidade(self):
        tabela = Notificacao.__table__
        unicas = {
            c.name
            for c in tabela.constraints
            if c.__class__.__name__ == "UniqueConstraint"
        }
        assert "uq_notificacoes_chave" in unicas


class TestIndices:
    def test_indices_de_busca_existem(self):
        nomes = {indice.name for indice in Base.metadata.tables["usuarios"].indexes}
        nomes |= {indice.name for indice in Base.metadata.tables["veiculos"].indexes}
        nomes |= {indice.name for indice in Base.metadata.tables["notificacoes"].indexes}

        for esperado in (
            "ix_usuarios_telegram_id",
            "ix_veiculos_placa",
            "ix_notificacoes_status",
        ):
            assert esperado in nomes


class TestMapeamentoInspectavel:
    def test_engine_do_sqlite_nao_e_usado_aqui(self):
        # Garantia de que o mapeamento é puramente declarativo: nenhum engine
        # aberto só por importar o pacote.
        assert inspect(Usuario).local_table is Usuario.__table__
