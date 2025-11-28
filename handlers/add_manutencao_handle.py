import base64 as b64
from datetime import datetime
from telebot.types import ReplyKeyboardRemove, ForceReply
from repository.models import Usuario, Manutencao, ManutencaoServico, Veiculo, _Session
from services.veiculos_service import get_veiculos_by_usuario
from keyboards.menu_principal_keyboard import menu_principal
from keyboards.markups_genericos_keyboard import markups_genericos_keyboard
from keyboards.veiculos_keyboard import veiculos_keyboard
from services.servicos_service import get_all_servicos, get_servico_by_descricao
from utils.upload_file_async import upload


session = _Session()
manutencao = Manutencao()
manutencaoServico = ManutencaoServico()

servicos_disponiveis = get_all_servicos()


def add_manutencao_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "🛠️ Registrar Manutenção")
    def add_manutencao(message):
        bot.send_message(message.chat.id,"Iniciando o processo de registro de manutenção. Por favor, envie os detalhes da manutenção.",reply_markup=ReplyKeyboardRemove())
        # Aqui você pode adicionar lógica adicional para processar a manutenção

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

        manutencao.status = "Finalizada"

        veiculos_opcoes = veiculos_keyboard(veiculos)

        bot.send_message(message.chat.id, "Selecione um Veículo para manutenção: ", reply_markup=veiculos_opcoes)
        bot.register_next_step_handler(message, receber_veiculo)


    def receber_veiculo(message):
        if (message.text == "❌ Cancelar"):
            bot.send_message(message.chat.id, "Registro de manutenção cancelado.", reply_markup=menu_principal())
            return
        
        placa_selecionada = message.text.split(" - ")[0].replace("-", "")
        veiculo = session.query(Veiculo).filter(Veiculo.placa == placa_selecionada).first()

        if not veiculo:
            bot.send_message(message.chat.id, "❌ Veículo não encontrado. Por favor, selecione um veículo válido.")
            bot.register_next_step_handler(message, receber_veiculo)
            return

        manutencao.veiculo_id = veiculo.id

        data_opcoes = markups_genericos_keyboard([
            {'identificacao': 'Hoje'},
            {'identificacao': 'Outra Data'}
        ], "identificacao")
        bot.send_message(message.chat.id, "Data da manutenção:", reply_markup=data_opcoes)
        bot.register_next_step_handler(message, receber_opcao_data)


    def receber_opcao_data(message):
        # Se o usuário escolher "Hoje", processamos imediatamente.
        if message.text == "Hoje":
            receber_data(message)
            return

        # Caso contrário, pedimos que informe a data e registramos o próximo passo.
        bot.send_message(message.chat.id, "Informe a data da manutenção (DD/MM/AAAA):", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_data)


    def receber_data(message):
        data_texto = message.text

        if data_texto == "Hoje":
            manutencao.data = datetime.now().strftime("%Y-%m-%d")
        else:
            manutencao.data = datetime.strptime(data_texto, "%d/%m/%Y").strftime("%Y-%m-%d")

        servicos_opcoes = markups_genericos_keyboard(servicos_disponiveis, "descricao")
        bot.send_message(message.chat.id, "Descreva o serviço realizado:", reply_markup=servicos_opcoes)
        bot.register_next_step_handler(message, receber_servico)


    def receber_servico(message):
        descricao_servico = message.text

        manutencaoServico.servico_id = get_servico_by_descricao(descricao_servico).id

        bot.send_message(message.chat.id, "Informe a quilometragem do veículo: (em KM):", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_quilometragem)


    def receber_quilometragem(message):
        km_texto = message.text
        try:
            km = int(km_texto)
            manutencao.km = km
        except ValueError:
            bot.send_message(message.chat.id, "❌ Formato de quilometragem inválido. Por favor, informe um valor numérico.")
            bot.register_next_step_handler(message, receber_quilometragem)
            return

        bot.send_message(message.chat.id, "Por favor, tire uma foto do painel mostrando a quilometragem:", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_foto)


    def receber_foto(message):
        if message.content_type != 'photo':
            bot.send_message(message.chat.id, "❌ Por favor, envie uma foto válida.")
            bot.register_next_step_handler(message, receber_foto)
            return

        foto_arquivo_id = message.photo[-1].file_id
        manutencao.imagem = foto_arquivo_id

        # Obtém informações sobre o arquivo (incluindo o file_path)
        file_info = bot.get_file(foto_arquivo_id)
        file_path = file_info.file_path

        # Baixa o arquivo usando a API do Telegram
        # bot.download_file retorna o conteúdo do arquivo em bytes
        downloaded_file = bot.download_file(file_path)

        upload(base64=b64.b64encode(downloaded_file).decode('utf-8'), tipo="imagens", filename=f"{foto_arquivo_id}.jpg")

        bot.send_message(message.chat.id, "Informe o custo do serviço (em R$):", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_custo)  


    def receber_custo(message):
        custo_texto = message.text
        try:
            custo = float(custo_texto.replace(",", "."))
            manutencao.custo = custo
        except ValueError:
            bot.send_message(message.chat.id, "❌ Formato de custo inválido. Por favor, informe um valor numérico.")
            bot.register_next_step_handler(message, receber_custo)
            return

        bot.send_message(message.chat.id, "Alguma observação a ser feita? (Opcional)", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_obervacoes)

    def receber_obervacoes(message):
        observacoes_texto = message.text
        manutencao.observacao = observacoes_texto if observacoes_texto != "." else None
        
        bot.send_message(message.chat.id, "⏳ Gravando Manutenção...")
        finalizar_registro(message)
        

    def finalizar_registro(message):
        session.add(manutencao)
        session.commit()

        manutencaoServico.manutencao_id = manutencao.id
        session.add(manutencaoServico)
        session.commit()

        bot.send_message(message.chat.id, "✅ Manutenção registrada com sucesso!")
        bot.send_message(message.chat.id, f"Escolha uma opção:", reply_markup=menu_principal())

