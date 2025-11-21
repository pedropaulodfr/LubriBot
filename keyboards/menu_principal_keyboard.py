from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def menu_principal():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("Registrar Manutenção"), 
        KeyboardButton("Ver Manutenções"),
        KeyboardButton("Gerenciar Veículos"),
        KeyboardButton("⚙️ Configurações"),
    )   
    return markup