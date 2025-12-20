from keyboards.menu_principal_keyboard import menu_principal
from keyboards.checkbox_genericos_keyboard import start_checkbox
from repository.models import Usuario, _Session

session = _Session()

def start(bot):
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        usuario = session.query(Usuario).filter(Usuario.telegram_id == message.from_user.id).first()

        if not usuario:
            usuario = Usuario( 
                telegram_id=message.from_user.id,
                perfil="Proprietario",
                primeiroNome=message.from_user.first_name or "",
                ultimoNome=message.from_user.last_name or "",
                usuarioNome=message.from_user.username or "",
                status="Ativo"
            )
            session.add(usuario)
            session.commit()
            session.refresh(usuario)

        bot.send_message(message.chat.id, f"Olá, {message.from_user.first_name}! Escolha uma opção:", reply_markup=menu_principal())

    @bot.message_handler(commands=['teste'])
    def teste(message):
        from services.produtos_service import get_all_produtos, get_produto_by_descricao_completa
        produtos = get_all_produtos()

        opcoes = []
        for produto in produtos:
            opcoes.append(produto.descricao_completa)
        
        def finalizado(chat_id, selecionadas):
            produtos_selecionados = []
            for desc in selecionadas:
                produto = get_produto_by_descricao_completa(desc)
                if produto:
                    produtos_selecionados.append(produto.descricao)
            bot.send_message(chat_id, f"Você escolheu: {', '.join(produtos_selecionados)}")

        start_checkbox(bot, message.chat.id, opcoes, finalizado)
