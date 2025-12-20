import os, datetime
import google.generativeai as genai

from telebot.types import ReplyKeyboardRemove,  InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv, find_dotenv
from repository.models import Usuario, VeiculoDica, Veiculo, _Session
from services.veiculos_service import get_veiculos_by_usuario
from keyboards.menu_principal_keyboard import menu_principal
from keyboards.veiculos_keyboard import veiculos_keyboard
from prompts.dicas_prompt import get_dica_maintenance_prompt
from utils.envio_mensagem import send_and_delete


# carrega .env (se existir)
load_dotenv(find_dotenv())

session = _Session()

genai.configure(api_key=os.getenv("GEMINI_ApiKey"))
modelo = genai.GenerativeModel("gemini-2.5-flash")


def ver_dica_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "💡 Dicas")
    def ver_dica(message):

        usuario = session.query(Usuario).filter(Usuario.telegram_id == message.from_user.id).first()
        if not usuario:
            send_and_delete(bot, message.chat.id, "❌ Usuário não encontrado.")
            send_and_delete(bot, message.chat.id, f"🔄 Clique em /start para tentar novamente.")
            return
        
        veiculos = get_veiculos_by_usuario(usuario.id)
        if not veiculos:
            send_and_delete(bot, message.chat.id, "❌ Nenhum veículo encontrado. Por favor, adicione um veículo primeiro.")
            bot.send_message(message.chat.id, f"Escolha uma opção:", reply_markup=menu_principal())
            return
        
        veiculos_opcoes = veiculos_keyboard(veiculos)

        bot.send_message(message.chat.id, "Selecione um veículo: ", reply_markup=veiculos_opcoes)
        bot.register_next_step_handler(message, receber_veiculo)


    def receber_veiculo(message):
        if (message.text == "❌ Cancelar"):
            bot.send_message(message.chat.id, "Solicitação de dica cancelada.", reply_markup=menu_principal())
            return
        
        veiculo = message.text.split(" - ")[1]
        processar_enviar_dica(message, veiculo)
        
        
    def processar_enviar_dica(message, veiculo):
        placa = message.text.split(" - ")[0]
        placa = placa.replace("-", "")

        usuario = session.query(Usuario).filter(Usuario.telegram_id == message.from_user.id).first()
        dica = session.query(VeiculoDica).join(Veiculo).filter(Veiculo.placa == placa, Veiculo.usuario_id == usuario.id).first()

        if (dica and dica.datacriacao <= (datetime.date.today() + datetime.timedelta(days=30))):
            bot.send_message(message.chat.id, dica.texto, reply_markup=menu_principal())
            return
        else:
            send_and_delete(bot, message.chat.id, "🧠 Gerando dica personalizada para o seu veículo. Por favor, aguarde...", delay=60)

        try:
            resposta = modelo.generate_content(get_dica_maintenance_prompt(veiculo))

            veiculo_id = session.query(Veiculo).filter(Veiculo.placa == placa, Veiculo.usuario_id == usuario.id).first().id
            if (not dica):
                dica = VeiculoDica(
                    veiculo_id = veiculo_id,
                    texto = resposta.text,
                    datacriacao = datetime.date.today()
                )
                session.add(dica)
            else:
                dica.texto = resposta.text
                dica.datacriacao = datetime.date.today()
            session.commit()

            bot.send_message(message.chat.id, resposta.text, reply_markup=menu_principal())        
        except:
            send_and_delete(bot, message.chat.id, "😕 Ocorreu um erro ao tentar gerar dica. Por favor, tente novamente!", reply_markup=menu_principal())        
