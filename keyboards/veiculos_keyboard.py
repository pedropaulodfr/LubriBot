from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def gerenciar_veiculos_keyboard(): 
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🔎 Visualizar Veículos"))
    markup.add(KeyboardButton("➕ Adicionar Veículo"))
    markup.add(KeyboardButton("➖ Remover Veículo"))
    return markup

def veiculos_keyboard(veiculos = []):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    for veiculo in veiculos:
        markup.add(KeyboardButton(f"{veiculo.placa[:3]}-{veiculo.placa[-4:]} - {veiculo.tipo} {veiculo.fabricante} {veiculo.modelo} {veiculo.cor} ({veiculo.anoModelo})"))
    
    markup.add(KeyboardButton("❌ Cancelar"))

    return markup