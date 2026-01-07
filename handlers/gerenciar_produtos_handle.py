from keyboards.markups_genericos_keyboard import markups_genericos_keyboard

def gerenciar_produtos_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "🛢️ Gerenciar Produtos")
    def gerenciar_produtos(message):
        gerenciar_produtos_opcoes = markups_genericos_keyboard([
            {'identificacao': '🔍🛢️ Ver Produtos'},
            {'identificacao': '➕🛢️ Adicionar Produtos'},
        ], "identificacao")

        bot.send_message(message.chat.id,"Escolha: ", reply_markup=gerenciar_produtos_opcoes)