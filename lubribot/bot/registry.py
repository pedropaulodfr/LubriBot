"""Registro central dos handlers do Telegram.

Os handlers ainda são os módulos legados (a migração de UX é a fase F5). Manter o
registro num único lugar evita o ``main.py`` de 130 linhas com 21 imports soltos.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from handlers.add_manutencao_handle import add_manutencao_handle
from handlers.add_produtos_handle import add_produto_handle
from handlers.add_servico_handle import add_servico_handle
from handlers.add_veiculo_handle import add_veiculo_handle
from handlers.configuracoes_handle import (
    configuracoes_cancelar,
    configuracoes_dias_notificacao,
    configuracoes_handle,
    configuracoes_receber_notificacoes,
)
from handlers.del_veiculo_handle import del_veiculo_handle
from handlers.gerenciar_produtos_handle import gerenciar_produtos_handle
from handlers.gerenciar_servicos_handle import gerenciar_servicos_handle
from handlers.gerenciar_veiculos_handle import gerenciar_veiculos_handle
from handlers.mais_handle import mais_handle
from handlers.navegacao_handle import navegacao_handle
from handlers.start_handle import start
from handlers.ver_diagnostico_handle import ver_diagnostico_handle
from handlers.ver_dicas_handle import ver_dica_handle
from handlers.ver_manutencoes_handle import ver_manutencao_handle
from handlers.ver_produtos_handle import ver_produtos_handle
from handlers.ver_servicos_handle import ver_servicos_handle
from handlers.ver_veiculos_handle import ver_veiculo_handle
from keyboards.checkbox_genericos_keyboard import register_checkbox_handlers
from lubribot.utils.logging import get_logger

if TYPE_CHECKING:  # pragma: no cover
    from telebot import TeleBot

logger = get_logger(__name__)


def registrar_handlers(bot: TeleBot) -> None:
    """Registra todos os handlers na instância do bot (ordem preservada)."""
    start(bot)
    navegacao_handle(bot)
    add_manutencao_handle(bot)
    ver_manutencao_handle(bot)
    add_veiculo_handle(bot)
    ver_veiculo_handle(bot)
    del_veiculo_handle(bot)
    gerenciar_veiculos_handle(bot)
    configuracoes_handle(bot)
    configuracoes_receber_notificacoes(bot)
    configuracoes_dias_notificacao(bot)
    configuracoes_cancelar(bot)
    ver_dica_handle(bot)
    ver_diagnostico_handle(bot)
    register_checkbox_handlers(bot)
    mais_handle(bot)
    gerenciar_produtos_handle(bot)
    add_produto_handle(bot)
    ver_produtos_handle(bot)
    gerenciar_servicos_handle(bot)
    ver_servicos_handle(bot)
    add_servico_handle(bot)
    logger.info("handlers_registrados")
