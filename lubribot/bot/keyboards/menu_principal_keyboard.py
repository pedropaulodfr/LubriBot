"""Teclado do menu principal.

Mudanças em relação ao menu antigo:
- o botão `"..."` virou `"🗂️ Mais opções"` (o texto "..." não comunicava nada);
- "Ver Manutenções" saiu do submenu e passou ao primeiro nível, porque consultar
  o histórico é uma das ações mais frequentes;
- a organização segue o uso: registrar → consultar → catálogo → IA → ajustes.
"""

from telebot.types import KeyboardButton, ReplyKeyboardMarkup


def menu_principal():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        KeyboardButton("🛠️ Registrar Manutenção"),
        KeyboardButton("🔎 Ver Manutenções"),
    )
    markup.row(
        KeyboardButton("🚘 Gerenciar Veículos"),
        KeyboardButton("🗂️ Mais opções"),
    )
    markup.row(
        KeyboardButton("💡 Dicas"),
        KeyboardButton("⚠️ Diagnósticos"),
    )
    markup.row(KeyboardButton("⚙️ Configurações"))
    return markup
