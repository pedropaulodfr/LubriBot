"""Envio de mensagens pelo Telegram com classificação de falha.

O código legado chamava ``bot.send_message`` e tratava qualquer exceção do mesmo
jeito. Aqui separamos:

- **permanente** (HTTP 400/403): usuário bloqueou o bot, chat inválido, texto
  rejeitado → não adianta repetir; a notificação vira ``Falha``.
- **temporária** (HTTP 429, 5xx, timeout, rede): repete com backoff, respeitando
  o ``retry_after`` quando o Telegram informa.
"""

from __future__ import annotations

from typing import Any

from lubribot.notifications.ports import SendOutcome
from lubribot.utils.logging import get_logger

logger = get_logger(__name__)


class TelegramSender:
    """Adaptador entre o despachante e a API do Telegram."""

    def __init__(self, bot: Any, *, parse_mode: str | None = None) -> None:
        self._bot = bot
        self._parse_mode = parse_mode

    def enviar(self, chat_id: int, texto: str) -> SendOutcome:
        if not texto:
            return SendOutcome.definitivo("conteúdo vazio")
        try:
            kwargs: dict[str, Any] = {"chat_id": chat_id, "text": texto}
            if self._parse_mode:
                kwargs["parse_mode"] = self._parse_mode
            self._bot.send_message(**kwargs)
            return SendOutcome.sucesso()
        except Exception as exc:  # classificamos via atributos da exceção
            return self._classificar(exc, chat_id)

    # ------------------------------------------------------------------ interno
    def _classificar(self, exc: Exception, chat_id: int) -> SendOutcome:
        codigo = getattr(exc, "error_code", None)
        descricao = getattr(exc, "description", None) or str(exc)

        if codigo == 429:
            retry_after = _extrair_retry_after(exc)
            logger.warning(
                "telegram_rate_limit",
                extra={"chat_id": chat_id, "retry_after": retry_after},
            )
            return SendOutcome.transitorio(f"HTTP 429: {descricao}", retry_after=retry_after)

        if codigo in {400, 403}:
            # 400 "chat not found"/"message text is empty"; 403 bot bloqueado.
            return SendOutcome.definitivo(f"HTTP {codigo}: {descricao}")

        if codigo is not None and 500 <= codigo < 600:
            return SendOutcome.transitorio(f"HTTP {codigo}: {descricao}")

        # Timeout, DNS, conexão resetada e afins: vale tentar de novo.
        return SendOutcome.transitorio(f"{type(exc).__name__}: {descricao}")


def _extrair_retry_after(exc: Exception) -> int | None:
    """Lê ``parameters.retry_after`` da resposta do Telegram, quando existir."""
    for atributo in ("result_json", "result", "json"):
        payload = getattr(exc, atributo, None)
        if isinstance(payload, dict):
            parametros = payload.get("parameters") or {}
            retry_after = parametros.get("retry_after")
            if isinstance(retry_after, int):
                return retry_after
    return None
