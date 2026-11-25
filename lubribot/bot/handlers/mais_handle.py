"""Submenu "Mais opções": catálogo de produtos e serviços.

O botão antigo era `"..."`. Para não quebrar teclados já enviados aos usuários
(o Telegram mantém o teclado antigo no cliente), o handler aceita os dois textos.
"""

from __future__ import annotations

from lubribot.bot.keyboards.markups_genericos_keyboard import markups_genericos_keyboard

TEXTOS_BOTAO = ("🗂️ Mais opções", "...")


def mais_handle(bot):
    @bot.message_handler(func=lambda message: message.text in TEXTOS_BOTAO)
    def mais(message):
        opcoes = markups_genericos_keyboard(
            [
                {"identificacao": "🛢️ Gerenciar Produtos"},
                {"identificacao": "🧰 Gerenciar Serviços"},
            ],
            "identificacao",
        )
        bot.send_message(
            message.chat.id,
            "🗂️ Mais opções — escolha uma categoria:",
            reply_markup=opcoes,
        )
