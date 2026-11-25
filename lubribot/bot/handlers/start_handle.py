"""Comandos de entrada: /start, /teste (QA) e boas-vindas.

Mudanças:
- a mensagem de boas-vindas orienta sobre /menu e /cancelar;
- o comando de debug `/teste` deixou de existir em produção (só com
  ``DEBUG_COMMANDS=true``), para não expor um fluxo experimental a usuários reais.
"""

from __future__ import annotations

from lubribot.bot.keyboards.checkbox_genericos_keyboard import start_checkbox
from lubribot.bot.keyboards.menu_principal_keyboard import menu_principal
from lubribot.config.settings import get_settings
from lubribot.database.runtime import get_database
from lubribot.models import Usuario
from lubribot.utils.logging import get_logger

logger = get_logger(__name__)

BOAS_VINDAS = (
    "Olá, {nome}! 👋\n\n"
    "Escolha uma opção no teclado abaixo.\n"
    "• /menu restaura o teclado\n"
    "• /cancelar interrompe a operação atual\n"
    "• /ajuda mostra todos os comandos"
)


def start(bot):
    @bot.message_handler(commands=["start"])
    def send_welcome(message):
        with get_database().unit_of_work() as session:
            usuario = (
                session.query(Usuario)
                .filter(Usuario.telegram_id == message.from_user.id)
                .first()
            )
            if not usuario:
                usuario = Usuario(
                    telegram_id=message.from_user.id,
                    perfil="Proprietario",
                    primeiroNome=message.from_user.first_name or "",
                    ultimoNome=message.from_user.last_name or "",
                    usuarioNome=message.from_user.username or "",
                    status="Ativo",
                )
                session.add(usuario)

        bot.send_message(
            message.chat.id,
            BOAS_VINDAS.format(nome=message.from_user.first_name or ""),
            reply_markup=menu_principal(),
        )

    # ---------------------------------------------------------------- debug
    if get_settings().debug_commands:

        @bot.message_handler(commands=["teste"])
        def teste(message):
            from services.produtos_service import get_all_produtos

            produtos = get_all_produtos()
            opcoes = [produto.descricao_completa for produto in produtos]

            def finalizado(chat_id, selecionadas):
                bot.send_message(chat_id, f"Você escolheu: {', '.join(selecionadas)}")

            start_checkbox(bot, message.chat.id, opcoes, finalizado)
