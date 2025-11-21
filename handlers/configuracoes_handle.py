from telebot.types import ForceReply
from repository.models import _Session, Usuario, UsuarioParametro
from keyboards.configuracoes_keyboard import configuracoes_keyboard
from keyboards.menu_principal_keyboard import menu_principal


session = _Session()

def configuracoes_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "⚙️ Configurações")
    def configurar(message):

        configuracoes_options = configuracoes_keyboard()
        bot.send_message(message.chat.id,"Escolha: ", reply_markup=configuracoes_options)


def configuracoes_receber_notificacoes(bot):
    @bot.message_handler(func=lambda message: message.text == "Ativar/Desativar Notificações")
    def receber_notificacoes(message):
        usuario = session.query(Usuario).filter(Usuario.telegram_id == message.from_user.id).first()
        usuarioParametros = session.query(UsuarioParametro).filter(UsuarioParametro.usuario_id == usuario.id).first()

        if (not usuarioParametros):
            usuarioParametros = UsuarioParametro()
            usuarioParametros.usuario_id = usuario.id
            session.add(usuarioParametros)

        usuarioParametros.receberNotificacoes = not usuarioParametros.receberNotificacoes

        session.commit()
        session.refresh(usuarioParametros)
        session.close()

        if (usuarioParametros.receberNotificacoes):
            bot.send_message(message.chat.id, "🔔 Você escolheu receber notificações.")
        else:
            bot.send_message(message.chat.id, "🔕 Você escolheu não receber notificações.")

        bot.send_message(message.chat.id, f"Escolha uma opção:", reply_markup=menu_principal())


def configuracoes_dias_notificacao(bot):
    @bot.message_handler(func=lambda message: message.text == "Configurar Periodo de Notificacao")
    def dias_notificacao(message):
        bot.send_message(message.chat.id, "Com quantos dias você deseja ser notificado?", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_dias)

    def receber_dias(message):
        dias_texto = message.text

        if not dias_texto.isdigit() or int(dias_texto) <= 0:
            bot.send_message(message.chat.id, "❌ Por favor, insira um número válido de dias.", reply_markup=ForceReply())
            bot.register_next_step_handler(message, receber_dias)
            return

        dias = int(dias_texto)

        usuario = session.query(Usuario).filter(Usuario.telegram_id == message.from_user.id).first()
        usuarioParametros = session.query(UsuarioParametro).filter(UsuarioParametro.usuario_id == usuario.id).first()

        if (not usuarioParametros):
            usuarioParametros = UsuarioParametro()
            usuarioParametros.usuario_id = usuario.id
            session.add(usuarioParametros)

        usuarioParametros.diasNotificacao = dias

        session.commit()
        session.refresh(usuarioParametros)
        session.close()

        bot.send_message(message.chat.id, f"✅ Período de notificação atualizado para {dias} dias.", reply_markup=menu_principal())
        bot.send_message(message.chat.id, f"Escolha uma opção:", reply_markup=menu_principal())