from telebot.types import ReplyKeyboardRemove, ForceReply
from repository.models import Usuario, Servico, _Session
from keyboards.menu_principal_keyboard import menu_principal

session = _Session()
servico = Servico()
usuario = Usuario()

def add_servico_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "➕🧰 Adicionar Serviço")
    def add_servico(message):
        bot.send_message(message.chat.id,"Iniciando o processo de registro do serviço. Por favor, preencha as informações.", reply_markup=ReplyKeyboardRemove())

        usuario = session.query(Usuario).filter(Usuario.telegram_id == message.from_user.id).first()
        if not usuario:
            bot.send_message(message.chat.id, "❌ Usuário não encontrado.")
            return

        servico.usuario_id = usuario.id
        servico.status = "Ativo"

        bot.send_message(message.chat.id, "Informe a descrição do serviço:", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_descricao)

    def receber_descricao(message):
        descricao = message.text.strip().capitalize()
        servico.descricao = descricao

        bot.send_message(message.chat.id, "⏳ Registrando serviço...")
        finalizar_registro(message)


    def finalizar_registro(message):
        session.add(servico)
        session.commit()
        session.close()
        bot.send_message(message.chat.id, "✅ Serviço registrado com sucesso!")
        bot.send_message(message.chat.id, f"Escolha uma opção:", reply_markup=menu_principal())