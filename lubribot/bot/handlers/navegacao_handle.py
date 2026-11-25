"""Navegação: menu novo, restauração do teclado e cancelamento global.

Motivação (auditoria de UX):
- o menu principal tinha um botão literal `"..."` escondendo o histórico;
- não havia como restaurar o teclado se o usuário ficasse preso num fluxo;
- não havia comando global para cancelar uma conversa em andamento.
"""

from __future__ import annotations

from lubribot.bot.keyboards.menu_principal_keyboard import menu_principal
from lubribot.utils.logging import get_logger

logger = get_logger(__name__)

AJUDA = (
    "🤖 <b>Como usar o LubriBot</b>\n\n"
    "Use os botões do teclado para navegar. Comandos úteis:\n"
    "• /menu — restaura o teclado do menu principal\n"
    "• /cancelar — interrompe a operação em andamento\n"
    "• /ajuda — mostra esta mensagem\n\n"
    "Se o teclado sumir, envie /menu."
)


def _limpar_estados(chat_id: int) -> int:
    """Limpa rascunhos de conversa em andamento; devolve quantos foram limpos."""
    from lubribot.bot.handlers.add_manutencao_handle import limpar_estado as limpar_manutencao
    from lubribot.bot.handlers.add_veiculo_handle import limpar_estado as limpar_veiculo
    from lubribot.bot.handlers.ver_diagnostico_handle import limpar_estado as limpar_diagnostico

    limpos = 0
    for funcao in (limpar_manutencao, limpar_veiculo, limpar_diagnostico):
        if funcao(chat_id):
            limpos += 1
    return limpos


def navegacao_handle(bot):
    @bot.message_handler(commands=["menu", "start_menu"])
    def menu_comando(message):
        bot.send_message(
            message.chat.id,
            "Menu principal:",
            reply_markup=menu_principal(),
        )

    @bot.message_handler(commands=["cancelar", "cancel"])
    def cancelar_comando(message):
        limpos = _limpar_estados(message.chat.id)
        logger.info(
            "cancelamento_global",
            extra={"chat_id": message.chat.id, "rascunhos_limpos": limpos},
        )
        texto = (
            "✅ Operação cancelada."
            if limpos
            else "ℹ️ Não havia operação em andamento."
        )
        bot.send_message(message.chat.id, texto, reply_markup=menu_principal())

    @bot.message_handler(commands=["ajuda", "help"])
    def ajuda_comando(message):
        bot.send_message(message.chat.id, AJUDA, parse_mode="HTML", reply_markup=menu_principal())
