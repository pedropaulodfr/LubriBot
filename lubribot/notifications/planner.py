"""Planejador: decide quais notificações devem existir e as cria de forma idempotente."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from lubribot.domain.maintenance import (
    TIPO_PROXIMA_MANUTENCAO,
    TITULO_PROXIMA_MANUTENCAO,
    calcular_agendamento,
    chave_notificacao,
    esta_na_janela,
    montar_conteudo_notificacao,
)
from lubribot.domain.notifications import NotificationStatus
from lubribot.notifications.models import (
    DadosNotificacao,
    PlanningResult,
)
from lubribot.notifications.ports import NotificationRepositoryPort
from lubribot.utils.logging import get_logger

logger = get_logger(__name__)


class NotificationPlanner:
    """Percorre os veículos ativos e garante a notificação da próxima manutenção."""

    def __init__(
        self,
        repo: NotificationRepositoryPort,
        *,
        intervalo_padrao_dias: int,
        hoje_factory: Callable[[], date] = date.today,
    ) -> None:
        self._repo = repo
        self._intervalo_padrao = intervalo_padrao_dias
        self._hoje = hoje_factory

    def planejar(self) -> PlanningResult:
        resultado = PlanningResult()
        hoje = self._hoje()

        try:
            candidatos = self._repo.listar_candidatos()
        except Exception:
            logger.exception("notificacoes_falha_ao_listar_candidatos")
            resultado.erros += 1
            return resultado

        for candidato in candidatos:
            resultado.avaliados += 1
            try:
                self._avaliar(candidato, hoje, resultado)
            except Exception:
                # Um veículo com dado inconsistente não pode derrubar o ciclo.
                resultado.erros += 1
                logger.exception(
                    "notificacoes_falha_ao_avaliar_veiculo",
                    extra={"veiculo_id": candidato.veiculo_id},
                )

        logger.info("notificacoes_planejamento_concluido", extra={"resumo": resultado.texto()})
        return resultado

    # ------------------------------------------------------------------ interno
    def _avaliar(self, candidato, hoje: date, resultado: PlanningResult) -> None:
        # Sem parâmetro, o padrão do produto é receber notificações.
        receber = candidato.receber_notificacoes
        if receber is False:
            resultado.sem_confirmacao += 1
            return

        agendamento = calcular_agendamento(
            ultima_manutencao_id=candidato.ultima_manutencao_id,
            ultima_data=candidato.ultima_data,
            intervalos=list(candidato.intervalos_dias),
            padrao=self._intervalo_padrao,
        )

        if not esta_na_janela(agendamento.proxima_data, hoje, candidato.dias_notificacao):
            resultado.fora_da_janela += 1
            return

        chave = chave_notificacao(agendamento.ultima_manutencao_id)
        dados = DadosNotificacao(
            chave=chave,
            tipo=TIPO_PROXIMA_MANUTENCAO,
            titulo=TITULO_PROXIMA_MANUTENCAO,
            conteudo=montar_conteudo_notificacao(
                candidato.nome_usuario,
                candidato.descricao,
                agendamento.proxima_data,
            ),
            usuario_id=candidato.usuario_id,
            veiculo_id=candidato.veiculo_id,
            manutencao_id=agendamento.ultima_manutencao_id,
            data_notificacao=hoje,
        )

        if self._repo.criar_se_nao_existir(dados):
            resultado.criadas += 1
            logger.info(
                "notificacao_criada",
                extra={
                    "chave": chave,
                    "veiculo_id": candidato.veiculo_id,
                    "proxima_data": agendamento.proxima_data.isoformat(),
                    "status": NotificationStatus.PENDENTE,
                },
            )
        else:
            resultado.ja_existentes += 1
