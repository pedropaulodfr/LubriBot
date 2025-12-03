from telebot.types import ReplyKeyboardRemove, ForceReply
from repository.models import Usuario, Veiculo, _Session
from keyboards.tipos_veiculos_keyboard import tipos_veiculos_keyboard
from keyboards.menu_principal_keyboard import menu_principal
from keyboards.modelos_veiculos_keyboard import modelos_veiculos_keyboard
from services.vpic_service import get_modelos_por_marca_ano

session = _Session()
veiculo = Veiculo()
usuario = Usuario()

def add_veiculo_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "➕ Adicionar Veículo")
    def add_veiculo(message):
        bot.send_message(message.chat.id,"Iniciando o processo de registro de veículo. Por favor, preencha as informações.", reply_markup=ReplyKeyboardRemove())

        usuario = session.query(Usuario).filter(Usuario.telegram_id == message.from_user.id).first()
        if not usuario:
            bot.send_message(message.chat.id, "❌ Usuário não encontrado.")
            return

        veiculo.usuario_id = usuario.id
        veiculo.status = "Ativo"
        

        bot.send_message(message.chat.id, "Informe a placa:", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_placa)
    

    def receber_placa(message):
        placa = message.text.replace("-", "")

        if len(placa) != 7:
            bot.send_message(message.chat.id, "❌ Placa inválida! Por favor, envie uma placa válida", reply_markup=ForceReply())
            bot.register_next_step_handler(message, receber_placa)
            return
        
        existeVeiculo = session.query(Veiculo).filter(Veiculo.placa == placa.upper(), Veiculo.usuario_id == veiculo.usuario_id, Veiculo.status != "Deletado").first()
        if (existeVeiculo):
            bot.send_message(message.chat.id, "❌ Placa já cadastrada! Por favor, envie uma placa diferente.", reply_markup=ForceReply())
            bot.register_next_step_handler(message, receber_placa)
            return
        
        veiculo.placa = placa.upper()

        bot.send_message(message.chat.id, "Selecione o tipo", reply_markup=tipos_veiculos_keyboard())
        bot.register_next_step_handler(message, receber_tipo)


    def receber_tipo(message):
        tipo = message.text

        if (tipo == "Cancelar"):
            bot.send_message(message.chat.id, "Operação de adição de veículo cancelada.", reply_markup=menu_principal())
            return

        veiculo.tipo = tipo

        bot.send_message(message.chat.id, "Informe a marca:", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_fabricante)


    def receber_fabricante(message):
        fabricante = message.text
        veiculo.fabricante = fabricante

        modelos_veiculos = get_modelos_por_marca_ano(marca=fabricante, tipo_veiculo=veiculo.tipo)

        if(len(modelos_veiculos) > 0):
            bot.send_message(message.chat.id, "Selecione ou insira o modelo:", reply_markup=modelos_veiculos_keyboard(modelos_veiculos))
            bot.register_next_step_handler(message, receber_modelo)
        else:
            bot.send_message(message.chat.id, "Insira o modelo:", reply_markup=ForceReply())
            bot.register_next_step_handler(message, receber_modelo_manualmente)
        

    def receber_modelo(message):
        modelo = message.text

        if (modelo == "❌ Cancelar"):
            bot.send_message(message.chat.id, "❌ Operação de adição de veículo cancelada.", reply_markup=menu_principal())
            return
        elif (modelo == "⌨️ Inserir manualmente:"):
            bot.send_message(message.chat.id, "Insira o modelo:", reply_markup=ForceReply())
            bot.register_next_step_handler(message, receber_modelo_manualmente)
        else:
            veiculo.modelo = modelo
            bot.send_message(message.chat.id, "Informe a cor:", reply_markup=ForceReply())
            bot.register_next_step_handler(message, receber_cor)


    def receber_modelo_manualmente(message):
        veiculo.modelo = message.text
        bot.send_message(message.chat.id, "Informe a cor:", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_cor)


    def receber_cor(message):
        cor = message.text
        veiculo.cor = cor

        bot.send_message(message.chat.id, "Informe o ano de fabricação:", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_ano_fabricacao)


    def receber_ano_fabricacao(message):
        ano_fabricacao = message.text

        if len(ano_fabricacao) != 4:
            bot.send_message(message.chat.id, "❌ Ano inválido! Por favor, informe um ano válido com 4 dígitos. Ex: 2026")
            bot.register_next_step_handler(message, receber_ano_fabricacao)
            return
        
        veiculo.anoFabricacao = ano_fabricacao

        bot.send_message(message.chat.id, "Informe o ano do modelo:", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_ano_modelo)


    def receber_ano_modelo(message):
        ano_modelo = message.text

        if len(ano_modelo) != 4:
            bot.send_message(message.chat.id, "❌ Ano inválido! Por favor, informe um ano válido com 4 dígitos. Ex: 2026")
            bot.register_next_step_handler(message, receber_ano_modelo)
            return
        
        veiculo.anoModelo = ano_modelo

        bot.send_message(message.chat.id, "Informe o RENAVAM: (Opcional)", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_renavam)
    

    def receber_renavam(message):
        renavam = message.text if message.text != "." else None
        veiculo.renavam = renavam

        bot.send_message(message.chat.id, "⏳ Registrando veículo...")
        finalizar_registro(message)


    def finalizar_registro(message):
        session.add(veiculo)
        session.commit()
        session.close()
        bot.send_message(message.chat.id, "✅ Veículo registrado com sucesso!")
        bot.send_message(message.chat.id, f"Escolha uma opção:", reply_markup=menu_principal())