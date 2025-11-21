from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def markups_genericos_keyboard(lista = [], identificador = ""):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    for item in lista:
        # Suporta tanto objetos com atributos quanto dicts
        if isinstance(item, dict):
            valor = item.get(identificador, "")
        else:
            valor = item.__getattribute__(identificador)
        
        if valor:
            markup.add(KeyboardButton(valor))
    
    return markup