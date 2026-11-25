"""Bootstrap da aplicação: bot, job periódico e health check.

Responsabilidades deste módulo:
- carregar e validar configuração;
- configurar logging;
- montar banco, bot, sender e job;
- iniciar o agendador em thread própria;
- servir ``GET /ping`` quando habilitado (o alvo futuro é o servidor do J4 Core);
- desligar de forma graciosa em SIGINT/SIGTERM.
"""

from __future__ import annotations

import contextlib
import signal
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from lubribot.bot.registry import registrar_handlers
from lubribot.config.settings import Settings, get_settings
from lubribot.database.runtime import get_database
from lubribot.integrations.telegram_sender import TelegramSender
from lubribot.jobs.notification_job import NotificationJob
from lubribot.jobs.scheduler import PeriodicScheduler
from lubribot.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


# ----------------------------------------------------------------------------
# Health check
# ----------------------------------------------------------------------------
class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (assinatura da stdlib)
        if self.path == "/ping":
            corpo = b'{"status": "ok", "message": "bot ativo"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, formato: str, *args) -> None:  # noqa: A002
        logger.debug("healthcheck_requisicao", extra={"detalhe": formato % args})


def _iniciar_http(settings: Settings) -> ThreadingHTTPServer:
    servidor = ThreadingHTTPServer((settings.http_host, settings.http_port), _HealthHandler)
    thread = threading.Thread(
        target=servidor.serve_forever, name="http-healthcheck", daemon=True
    )
    thread.start()
    logger.info(
        "http_healthcheck_ativo",
        extra={"host": settings.http_host, "porta": settings.http_port},
    )
    return servidor


# ----------------------------------------------------------------------------
# Aplicação
# ----------------------------------------------------------------------------
class Application:
    """Contêiner de dependências da aplicação."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        configure_logging(self.settings.log_level, json_output=self.settings.log_json)

        self.db = get_database()
        self.stop_event = threading.Event()

        import telebot  # import local: mantém o custo fora de testes de domínio

        self.bot = telebot.TeleBot(self.settings.telegram_token)
        registrar_handlers(self.bot)

        self.sender = TelegramSender(self.bot)
        self.job = NotificationJob(self.db, self.sender, self.settings)
        self.scheduler: PeriodicScheduler | None = None
        self.http: ThreadingHTTPServer | None = None

    # --------------------------------------------------------------- ciclo de vida
    def iniciar_agendador(self) -> PeriodicScheduler:
        self.scheduler = PeriodicScheduler(
            self.job,
            interval_seconds=self.settings.intervalo_notificacao_segundos,
            db=self.db,
            lock_key=self.settings.scheduler_lock_key,
            stop_event=self.stop_event,
        )
        self.scheduler.start()
        return self.scheduler

    def iniciar_http(self) -> None:
        if self.settings.http_habilitado:
            self.http = _iniciar_http(self.settings)

    def encerrar(self) -> None:
        self.stop_event.set()
        if self.scheduler is not None:
            self.scheduler.parar()
            self.scheduler.join(timeout=30)
        if self.http is not None:
            self.http.shutdown()
        self.db.dispose()
        logger.info("aplicacao_encerrada")

    # --------------------------------------------------------------- execução
    def executar(self) -> int:
        self._instalar_sinais()
        self.iniciar_http()
        if self.settings.notificacoes_habilitadas:
            self.iniciar_agendador()
        else:
            logger.warning("scheduler_desabilitado_por_configuracao")

        logger.info(
            "bot_iniciado",
            extra={
                "ambiente": self.settings.ambiente_rotulo,
                "polling": "long_polling",
            },
        )
        try:
            self.bot.remove_webhook()
            self.bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except KeyboardInterrupt:  # pragma: no cover
            logger.info("bot_interrompido_por_usuario")
        finally:
            self.encerrar()
        return 0

    def _instalar_sinais(self) -> None:
        def _handler(signum, _frame):  # pragma: no cover - sinal do SO
            logger.info("sinal_recebido", extra={"sinal": signum})
            self.stop_event.set()

        for nome in ("SIGINT", "SIGTERM"):
            sinal = getattr(signal, nome, None)
            if sinal is not None:
                with contextlib.suppress(ValueError):  # registro fora do thread principal
                    signal.signal(sinal, _handler)


def run() -> int:
    """Entrada da aplicação; retorna código de saída."""
    return Application().executar()
