from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def tipos_veiculos_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("Carro"), 
        KeyboardButton("Moto"),
        KeyboardButton("Caminhão"),
        KeyboardButton("Ônibus"),
        KeyboardButton("Van"),
        KeyboardButton("Outro"),
        KeyboardButton("Cancelar")
    )
    
    return markup