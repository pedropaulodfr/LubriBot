from keyboards.markups_genericos_keyboard import markups_genericos_keyboard

def gerenciar_servicos_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "🧰 Gerenciar Serviços")
    def gerenciar_servicos(message):
        gerenciar_servicos_opcoes = markups_genericos_keyboard([
            {'identificacao': '🔍🧰 Ver Serviços'},
            {'identificacao': '➕🧰 Adicionar Serviço'}
        ], "identificacao")

        bot.send_message(message.chat.id,"Escolha: ", reply_markup=gerenciar_servicos_opcoes)