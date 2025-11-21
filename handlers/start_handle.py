from keyboards.menu_principal_keyboard import menu_principal
from repository.models import Usuario, Veiculo, _Session

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
