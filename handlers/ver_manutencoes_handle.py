import os

from telebot.types import ReplyKeyboardRemove,  InlineKeyboardMarkup, InlineKeyboardButton
from repository.models import Usuario, Manutencao, ManutencaoServico, Servico, _Session
from keyboards.menu_principal_keyboard import menu_principal
from services.manutencoes_service import get_manutencoes_by_usuario
from dotenv import load_dotenv, find_dotenv

# carrega .env (se existir)
load_dotenv(find_dotenv())

session = _Session()

AWS = {
    "Region": os.getenv("AWS_Region"),
    "BucketName": os.getenv("AWS_BucketName"),
}

REGION = AWS["Region"]
BUCKET_NAME = AWS["BucketName"]

def ver_manutencao_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "🔎 Ver Manutenções")
    def ver_manutencao(message):
        try:
            usuario = session.query(Usuario).filter(Usuario.telegram_id == message.from_user.id).first()
            
            if not usuario:
                bot.send_message(message.chat.id, "❌ Usuário não encontrado.")
                return

            manutencoes = get_manutencoes_by_usuario(usuario.id)

            if (len(manutencoes) == 0):
                bot.send_message(message.chat.id, f"⚠️ Você ainda não veículos com manutenções registradas!", reply_markup=menu_principal())
                return

            bot.send_message(message.chat.id, f"{usuario.primeiroNome}, aqui estão as suas manutenções registradas:", reply_markup=ReplyKeyboardRemove())

            for manutencao in manutencoes:
                manutencao_servicos = session.query(ManutencaoServico).join(Servico).filter(ManutencaoServico.manutencao_id == manutencao.id).first()
                info_manutencao = (
                    f"🚘 Veículo: {manutencao.veiculo.tipo} {manutencao.veiculo.fabricante} {manutencao.veiculo.modelo} {manutencao.veiculo.cor} - {manutencao.veiculo.anoModelo} ({manutencao.veiculo.placa[:3]}-{manutencao.veiculo.placa[-4:]})\n"
                    f"📅 Data: {manutencao.data.strftime('%d/%m/%Y')}\n"
                    f"🔧 Serviço: {manutencao_servicos.servico.descricao}\n"
                    f"💲 Custo: R$ {manutencao.custo:.2f}\n"
                )

                if (manutencao.imagem and manutencao.imagem != ""):
                    keyboard = InlineKeyboardMarkup()
                    keyboard.add(
                        InlineKeyboardButton("📷 Ver imagem", callback_data=f"ver_img_{manutencao.id}")
                    )

                    bot.send_message(message.chat.id, info_manutencao, reply_markup=keyboard)
                else:
                    bot.send_message(message.chat.id, info_manutencao)

            bot.send_message(message.chat.id, f"Escolha uma opção:", reply_markup=menu_principal())

        finally:
            session.close()

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ver_img_"))
    def callback_ver_imagem(call):
        manutencao_id = int(call.data.replace("ver_img_", ""))

        session = _Session()
        try:
            manutencao = session.query(Manutencao).filter(Manutencao.id == manutencao_id).first()

            if not manutencao or not manutencao.imagem:
                bot.answer_callback_query(call.id, "❌ Nenhuma imagem encontrada.")
                return

            # Envia a foto salva (file_id)
            bot.send_photo(call.message.chat.id, f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/uploads/imagens/{manutencao.imagem}")

            bot.answer_callback_query(call.id)

        finally:
            session.close()