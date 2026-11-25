"""Agendador periódico com desligamento gracioso e trava de instância única.

Substitui o laço legado ``while True: ...; time.sleep(24h)``, que:

- morria em silêncio na primeira exceção (inclusive ``NameError``);
- usava ``sleep`` fixo, sem respeitar o intervalo configurado;
- permitia duas instâncias enviando a mesma notificação.

A trava usa ``pg_try_advisory_lock``: se outra instância está executando o ciclo,
esta apenas espera o próximo intervalo.
"""

from __future__ import annotations

import threading
import time

from lubribot.database.engine import Database
from lubribot.database.locks import AdvisoryLock
from lubribot.jobs.notification_job import NotificationJob
from lubribot.utils.logging import get_logger

logger = get_logger(__name__)


class PeriodicScheduler(threading.Thread):
    """Thread que executa o job em intervalos fixos e para de forma limpa."""

    def __init__(
        self,
        job: NotificationJob,
        *,
        interval_seconds: int,
        db: Database,
        lock_key: int,
        stop_event: threading.Event | None = None,
        nome: str = "notificacoes",
    ) -> None:
        super().__init__(name=nome, daemon=True)
        self._job = job
        self._interval = max(1, interval_seconds)
        self._db = db
        self._lock_key = lock_key
        self._stop = stop_event or threading.Event()

    def parar(self) -> None:
        """Sinaliza parada; a thread termina após o ciclo corrente."""
        self._stop.set()

    # ------------------------------------------------------------------- laço
    def run(self) -> None:  # pragma: no cover - laço de infraestrutura
        logger.info(
            "scheduler_iniciado",
            extra={"intervalo_segundos": self._interval, "nome": self.name},
        )
        while not self._stop.is_set():
            inicio = time.monotonic()
            self._executar_uma_vez()
            decorrido = time.monotonic() - inicio
            espera = max(1.0, self._interval - decorrido)
            if self._stop.wait(espera):
                break
        logger.info("scheduler_encerrado", extra={"nome": self.name})

    def _executar_uma_vez(self) -> None:
        try:
            with AdvisoryLock(self._db, self._lock_key) as adquiriu:
                if not adquiriu:
                    logger.info("scheduler_ciclo_ignorado_outra_instancia")
                    return
                resultado = self._job.executar_ciclo()
                logger.info(
                    "scheduler_ciclo_concluido",
                    extra={
                        "erro": resultado.erro,
                        "planejamento": (
                            resultado.planejamento.texto()
                            if resultado.planejamento
                            else None
                        ),
                        "despacho": (
                            resultado.despacho.texto() if resultado.despacho else None
                        ),
                    },
                )
        except Exception:
            # O agendador nunca morre por causa de um ciclo com problema.
            logger.exception("scheduler_ciclo_falhou")
