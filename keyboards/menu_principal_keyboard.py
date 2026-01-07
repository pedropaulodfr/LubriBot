from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def menu_principal():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("🛠️ Registrar Manutenção"), 
        # KeyboardButton("🔎 Ver Manutenções"),
        KeyboardButton("🚘 Gerenciar Veículos"),
        KeyboardButton("..."),
        KeyboardButton("💡 Dicas"),
        KeyboardButton("⚠️ Diagnósticos"),
        KeyboardButton("⚙️ Configurações"),
    )   
    return markup