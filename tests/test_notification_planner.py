"""Testes do planejador de notificações."""

from __future__ import annotations

from datetime import date, timedelta

from lubribot.domain.maintenance import INTERVALO_PADRAO_DIAS
from lubribot.notifications.planner import NotificationPlanner
from tests.fakes import FakeNotificationRepository, candidato

HOJE = date(2026, 6, 1)


def _planner(repo, *, padrao: int = INTERVALO_PADRAO_DIAS) -> NotificationPlanner:
    return NotificationPlanner(repo, intervalo_padrao_dias=padrao, hoje_factory=lambda: HOJE)


class TestCriacao:
    def test_cria_quando_na_janela(self):
        repo = FakeNotificationRepository(
            candidatos=[
                candidato(ultima_data=HOJE - timedelta(days=180), intervalos_dias=(180,))
            ]
        )
        resultado = _planner(repo).planejar()

        assert resultado.criadas == 1
        assert resultado.avaliados == 1
        assert len(repo.criadas) == 1
        dados = repo.criadas[0]
        assert dados.chave == "ProximaManutencao:100"
        assert dados.usuario_id == 10
        assert dados.veiculo_id == 1
        assert dados.manutencao_id == 100
        assert "01/06/2026" in dados.conteudo

    def test_usa_maior_intervalo_dos_servicos(self):
        # Última manutenção há 100 dias; serviços de 90 e 100 dias.
        # O maior intervalo (100) coloca o vencimento exatamente hoje.
        repo = FakeNotificationRepository(
            candidatos=[
                candidato(ultima_data=HOJE - timedelta(days=100), intervalos_dias=(90, 100))
            ]
        )
        resultado = _planner(repo).planejar()
        assert resultado.criadas == 1
        assert repo.criadas[0].chave == "ProximaManutencao:100"

    def test_intervalo_padrao_quando_servico_sem_intervalo(self):
        # 180 dias desde a última manutenção, sem intervalo no serviço.
        repo = FakeNotificationRepository(
            candidatos=[
                candidato(ultima_data=HOJE - timedelta(days=180), intervalos_dias=(None,))
            ]
        )
        resultado = _planner(repo, padrao=180).planejar()
        assert resultado.criadas == 1


class TestNaoCriacao:
    def test_fora_da_janela_nao_cria(self):
        repo = FakeNotificationRepository(
            candidatos=[
                candidato(ultima_data=HOJE - timedelta(days=10), intervalos_dias=(180,))
            ]
        )
        resultado = _planner(repo).planejar()
        assert resultado.criadas == 0
        assert resultado.fora_da_janela == 1

    def test_manutencao_vencida_ha_muito_tempo_nao_cria(self):
        repo = FakeNotificationRepository(
            candidatos=[
                candidato(ultima_data=HOJE - timedelta(days=400), intervalos_dias=(180,))
            ]
        )
        resultado = _planner(repo).planejar()
        assert resultado.criadas == 0
        assert resultado.fora_da_janela == 1

    def test_usuario_com_notificacao_desativada_nao_cria(self):
        repo = FakeNotificationRepository(
            candidatos=[
                candidato(
                    ultima_data=HOJE - timedelta(days=180),
                    intervalos_dias=(180,),
                    receber_notificacoes=False,
                )
            ]
        )
        resultado = _planner(repo).planejar()
        assert resultado.criadas == 0
        assert resultado.sem_confirmacao == 1

    def test_duplicata_nao_e_criada_de_novo(self):
        repo = FakeNotificationRepository(
            candidatos=[
                candidato(ultima_data=HOJE - timedelta(days=180), intervalos_dias=(180,))
            ],
            chaves_existentes={"ProximaManutencao:100"},
        )
        resultado = _planner(repo).planejar()
        assert resultado.criadas == 0
        assert resultado.ja_existentes == 1


class TestToleranciaAFalhas:
    def test_falha_em_um_veiculo_nao_derruba_o_ciclo(self):
        class RepoComFalha(FakeNotificationRepository):
            def criar_se_nao_existir(self, dados):
                if dados.veiculo_id == 1:
                    raise RuntimeError("falha simulada")
                return super().criar_se_nao_existir(dados)

        repo = RepoComFalha(
            candidatos=[
                candidato(
                    veiculo_id=1,
                    ultima_manutencao_id=100,
                    ultima_data=HOJE - timedelta(days=180),
                ),
                candidato(
                    veiculo_id=2,
                    ultima_manutencao_id=200,
                    ultima_data=HOJE - timedelta(days=180),
                ),
            ]
        )
        resultado = _planner(repo).planejar()

        assert resultado.erros == 1
        assert resultado.criadas == 1
        assert repo.criadas[0].veiculo_id == 2

    def test_falha_ao_listar_candidatos_retorna_resultado_vazio(self):
        class RepoQuebrado(FakeNotificationRepository):
            def listar_candidatos(self):
                raise RuntimeError("banco fora")

        resultado = _planner(RepoQuebrado()).planejar()
        assert resultado.avaliados == 0
        assert resultado.erros == 1
