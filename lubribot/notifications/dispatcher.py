"""Despachante: entrega notificações pendentes com retentativa controlada.

Garantias:
- A notificação só vira ``Enviada`` **depois** do envio bem-sucedido.
- Falha temporária incrementa tentativas e agenda nova tentativa com backoff.
- Depois de ``max_tentativas``, vira ``Falha`` (não desaparece: fica auditável).
- Usuário que desativou notificações tem a pendência ``Cancelada``.
- Nada de ``except:`` silencioso: toda falha é logada com a chave da notificação.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from lubribot.domain.notifications import NotificationStatus, RetryPolicy
from lubribot.notifications.models import DispatchResult
from lubribot.notifications.ports import NotificationRepositoryPort, SenderPort
from lubribot.utils.logging import get_logger

logger = get_logger(__name__)


def _agora_utc() -> datetime:
    return datetime.now(UTC)


class NotificationDispatcher:
    """Envia as notificações pendentes e registra o resultado de cada tentativa."""

    def __init__(
        self,
        repo: NotificationRepositoryPort,
        sender: SenderPort,
        *,
        retry_policy: RetryPolicy,
        agora_factory: Callable[[], datetime] = _agora_utc,
    ) -> None:
        self._repo = repo
        self._sender = sender
        self._retry = retry_policy
        self._agora = agora_factory

    def despachar(self) -> DispatchResult:
        resultado = DispatchResult()
        agora = self._agora()

        try:
            pendentes = self._repo.listar_pendentes(agora)
        except Exception:
            logger.exception("notificacoes_falha_ao_listar_pendentes")
            resultado.falhas_temporarias += 1
            return resultado

        resultado.pendentes = len(pendentes)

        for notificacao in pendentes:
            try:
                self._processar(notificacao, agora, resultado)
            except Exception:
                resultado.falhas_temporarias += 1
                logger.exception(
                    "notificacao_falha_inesperada",
                    extra={"notificacao_id": notificacao.id},
                )

        logger.info("notificacoes_despacho_concluido", extra={"resumo": resultado.texto()})
        return resultado

    # ------------------------------------------------------------------ interno
    def _processar(self, notificacao, agora: datetime, resultado: DispatchResult) -> None:
        chat_id = notificacao.telegram_id
        if chat_id is None:
            self._repo.marcar_falha_definitiva(
                notificacao.id,
                erro="usuário sem telegram_id",
                agora=agora,
            )
            resultado.falhas_definitivas += 1
            logger.warning(
                "notificacao_sem_destinatario",
                extra={"notificacao_id": notificacao.id},
            )
            return

        if notificacao.receber_notificacoes is False:
            self._repo.cancelar(
                notificacao.id,
                motivo="usuário desativou notificações",
                agora=agora,
            )
            resultado.canceladas += 1
            logger.info(
                "notificacao_cancelada", extra={"notificacao_id": notificacao.id}
            )
            return

        envio = self._sender.enviar(chat_id, notificacao.conteudo or "")

        if envio.ok:
            self._repo.marcar_enviada(notificacao.id, agora)
            resultado.enviadas += 1
            logger.info(
                "notificacao_enviada",
                extra={
                    "notificacao_id": notificacao.id,
                    "tentativas": notificacao.tentativas + 1,
                },
            )
            return

        erro = (envio.erro or "erro desconhecido")[:500]
        tentativas = notificacao.tentativas + 1

        if envio.permanente:
            self._repo.marcar_falha_definitiva(notificacao.id, erro=erro, agora=agora)
            resultado.falhas_definitivas += 1
            logger.error(
                "notificacao_falha_definitiva",
                extra={"notificacao_id": notificacao.id, "erro": erro},
            )
            return

        if self._retry.esgotou(tentativas):
            self._repo.marcar_falha_definitiva(
                notificacao.id,
                erro=f"tentativas esgotadas ({tentativas}): {erro}",
                agora=agora,
            )
            resultado.falhas_definitivas += 1
            logger.error(
                "notificacao_tentativas_esgotadas",
                extra={
                    "notificacao_id": notificacao.id,
                    "tentativas": tentativas,
                },
            )
            return

        atraso = envio.retry_after or self._retry.atraso(tentativas)
        proxima = agora + timedelta(seconds=atraso)
        self._repo.registrar_falha_temporaria(
            notificacao.id,
            tentativas=tentativas,
            proxima_tentativa_em=proxima,
            erro=erro,
            agora=agora,
        )
        resultado.reagendadas += 1
        resultado.falhas_temporarias += 1
        logger.warning(
            "notificacao_reagendada",
            extra={
                "notificacao_id": notificacao.id,
                "tentativas": tentativas,
                "atraso_segundos": atraso,
                "status_esperado": NotificationStatus.PENDENTE,
            },
        )
