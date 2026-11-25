"""Job de notificações: um ciclo de planejamento + um ciclo de despacho.

Cada etapa roda em sua própria unidade de trabalho, então uma falha no envio não
desfaz o planejamento já confirmado (e vice-versa).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from lubribot.config.settings import Settings
from lubribot.database.engine import Database
from lubribot.domain.notifications import RetryPolicy
from lubribot.notifications.dispatcher import NotificationDispatcher
from lubribot.notifications.models import DispatchResult, PlanningResult
from lubribot.notifications.planner import NotificationPlanner
from lubribot.repositories.notification_repository import (
    SQLAlchemyNotificationRepository,
)
from lubribot.utils.logging import get_logger

if TYPE_CHECKING:
    from lubribot.notifications.ports import SenderPort

logger = get_logger(__name__)


@dataclass(slots=True)
class CycleResult:
    """Resultado observável de um ciclo completo."""

    planejamento: PlanningResult | None = None
    despacho: DispatchResult | None = None
    erro: str | None = None
    detalhes: list[str] = field(default_factory=list)


class NotificationJob:
    """Orquestra planejamento e envio, cada um em sua transação."""

    def __init__(
        self,
        db: Database,
        sender: SenderPort,
        settings: Settings,
    ) -> None:
        self._db = db
        self._sender = sender
        self._settings = settings
        self._retry = RetryPolicy(
            max_tentativas=settings.notificacoes_max_tentativas,
            base_segundos=settings.notificacoes_backoff_base_segundos,
        )

    def executar_ciclo(self) -> CycleResult:
        resultado = CycleResult()
        try:
            resultado.planejamento = self._planejar()
        except Exception as exc:
            resultado.erro = f"planejamento: {exc}"
            logger.exception("notificacoes_ciclo_planejamento_falhou")
            return resultado

        try:
            resultado.despacho = self._despachar()
        except Exception as exc:
            resultado.erro = f"despacho: {exc}"
            logger.exception("notificacoes_ciclo_despacho_falhou")
            return resultado

        return resultado

    # ------------------------------------------------------------------ etapas
    def _planejar(self) -> PlanningResult:
        with self._db.unit_of_work() as session:
            planner = NotificationPlanner(
                SQLAlchemyNotificationRepository(session),
                intervalo_padrao_dias=self._settings.intervalo_manutencao_padrao_dias,
            )
            return planner.planejar()

    def _despachar(self) -> DispatchResult:
        with self._db.unit_of_work() as session:
            dispatcher = NotificationDispatcher(
                SQLAlchemyNotificationRepository(session),
                self._sender,
                retry_policy=self._retry,
            )
            return dispatcher.despachar()
