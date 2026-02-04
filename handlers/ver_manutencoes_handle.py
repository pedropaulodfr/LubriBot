import os

from telebot.types import ReplyKeyboardRemove,  InlineKeyboardMarkup, InlineKeyboardButton
from repository.models import Usuario, Manutencao, ManutencaoServico, ManutencaoProduto, Produto, Servico, Veiculo, _Session
from keyboards.menu_principal_keyboard import menu_principal
from keyboards.markups_genericos_keyboard import markups_genericos_keyboard
from keyboards.veiculos_keyboard import veiculos_keyboard
from services.manutencoes_service import get_manutencoes_by_usuario, get_manutencoes_by_veiculos
from services.veiculos_service import get_veiculos_by_usuario
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
    def tipo_manutencao(message):
        manutencao_opoes = markups_genericos_keyboard([
            {'identificacao': '🚗 Ver por veículo'},
            {'identificacao': '📑 Ver todas'},
        ], "identificacao")

        bot.send_message(message.chat.id, "Deseja ver todas as manutenções ou somente as de um veículo específico?", reply_markup=manutencao_opoes)
        bot.register_next_step_handler(message, receber_tipo_manutencao)

    
    def receber_tipo_manutencao(message):
        tipo_manutencao_escolhida = message.text

        if tipo_manutencao_escolhida == "🚗 Ver por veículo":
            usuario = session.query(Usuario).filter(Usuario.telegram_id == message.from_user.id).first()
            if not usuario:
                bot.send_message(message.chat.id, "❌ Usuário não encontrado.")
                bot.send_message(message.chat.id, f"🔄 Clique em /start para tentar novamente.")
                return

            veiculos = get_veiculos_by_usuario(usuario.id)
            if not veiculos:
                bot.send_message(message.chat.id, "❌ Nenhum veículo encontrado. Por favor, adicione um veículo primeiro.")
                bot.send_message(message.chat.id, f"Escolha uma opção:", reply_markup=menu_principal())
                return

            veiculos_opcoes = veiculos_keyboard(veiculos)

            bot.send_message(message.chat.id, "Selecione um Veículo: ", reply_markup=veiculos_opcoes)
            bot.register_next_step_handler(message, receber_veiculo)
        else:
            ver_manutencao(message, tipo_manutencao_escolhida)


    def receber_veiculo(message):
        if (message.text == "❌ Cancelar"):
            bot.send_message(message.chat.id, "Visualização de manutenção cancelada.", reply_markup=menu_principal())
            return
        
        placa_selecionada = message.text.split(" - ")[0].replace("-", "")
        veiculo = session.query(Veiculo).filter(Veiculo.placa == placa_selecionada).first()

        if not veiculo:
            bot.send_message(message.chat.id, "❌ Veículo não encontrado. Por favor, selecione um veículo válido.")
            bot.register_next_step_handler(message, ver_manutencao)
            return

        ver_manutencao(message, "🚗 Ver por veículo", veiculo.id)

    def ver_manutencao(message, tipo, veiculo_id=None):
        try:
            usuario = session.query(Usuario).filter(Usuario.telegram_id == message.from_user.id).first()
            
            if not usuario:
                bot.send_message(message.chat.id, "❌ Usuário não encontrado.")
                return

            if (tipo == "🚗 Ver por veículo"):
                manutencoes = get_manutencoes_by_veiculos(veiculo_id)
            else:
                manutencoes = get_manutencoes_by_usuario(usuario.id)

            if (len(manutencoes) == 0):
                bot.send_message(
                    message.chat.id, 
                    "⚠️ Você ainda não tem manutenções registradas para este veículo!" if tipo == "🚗 Ver por veículo" else f"⚠️ Você ainda não tem veículos com manutenções registradas!", 
                    reply_markup=menu_principal()
                )
                return

            bot.send_message(
                message.chat.id, 
                f"{message.from_user.first_name}, aqui estão as suas manutenções registradas {' para este veículo' if tipo == '🚗 Ver por veículo' else ''}:", 
                reply_markup=ReplyKeyboardRemove()
            )

            for manutencao in manutencoes:
                manutencao_produtos = session.query(ManutencaoProduto).join(Produto).filter(ManutencaoProduto.manutencao_id == manutencao.id).all()
                manutencao_servicos = session.query(ManutencaoServico).join(Servico).filter(ManutencaoServico.manutencao_id == manutencao.id).first()

                produtos_descricoes = ", ".join([mp.produto.descricao for mp in manutencao_produtos]) if manutencao_produtos else "—"
                
                info_manutencao = (
                    f"🚘 Veículo: {manutencao.veiculo.tipo} {manutencao.veiculo.fabricante} {manutencao.veiculo.modelo} {manutencao.veiculo.cor} - {manutencao.veiculo.anoModelo} ({manutencao.veiculo.placa[:3]}-{manutencao.veiculo.placa[-4:]})\n"
                    f"📅 Data: {manutencao.data.strftime('%d/%m/%Y')}\n"
                    f"🔧 Serviço: {manutencao_servicos.servico.descricao}\n"
                    f"🛢️ Produtos: {produtos_descricoes}\n"
                    f"💲 Custo: R$ {manutencao.custo:.2f}\n"
                    f"📝 Observações: {manutencao.observacao if manutencao.observacao else '—'}"
                )

                keyboard = InlineKeyboardMarkup()
                if (manutencao.imagem and manutencao.imagem != ""):
                    keyboard.add(
                        InlineKeyboardButton("📷 Ver imagem", callback_data=f"ver_img_{manutencao.id}")
                    )
            
                    if manutencao.imagemNotaServico and manutencao.imagemNotaServico != "":
                        keyboard.add(
                            InlineKeyboardButton("📄 Ver nota de serviço/recibo", callback_data=f"ver_img_nota_servico_{manutencao.id}")
                        )

                    bot.send_message(message.chat.id, info_manutencao, reply_markup=keyboard)
                else:
                    bot.send_message(message.chat.id, info_manutencao)

            bot.send_message(message.chat.id, f"Escolha uma opção:", reply_markup=menu_principal())

        finally:
            session.close()

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ver_img_") and not call.data.startswith("ver_img_nota_servico_"))
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
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("ver_img_nota_servico_"))
    def callback_ver_imagem_nota_servico(call):
        manutencao_id = int(call.data.replace("ver_img_nota_servico_", ""))

        session = _Session()
        try:
            manutencao = session.query(Manutencao).filter(Manutencao.id == manutencao_id).first()

            if not manutencao or not manutencao.imagemNotaServico:
                bot.answer_callback_query(call.id, "❌ Nenhuma imagem encontrada.")
                return

            # Envia a foto salva (file_id)
            bot.send_photo(call.message.chat.id, f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/uploads/imagens/{manutencao.imagemNotaServico}")

            bot.answer_callback_query(call.id)

        finally:
            session.close()