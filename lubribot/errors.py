"""Exceções de domínio e de infraestrutura da aplicação."""

from __future__ import annotations


class LubriBotError(Exception):
    """Erro base da aplicação."""


class ConfigurationError(LubriBotError):
    """Configuração ausente ou inválida."""


class TelegramError(LubriBotError):
    """Falha genérica no envio pelo Telegram."""


class TelegramTransientError(TelegramError):
    """Falha temporária: faz sentido tentar novamente com backoff."""


class TelegramPermanentError(TelegramError):
    """Falha definitiva (ex.: bot bloqueado pelo usuário). Não repetir."""

    def __init__(self, mensagem: str, *, chat_id: int | None = None) -> None:
        super().__init__(mensagem)
        self.chat_id = chat_id


class NotificationError(LubriBotError):
    """Falha no planejamento ou despacho de notificações."""
