from telebot.types import ReplyKeyboardRemove, ForceReply
from repository.models import Usuario, Produto, _Session
from keyboards.menu_principal_keyboard import menu_principal

session = _Session()
usuario = Usuario()

def add_produto_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "➕🛢️ Adicionar Produtos")
    def add_produto(message):
        bot.send_message(message.chat.id,"Iniciando o processo de registro do produto. Por favor, preencha as informações.", reply_markup=ReplyKeyboardRemove())

        usuario = session.query(Usuario).filter(Usuario.telegram_id == message.from_user.id).first()
        if not usuario:
            bot.send_message(message.chat.id, "❌ Usuário não encontrado.")
            return

        produto = Produto()
        produto.usuario_id = usuario.id
        produto.status = "Ativo"

        bot.send_message(message.chat.id, "Informe a descrição do produto:", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_descricao, produto)

    def receber_descricao(message, produto):
        descricao = message.text.strip().capitalize()
        produto.descricao = descricao

        bot.send_message(message.chat.id, "⏳ Registrando produto...")
        finalizar_registro(message, produto)


    def finalizar_registro(message, produto):
        session.add(produto)
        session.commit()
        session.close()
        bot.send_message(message.chat.id, "✅ Produto registrado com sucesso!")
        bot.send_message(message.chat.id, f"Escolha uma opção:", reply_markup=menu_principal())