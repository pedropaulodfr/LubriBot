"""Compatibilidade da API antiga de notificações.

A lógica saiu do banco (procedure não versionada) para Python puro, testável e
idempotente. Este módulo mantém as duas funções que o código antigo chamava, para
que imports existentes não quebrem durante a transição.

Para uso novo, prefira :class:`lubribot.jobs.notification_job.NotificationJob`.
"""

from __future__ import annotations

from lubribot.config.settings import get_settings
from lubribot.database.runtime import get_database
from lubribot.domain.notifications import RetryPolicy
from lubribot.integrations.telegram_sender import TelegramSender
from lubribot.notifications.dispatcher import NotificationDispatcher
from lubribot.notifications.models import DispatchResult, PlanningResult
from lubribot.notifications.planner import NotificationPlanner
from lubribot.repositories.notification_repository import (
    SQLAlchemyNotificationRepository,
)
from lubribot.utils.logging import get_logger

logger = get_logger(__name__)


def ProcessarNotificacoes() -> PlanningResult:
    """Gera as notificações devidas (equivalente à antiga procedure)."""
    settings = get_settings()
    db = get_database()
    with db.unit_of_work() as session:
        planner = NotificationPlanner(
            SQLAlchemyNotificationRepository(session),
            intervalo_padrao_dias=settings.intervalo_manutencao_padrao_dias,
            intervalo_km_padrao=settings.intervalo_km_padrao,
        )
        return planner.planejar()


def EnviaNotificacoes(bot) -> DispatchResult:
    """Envia as notificações pendentes com retentativa controlada."""
    settings = get_settings()
    db = get_database()
    with db.unit_of_work() as session:
        dispatcher = NotificationDispatcher(
            SQLAlchemyNotificationRepository(session),
            TelegramSender(bot),
            retry_policy=RetryPolicy(
                max_tentativas=settings.notificacoes_max_tentativas,
                base_segundos=settings.notificacoes_backoff_base_segundos,
            ),
        )
        return dispatcher.despachar()
