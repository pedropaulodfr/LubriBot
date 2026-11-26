"""Testes de integração com PostgreSQL real (dedicado, nunca produção).

Só roda quando `LUBRIBOT_TEST_DATABASE_URL` está definida. Para executar sem ter
um Postgres instalado, use::

    python scripts/validate_with_embedded_pg.py

O script sobe um PostgreSQL embarcado (pacote `pgserver`), aponta a variável e
roda esta suíte.
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from lubribot.database.engine import Database
from lubribot.domain.notifications import RetryPolicy
from lubribot.models import (
    Manutencao,
    ManutencaoServico,
    Notificacao,
    Servico,
    Usuario,
    UsuarioParametro,
    Veiculo,
)
from lubribot.notifications.dispatcher import NotificationDispatcher
from lubribot.notifications.planner import NotificationPlanner
from lubribot.notifications.ports import SendOutcome
from lubribot.repositories.notification_repository import (
    SQLAlchemyNotificationRepository,
)

RAIZ = Path(__file__).resolve().parents[2]


def _url() -> str:
    url = os.getenv("LUBRIBOT_TEST_DATABASE_URL")
    if not url:
        pytest.skip("LUBRIBOT_TEST_DATABASE_URL não definida")
    return url


@pytest.fixture(scope="session")
def engine():
    url = _url()
    config = Config(str(RAIZ / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(config, "head")

    eng = create_engine(url, pool_pre_ping=True)
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    """Limpa as tabelas e devolve um Database ligado ao Postgres de teste."""
    with engine.begin() as conexao:
        conexao.execute(
            text(
                "TRUNCATE notificacoes, manutencaoprodutos, manutencaoservicos, "
                "manutencoes, servicoprodutos, produtos, servicos, veiculodica, "
                "veiculodiagnosticos, veiculos, usuarioparametros, usuarios "
                "RESTART IDENTITY CASCADE"
            )
        )
    return Database.from_url(url=_url())


@pytest.fixture()
def cenario(db):
    """Usuário + veículo + manutenção finalizada há 180 dias + serviço de 180d."""
    with db.unit_of_work() as session:
        usuario = Usuario(
            telegram_id=555_000_111,
            perfil="Proprietario",
            primeiroNome="Ana",
            status="Ativo",
        )
        session.add(usuario)
        session.flush()

        session.add(
            UsuarioParametro(
                usuario_id=usuario.id, receberNotificacoes=True, diasNotificacao=7
            )
        )
        veiculo = Veiculo(
            usuario_id=usuario.id,
            tipo="Moto",
            placa="ABC1D23",
            fabricante="Honda",
            modelo="Bros",
            cor="Vermelha",
            anoModelo="2022",
            status="Ativo",
        )
        session.add(veiculo)
        service = Servico(descricao="Troca de Óleo", status="Ativo", intervaloDias=180)
        session.add(service)
        session.flush()

        manutencao = Manutencao(
            data=date.today() - timedelta(days=180),
            veiculo_id=veiculo.id,
            km=10_000,
            status="Finalizada",
            custo=120.0,
        )
        session.add(manutencao)
        session.flush()
        session.add(
            ManutencaoServico(manutencao_id=manutencao.id, servico_id=service.id)
        )

    return {"usuario_id": usuario.id, "veiculo_id": veiculo.id, "manutencao_id": manutencao.id}


class FakeSender:
    def __init__(self, resultados=None):
        self._resultados = list(resultados or [])
        self.chamadas = []

    def enviar(self, chat_id, texto):
        self.chamadas.append((chat_id, texto))
        if self._resultados:
            return self._resultados.pop(0)
        return SendOutcome.sucesso()


class TestSchema:
    def test_migracoes_criam_indices_e_outbox(self, engine):
        inspetor = inspect(engine)
        colunas = {c["name"] for c in inspetor.get_columns("notificacoes")}
        assert {"chave", "tentativas", "proximaTentativaEm", "enviadaEm"} <= colunas

        indices = {i["name"] for i in inspetor.get_indexes("notificacoes")}
        assert "uq_notificacoes_chave" in indices
        assert "ix_notificacoes_status" in indices

        colunas_servico = {c["name"] for c in inspetor.get_columns("servicos")}
        assert "intervaloDias" in colunas_servico

        with engine.connect() as conexao:
            tamanho = conexao.execute(
                text(
                    "SELECT character_maximum_length FROM information_schema.columns "
                    "WHERE table_name = 'notificacoes' AND column_name = 'status'"
                )
            ).scalar()
        assert tamanho == 20

    def test_revisao_aplicada(self, engine):
        with engine.connect() as conexao:
            revisao = conexao.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar()
        assert revisao == "0004"

    def test_colunas_de_km_existem(self, engine):
        inspetor = inspect(engine)
        servicos = {c["name"] for c in inspetor.get_columns("servicos")}
        veiculos = {c["name"] for c in inspetor.get_columns("veiculos")}
        assert "intervaloKm" in servicos
        assert {"kmAtual", "kmAtualizadoEm"} <= veiculos

    def test_tabela_de_conversas_existe(self, engine):
        inspetor = inspect(engine)
        assert "conversas" in inspetor.get_table_names()
        colunas = {c["name"] for c in inspetor.get_columns("conversas")}
        assert {"chat_id", "fluxo", "etapa", "dados"} <= colunas


class TestConversasPersistidas:
    """Rascunho sobrevive a restart: nova instância do registry lê o mesmo estado."""

    def test_rascunho_sobrevive_a_nova_instancia(self, db):
        from dataclasses import dataclass, field

        from lubribot.bot.conversation_store import DraftMixin, SQLConversationRegistry

        @dataclass
        class Rascunho(  # type: ignore[misc]
            DraftMixin
        ):
            __fluxo__ = "teste-integracao"
            usuario_id: int
            km: int | None = None
            produtos: list[int] = field(default_factory=list)

        def fabrica():
            return db

        primeiro = SQLConversationRegistry("teste-integracao", Rascunho, db_factory=fabrica)
        primeiro[999] = Rascunho(usuario_id=1, km=1000)
        rascunho = primeiro.get(999)
        rascunho.km = 45000
        primeiro.definir_etapa(999, "receber_km")

        # Simula restart: novo registry, mesmo banco.
        segundo = SQLConversationRegistry("teste-integracao", Rascunho, db_factory=fabrica)
        carregado = segundo.get(999)
        assert carregado is not None
        assert carregado.km == 45000
        assert segundo.obter_etapa(999) == "receber_km"

        assert segundo.limpar(999) is True
        assert segundo.get(999) is None

    def test_registros_de_fluxos_diferentes_nao_colidem(self, db):
        from lubribot.bot.conversation_store import SQLConversationRegistry

        def fabrica():
            return db

        manutencao = SQLConversationRegistry("manutencao", dict, db_factory=fabrica)
        veiculo = SQLConversationRegistry("veiculo", dict, db_factory=fabrica)

        manutencao[555] = {"km": 10}
        assert veiculo.get(555) is None
        assert manutencao.get(555)["km"] == 10


class TestNotificacaoPorKmIntegracao:
    def test_planner_dispara_por_km_fora_da_janela_de_data(self, db):
        with db.unit_of_work() as session:
            usuario = Usuario(telegram_id=777_000_222, primeiroNome="Bruno", status="Ativo")
            session.add(usuario)
            session.flush()
            session.add(
                UsuarioParametro(usuario_id=usuario.id, receberNotificacoes=True, diasNotificacao=7)
            )
            veiculo = Veiculo(
                usuario_id=usuario.id,
                tipo="Carro",
                placa="XYZ9A11",
                fabricante="Toyota",
                modelo="Yaris",
                status="Ativo",
                kmAtual=11_500,  # já passou do vencimento (10.000 + 1.000)
            )
            session.add(veiculo)
            servico = Servico(
                descricao="Troca de óleo",
                status="Ativo",
                intervaloDias=180,
                intervaloKm=1_000,
            )
            session.add(servico)
            session.flush()
            manutencao = Manutencao(
                data=date.today() - timedelta(days=10),  # longe da janela de data
                veiculo_id=veiculo.id,
                km=10_000,
                status="Finalizada",
            )
            session.add(manutencao)
            session.flush()
            session.add(
                ManutencaoServico(manutencao_id=manutencao.id, servico_id=servico.id)
            )

        with db.unit_of_work() as session:
            plano = NotificationPlanner(
                SQLAlchemyNotificationRepository(session), intervalo_padrao_dias=180
            ).planejar()
        assert plano.criadas == 1

        with db.unit_of_work() as session:
            notificacao = session.query(Notificacao).one()
            assert "km" in (notificacao.conteudo or "").lower()
            assert notificacao.status == "Pendente"


class TestNotificacoesPontaAPonta:
    def test_planeja_envia_e_nao_duplica(self, db, cenario):
        with db.unit_of_work() as session:
            plano = NotificationPlanner(
                SQLAlchemyNotificationRepository(session), intervalo_padrao_dias=180
            ).planejar()
        assert plano.criadas == 1

        # Rodar de novo não cria duplicata (idempotência no banco).
        with db.unit_of_work() as session:
            plano2 = NotificationPlanner(
                SQLAlchemyNotificationRepository(session), intervalo_padrao_dias=180
            ).planejar()
        assert plano2.criadas == 0
        assert plano2.ja_existentes == 1

        sender = FakeSender()
        with db.unit_of_work() as session:
            resultado = NotificationDispatcher(
                SQLAlchemyNotificationRepository(session),
                sender,
                retry_policy=RetryPolicy(max_tentativas=3),
            ).despachar()
        assert resultado.enviadas == 1
        assert sender.chamadas[0][0] == 555_000_111
        assert date.today().strftime("%d/%m/%Y") in sender.chamadas[0][1]

        with db.unit_of_work() as session:
            notificacao = session.query(Notificacao).one()
            assert notificacao.status == "Enviada"
            assert notificacao.enviadaEm is not None
            assert notificacao.chave == f"ProximaManutencao:{cenario['manutencao_id']}"

    def test_falha_temporaria_agenda_retry(self, db, cenario):
        with db.unit_of_work() as session:
            NotificationPlanner(
                SQLAlchemyNotificationRepository(session), intervalo_padrao_dias=180
            ).planejar()

        sender = FakeSender([SendOutcome.transitorio("timeout simulado")])
        with db.unit_of_work() as session:
            resultado = NotificationDispatcher(
                SQLAlchemyNotificationRepository(session),
                sender,
                retry_policy=RetryPolicy(max_tentativas=3, base_segundos=60),
            ).despachar()
        assert resultado.reagendadas == 1

        with db.unit_of_work() as session:
            notificacao = session.query(Notificacao).one()
            assert notificacao.status == "Pendente"
            assert notificacao.tentativas == 1
            assert notificacao.proximaTentativaEm is not None
            assert "timeout" in (notificacao.ultimoErro or "")

        # Enquanto está agendada para o futuro, não é reenviada.
        with db.unit_of_work() as session:
            resultado2 = NotificationDispatcher(
                SQLAlchemyNotificationRepository(session),
                FakeSender(),
                retry_policy=RetryPolicy(max_tentativas=3),
            ).despachar()
        assert resultado2.pendentes == 0

    def test_chave_unica_impede_duplicata_no_banco(self, db, cenario):
        with db.unit_of_work() as session:
            session.add(
                Notificacao(
                    tipoNotificacao="ProximaManutencao",
                    usuario_id=cenario["usuario_id"],
                    veiculo_id=cenario["veiculo_id"],
                    manutencao_id=cenario["manutencao_id"],
                    conteudo="a",
                    status="Pendente",
                    chave=f"ProximaManutencao:{cenario['manutencao_id']}",
                )
            )

        with pytest.raises(IntegrityError):
            with db.unit_of_work() as session:
                session.add(
                    Notificacao(
                        tipoNotificacao="ProximaManutencao",
                        usuario_id=cenario["usuario_id"],
                        veiculo_id=cenario["veiculo_id"],
                        manutencao_id=cenario["manutencao_id"],
                        conteudo="b",
                        status="Pendente",
                        chave=f"ProximaManutencao:{cenario['manutencao_id']}",
                    )
                )
