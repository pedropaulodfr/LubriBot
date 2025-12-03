from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def modelos_veiculos_keyboard(modelos = []):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add(KeyboardButton("⌨️ Inserir manualmente:"))
    markup.add(KeyboardButton("❌ Cancelar"))

    for modelo in modelos:
        markup.add(KeyboardButton(modelo))
    

    return markup