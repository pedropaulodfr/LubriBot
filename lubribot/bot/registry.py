"""Registro central dos handlers do Telegram.

A fachada (:class:`BotFacade`) embrulha o bot para anotar qual é o próximo passo
de cada conversa. Isso, somado aos rascunhos persistidos, permite retomar um
fluxo interrompido por restart. O handler de retomada é registrado por último,
por isso só atua quando nenhum `next_step_handler` está pendente.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from lubribot.bot.facade import BotFacade
from lubribot.bot.handlers.add_manutencao_handle import add_manutencao_handle
from lubribot.bot.handlers.add_produtos_handle import add_produto_handle
from lubribot.bot.handlers.add_servico_handle import add_servico_handle
from lubribot.bot.handlers.add_veiculo_handle import add_veiculo_handle
from lubribot.bot.handlers.configuracoes_handle import (
    configuracoes_cancelar,
    configuracoes_dias_notificacao,
    configuracoes_handle,
    configuracoes_receber_notificacoes,
)
from lubribot.bot.handlers.del_veiculo_handle import del_veiculo_handle
from lubribot.bot.handlers.gerenciar_produtos_handle import gerenciar_produtos_handle
from lubribot.bot.handlers.gerenciar_servicos_handle import gerenciar_servicos_handle
from lubribot.bot.handlers.gerenciar_veiculos_handle import gerenciar_veiculos_handle
from lubribot.bot.handlers.mais_handle import mais_handle
from lubribot.bot.handlers.navegacao_handle import navegacao_handle
from lubribot.bot.handlers.start_handle import start
from lubribot.bot.handlers.ver_diagnostico_handle import ver_diagnostico_handle
from lubribot.bot.handlers.ver_dicas_handle import ver_dica_handle
from lubribot.bot.handlers.ver_manutencoes_handle import ver_manutencao_handle
from lubribot.bot.handlers.ver_produtos_handle import ver_produtos_handle
from lubribot.bot.handlers.ver_servicos_handle import ver_servicos_handle
from lubribot.bot.handlers.ver_veiculos_handle import ver_veiculo_handle
from lubribot.bot.keyboards.checkbox_genericos_keyboard import register_checkbox_handlers
from lubribot.utils.logging import get_logger

if TYPE_CHECKING:  # pragma: no cover
    from telebot import TeleBot

logger = get_logger(__name__)


def registrar_handlers(bot: TeleBot) -> BotFacade:
    """Registra todos os handlers na instância do bot (ordem preservada)."""
    facade = BotFacade(bot)
    start(facade)
    navegacao_handle(facade)
    add_manutencao_handle(facade)
    ver_manutencao_handle(facade)
    add_veiculo_handle(facade)
    ver_veiculo_handle(facade)
    del_veiculo_handle(facade)
    gerenciar_veiculos_handle(facade)
    configuracoes_handle(facade)
    configuracoes_receber_notificacoes(facade)
    configuracoes_dias_notificacao(facade)
    configuracoes_cancelar(facade)
    ver_dica_handle(facade)
    ver_diagnostico_handle(facade)
    register_checkbox_handlers(facade)
    mais_handle(facade)
    gerenciar_produtos_handle(facade)
    add_produto_handle(facade)
    ver_produtos_handle(facade)
    gerenciar_servicos_handle(facade)
    ver_servicos_handle(facade)
    add_servico_handle(facade)
    _registrar_retomada(facade)
    logger.info("handlers_registrados")
    return facade


def _registrar_retomada(facade: BotFacade) -> None:
    """Catch-all que retoma um rascunho persistido quando não há passo pendente."""

    @facade.message_handler(content_types=["text", "photo"])
    def retomar_conversa(message):
        if (message.text or "").startswith("/"):
            return
        retomada = facade.retomar(message.chat.id)
        if retomada is None:
            return
        _registro, _etapa, callback = retomada
        facade.send_message(
            message.chat.id,
            "🔄 Retomando a operação que ficou em andamento...",
        )
        logger.info("conversa_retomada", extra={"chat_id": message.chat.id})
        callback(message)
