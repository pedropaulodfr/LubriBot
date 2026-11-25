"""Configuração de logging estruturado.

O projeto usava ``print`` espalhado. Aqui centralizamos:
- um único formato (texto legível ou JSON de uma linha, para servidor);
- campo ``evento`` para agrupar logs por operação;
- nada de segredo em log (quem loga é responsável por não passar credencial).
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

_RESERVED = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "taskName", "message", "asctime",
}


class JsonFormatter(logging.Formatter):
    """Formata cada registro como uma linha JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "nivel": record.levelname,
            "logger": record.name,
            "mensagem": record.getMessage(),
        }
        for chave, valor in record.__dict__.items():
            if chave not in _RESERVED and not chave.startswith("_"):
                payload[chave] = valor
        if record.exc_info:
            payload["excecao"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """Formata registros como texto com os campos extras anexados."""

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        extras = [
            f"{chave}={valor}"
            for chave, valor in record.__dict__.items()
            if chave not in _RESERVED and not chave.startswith("_")
        ]
        return f"{base} {' '.join(extras)}".rstrip()


def configure_logging(nivel: str = "INFO", *, json_output: bool = False) -> None:
    """Configura o logging raiz da aplicação (idempotente)."""
    root = logging.getLogger()
    root.setLevel(nivel.upper())

    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(stream=sys.stdout)
    if json_output:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            TextFormatter("%(asctime)s %(levelname)-8s %(name)s | %(message)s")
        )
    root.addHandler(handler)

    # Bibliotecas externas são barulhentas em DEBUG.
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("telebot").setLevel(logging.INFO)


def get_logger(nome: str) -> logging.Logger:
    """Atalho para obter um logger nomeado."""
    return logging.getLogger(nome)


def evento(logger: logging.Logger, mensagem: str, **campos: Any) -> None:
    """Loga uma mensagem com campos estruturados (``evento`` + extras)."""
    logger.info(mensagem, extra=campos)
