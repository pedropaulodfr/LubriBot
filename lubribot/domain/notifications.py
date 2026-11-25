"""Ciclo de vida e política de retentativa das notificações."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

MAX_TENTATIVAS_PADRAO = 5
BACKOFF_BASE_SEGUNDOS_PADRAO = 60
BACKOFF_MAXIMO_SEGUNDOS = 6 * 60 * 60  # 6 horas


class NotificationStatus(StrEnum):
    """Estados persistidos em ``notificacoes.status``."""

    PENDENTE = "Pendente"
    ENVIADA = "Enviada"
    CANCELADA = "Cancelada"
    FALHA = "Falha"


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Política de retentativa com backoff exponencial."""

    max_tentativas: int = MAX_TENTATIVAS_PADRAO
    base_segundos: int = BACKOFF_BASE_SEGUNDOS_PADRAO
    maximo_segundos: int = BACKOFF_MAXIMO_SEGUNDOS

    def esgotou(self, tentativas: int) -> bool:
        return tentativas >= self.max_tentativas

    def atraso(self, tentativas: int) -> int:
        """Atraso em segundos após a N-ésima tentativa falha.

        >>> RetryPolicy(base_segundos=60).atraso(1)
        60
        >>> RetryPolicy(base_segundos=60).atraso(3)
        240
        >>> RetryPolicy(base_segundos=60, maximo_segundos=120).atraso(5)
        120
        """
        tentativas = max(1, tentativas)
        return min(self.base_segundos * (2 ** (tentativas - 1)), self.maximo_segundos)

    def proxima_tentativa(self, tentativas: int, agora: datetime) -> datetime:
        return agora + timedelta(seconds=self.atraso(tentativas))


def esta_pronta(
    status: str | None,
    proxima_tentativa_em: datetime | None,
    agora: datetime,
) -> bool:
    """Indica se uma notificação pendente pode ser processada agora.

    Notificação sem agendamento de retentativa (``None``) está pronta; com
    agendamento no futuro, espera — isso evita martelar a API do Telegram.
    """
    if status != NotificationStatus.PENDENTE:
        return False
    if proxima_tentativa_em is None:
        return True
    return agora >= proxima_tentativa_em
