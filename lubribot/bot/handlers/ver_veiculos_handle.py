from telebot.types import ReplyKeyboardRemove
from repository.models import Usuario, _Session
from lubribot.bot.keyboards.menu_principal_keyboard import menu_principal
from services.veiculos_service import get_veiculos_by_usuario


session = _Session()

def ver_veiculo_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "🔎 Visualizar Veículos")
    def ver_veiculo(message):
        try:
            usuario = session.query(Usuario).filter(Usuario.telegram_id == message.from_user.id).first()
            
            if not usuario:
                bot.send_message(message.chat.id, "❌ Usuário não encontrado.")
                return
            
            veiculos = get_veiculos_by_usuario(usuario.id)

            if(len(veiculos) == 0):
                bot.send_message(message.chat.id, f"⚠️ Você ainda não possui veículos registrados!", reply_markup=menu_principal())
                return

            bot.send_message(message.chat.id, f"{message.from_user.first_name}, aqui estão os seus veículos cadastrados:", reply_markup=ReplyKeyboardRemove())

            for veiculo in veiculos:
                info_veiculo = (
                    f"{'🏍️' if veiculo.tipo == 'Moto' else '🚗'} Tipo: {veiculo.tipo}\n"
                    f"🔖 Marca: {veiculo.fabricante}\n"
                    f"🚘 Modelo: {veiculo.modelo}\n"
                    f"🪧 Placa: {veiculo.placa[:3]}-{veiculo.placa[-4:]}\n"
                    f"📆 Ano de Fabricação: {veiculo.anoFabricacao}\n"
                    f"📆 Ano do Modelo: {veiculo.anoModelo}\n"
                    f"🎨 Cor: {veiculo.cor}\n"
                    f"📄 RENAVAM: {veiculo.renavam or ""}\n"
                    f"🔎 Status: {veiculo.status}\n"
                    "➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖"
                )
                
                bot.send_message(message.chat.id, info_veiculo)

            bot.send_message(message.chat.id, f"Escolha uma opção:", reply_markup=menu_principal())
        finally:
            session.close()