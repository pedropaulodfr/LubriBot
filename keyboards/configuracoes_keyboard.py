from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def configuracoes_keyboard(): 
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Ativar/Desativar Notificações"))
    markup.add(KeyboardButton("Configurar Periodo de Notificacao"))
    return markup