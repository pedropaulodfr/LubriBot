from telebot.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from repository.models import Usuario, Produto, _Session
from keyboards.menu_principal_keyboard import menu_principal
from keyboards.markups_genericos_keyboard import markups_genericos_keyboard
from services.produtos_service import get_produtos_by_usuario


session = _Session()

def ver_produtos_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "🔍🛢️ Ver Produtos")
    def ver_produtos(message):
        try:
            usuario = session.query(Usuario).filter(Usuario.telegram_id == message.from_user.id).first()
            
            if not usuario:
                bot.send_message(message.chat.id, "❌ Usuário não encontrado.")
                return

            produtos = get_produtos_by_usuario(usuario.id)

            if(len(produtos) == 0):
                bot.send_message(message.chat.id, f"⚠️ Você ainda não possui produtos registrados!", reply_markup=menu_principal())
                return

            bot.send_message(message.chat.id, f"{message.from_user.first_name}, aqui estão os seus produtos cadastrados:", reply_markup=ReplyKeyboardRemove())

            for produto in produtos:
                info_produto = (
                    f"🔖 Descrição: {produto.descricao}\n"
                    f"🔎 Status: {produto.status}\n"
                    "➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖"
                )

                keyboard = InlineKeyboardMarkup()
                keyboard.add(
                    InlineKeyboardButton("🗑️ Excluir Produto", callback_data=f"excluir_produto_{produto.id}")
                )

                bot.send_message(message.chat.id, info_produto, reply_markup=keyboard)

            bot.send_message(message.chat.id, f"Escolha uma opção:", reply_markup=menu_principal())
        finally:
            session.close()

    @bot.callback_query_handler(func=lambda call: call.data.startswith("excluir_produto_"))
    def callback_excluir_produto(call):
        produto_id = int(call.data.replace("excluir_produto_", ""))

        bot.send_message(call.message.chat.id, "⚠️ Tem certeza que deseja excluir este produto?", reply_markup=ReplyKeyboardRemove())
        confirmacao_opcoes = markups_genericos_keyboard([
            {'identificacao': 'Sim'},
            {'identificacao': 'Não'},
        ], "identificacao")

        bot.send_message(call.message.chat.id,"Escolha: ", reply_markup=confirmacao_opcoes)

        @bot.message_handler(func=lambda message: message.text in ["Sim", "Não"])
        def confirmar_exclusao_produto(message):
            if message.text == "Sim":
                excluir_produto(call, produto_id)
            else:
                bot.send_message(message.chat.id, "❌ Exclusão cancelada.", reply_markup=menu_principal())


    def excluir_produto(call, produto_id):
        session = _Session()
        try:
            produto = session.query(Produto).filter(Produto.id == produto_id).first()

            if not produto:
                bot.send_message(call.message.chat.id, "❌ Produto não encontrado.")
                return

            produto.status = "Excluido"
            session.commit()

            bot.send_message(call.message.chat.id, "✅ Produto excluído com sucesso!", reply_markup=menu_principal())
        finally:
            session.close()