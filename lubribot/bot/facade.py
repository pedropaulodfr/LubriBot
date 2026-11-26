"""Fachada do bot que registra a etapa de cada conversa.

Os handlers continuam usando ``bot.register_next_step_handler(...)``; a fachada
intercepta a chamada para guardar qual função é o próximo passo. Se o processo
reiniciar, o rascunho persistido + o nome da etapa permitem retomar de onde parou.

Nenhuma outra característica do bot é alterada: tudo o mais é repassado.
"""

from __future__ import annotations

from typing import Any

from lubribot.bot.conversation_store import registros_ativos
from lubribot.utils.logging import get_logger

logger = get_logger(__name__)


class BotFacade:
    def __init__(self, bot: Any) -> None:
        self._bot = bot
        self._passos: dict[str, Any] = {}

    def __getattr__(self, nome: str) -> Any:
        return getattr(self._bot, nome)

    def register_next_step_handler(self, message, callback, *args, **kwargs):
        self._passos[callback.__name__] = callback
        chat_id = getattr(getattr(message, "chat", None), "id", None)
        if chat_id is not None:
            for registro in registros_ativos():
                registro.definir_etapa(chat_id, callback.__name__)
        return self._bot.register_next_step_handler(message, callback, *args, **kwargs)

    # ------------------------------------------------------------------ retomada
    def obter_passo(self, etapa: str | None) -> Any:
        if not etapa:
            return None
        return self._passos.get(etapa)

    def retomar(self, chat_id: int):
        """Retorna (registro, etapa, callback) do fluxo pendente, se houver."""
        for registro in registros_ativos():
            if not registro.tem_conversa(chat_id):
                continue
            etapa = registro.obter_etapa(chat_id)
            callback = self.obter_passo(etapa)
            if callback is not None:
                return registro, etapa, callback
        return None
