from telebot.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from repository.models import Usuario, Servico, _Session
from keyboards.menu_principal_keyboard import menu_principal
from keyboards.markups_genericos_keyboard import markups_genericos_keyboard
from services.servicos_service import get_servicos_by_usuario


session = _Session()

def ver_servicos_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "🔍🧰 Ver Serviços")
    def ver_servicos(message):
        try:
            usuario = session.query(Usuario).filter(Usuario.telegram_id == message.from_user.id).first()
            
            if not usuario:
                bot.send_message(message.chat.id, "❌ Usuário não encontrado.")
                return

            servicos = get_servicos_by_usuario(usuario.id)

            if(len(servicos) == 0):
                bot.send_message(message.chat.id, f"⚠️ Você ainda não possui serviços registrados!", reply_markup=menu_principal())
                return

            bot.send_message(message.chat.id, f"{message.from_user.first_name}, aqui estão os seus serviços cadastrados:", reply_markup=ReplyKeyboardRemove())

            for servico in servicos:
                info_servico = (
                    f"🔖 Descrição: {servico.descricao}\n"
                    f"🔎 Status: {servico.status}\n"
                    "➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖"
                )

                keyboard = InlineKeyboardMarkup()
                keyboard.add(
                    InlineKeyboardButton("🗑️ Excluir Serviço", callback_data=f"excluir_servico_{servico.id}")
                )

                bot.send_message(message.chat.id, info_servico, reply_markup=keyboard)

            bot.send_message(message.chat.id, f"Escolha uma opção:", reply_markup=menu_principal())
        finally:
            session.close()

    @bot.callback_query_handler(func=lambda call: call.data.startswith("excluir_servico_"))
    def callback_excluir_servico(call):
        servico_id = int(call.data.replace("excluir_servico_", ""))

        bot.send_message(call.message.chat.id, "⚠️ Tem certeza que deseja excluir este serviço?", reply_markup=ReplyKeyboardRemove())
        confirmacao_opcoes = markups_genericos_keyboard([
            {'identificacao': 'Sim'},
            {'identificacao': 'Não'},
        ], "identificacao")

        bot.send_message(call.message.chat.id,"Escolha: ", reply_markup=confirmacao_opcoes)

        @bot.message_handler(func=lambda message: message.text in ["Sim", "Não"])
        def confirmar_exclusao_servico(message):
            if message.text == "Sim":
                excluir_servico(call, servico_id)
            else:
                bot.send_message(message.chat.id, "❌ Exclusão cancelada.", reply_markup=menu_principal())


    def excluir_servico(call, servico_id):
        session = _Session()
        try:
            servico = session.query(Servico).filter(Servico.id == servico_id).first()

            if not servico:
                bot.send_message(call.message.chat.id, "❌ Serviço não encontrado.")
                return

            servico.status = "Excluido"
            session.commit()

            bot.send_message(call.message.chat.id, "✅ Serviço excluído com sucesso!", reply_markup=menu_principal())
        finally:
            session.close()