from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from services.usuarioparametros_service import get_parametros_usuario_by_telegram_id

def configuracoes_keyboard(message): 
    parametros = get_parametros_usuario_by_telegram_id(message.from_user.id)

    recebe_notificacao = parametros.receberNotificacoes if parametros else False

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(f"{'🔕 Desativar' if recebe_notificacao else '🔔 Ativar'} Notificações"))
    markup.add(KeyboardButton("⏱️ Configurar Periodo de Notificação"))
    markup.add(KeyboardButton("❌ Cancelar"))
    return markup