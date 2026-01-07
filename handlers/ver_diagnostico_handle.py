import os, datetime
import google.generativeai as genai

from telebot.types import ReplyKeyboardRemove,  InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from dotenv import load_dotenv, find_dotenv
from repository.models import Usuario, VeiculoDiagnosticos, Veiculo, _Session
from services.veiculos_service import get_veiculos_by_usuario
from keyboards.menu_principal_keyboard import menu_principal
from keyboards.veiculos_keyboard import veiculos_keyboard
from keyboards.markups_genericos_keyboard import markups_genericos_keyboard
from prompts.diagnosticos_prompt import get_diagnostico_prompt
from utils.envio_mensagem import send_and_delete


# carrega .env (se existir)
load_dotenv(find_dotenv())

session = _Session()
diagnostico = VeiculoDiagnosticos()
veiculo = Veiculo()

genai.configure(api_key=os.getenv("GEMINI_ApiKey"))
modelo = genai.GenerativeModel("gemini-2.5-flash")


def ver_diagnostico_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "⚠️ Diagnósticos")
    def ver_diagnostico(message):
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
            bot.send_message(message.chat.id, "Solicitação de diagnóstico cancelada.", reply_markup=menu_principal())
            return
        
        veiculo.placa = message.text.split(" - ")[0]
        veiculo.modelo = message.text.split(" - ")[1]

        bot.send_message(message.chat.id, "Relate o problema do veículo: ", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_problema)

    
    def receber_problema(message):
        if (message.text == "❌ Cancelar"):
            bot.send_message(message.chat.id, "Solicitação de diagnóstico cancelada.", reply_markup=menu_principal())
            return
        
        problema = message.text
        processar_enviar_diagnostico(message, problema)

    
    def processar_enviar_diagnostico(message, problema):
        placa = veiculo.placa.replace("-", "")

        usuario = session.query(Usuario).filter(Usuario.telegram_id == message.from_user.id).first()
        veiculo.id = session.query(Veiculo).filter(Veiculo.placa == placa, Veiculo.usuario_id == usuario.id).first().id
        
        send_and_delete(bot, message.chat.id, "🧠 Diagnosticando o problema do seu veículo. Por favor, aguarde...", delay=60)

        try:
            resposta = modelo.generate_content(get_diagnostico_prompt(veiculo.modelo, problema))

            diagnostico.veiculo_id = veiculo.id,
            diagnostico.problema = problema,
            diagnostico.diagnostico = resposta.text,
            diagnostico.datacriacao = datetime.date.today()
        
            bot.send_message(message.chat.id, resposta.text, reply_markup=menu_principal(), parse_mode='HTML')

            informar_resolucao = markups_genericos_keyboard([
                {'identificacao': '✅ Sim'},
                {'identificacao': '❌ Não'}
            ], "identificacao")
            bot.send_message(message.chat.id, "O seu problema foi resolvido?", reply_markup=informar_resolucao)
            bot.register_next_step_handler(message, receber_resolucao)
        except:
            send_and_delete(bot, message.chat.id, "😕 Ocorreu um erro ao tentar procurar um diagnóstico. Por favor, tente novamente!", reply_markup=menu_principal())      

    def receber_resolucao(message):
        if (message.text == "✅ Sim"):
            diagnostico.resolvido = True
            bot.send_message(message.chat.id, "✅ Que ótimo! Fico feliz em ajudar.", reply_markup=menu_principal())
        elif (message.text == "❌ Não"):
            diagnostico.resolvido = False
            bot.send_message(message.chat.id, "❌ Sinto muito por não ter ajudado. Recomendo procurar um mecânico de confiança para uma avaliação mais detalhada.", reply_markup=menu_principal())
        else:
            bot.send_message(message.chat.id, "❌ Opção inválida. Por favor, tente novamente.", reply_markup=menu_principal())
            return

        session.add(diagnostico)
        session.commit()