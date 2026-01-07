from keyboards.markups_genericos_keyboard import markups_genericos_keyboard

def mais_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "...")
    def mais(message):
        menu_opcoes = markups_genericos_keyboard([
            {'identificacao': '🔎 Ver Manutenções'},
            {'identificacao': '🛢️ Gerenciar Produtos'},
            {'identificacao': '🧰 Gerenciar Serviços'},
        ], "identificacao")

        bot.send_message(message.chat.id,"Escolha: ", reply_markup=menu_opcoes)