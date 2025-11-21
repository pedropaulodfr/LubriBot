from telebot.types import ReplyKeyboardRemove, ForceReply
from keyboards.veiculos_keyboard import gerenciar_veiculos_keyboard

def gerenciar_veiculos_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "Gerenciar Veículos")
    def gerenciar_veiculo(message):

        gerenciar_veiculos_options = gerenciar_veiculos_keyboard()
        bot.send_message(message.chat.id,"Escolha: ", reply_markup=gerenciar_veiculos_options)