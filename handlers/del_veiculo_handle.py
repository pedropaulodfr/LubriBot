from repository.models import Usuario, Manutencao, Veiculo, _Session
from keyboards.menu_principal_keyboard import menu_principal
from keyboards.veiculos_keyboard import veiculos_keyboard
from services.veiculos_service import get_veiculos_by_usuario


session = _Session()
veiculo = Veiculo()

def del_veiculo_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "➖ Remover Veículo")
    def del_veiculo(message):
        usuario = session.query(Usuario).filter(Usuario.telegram_id == message.from_user.id).first()
        
        if not usuario:
            bot.send_message(message.chat.id, "❌ Usuário não encontrado.")
            return
        
        veiculos_usuario = get_veiculos_by_usuario(usuario.id)
        veiculos_opcoes = veiculos_keyboard(veiculos_usuario)

        bot.send_message(message.chat.id, "Selecione um veículo para deletar: ", reply_markup=veiculos_opcoes)
        bot.register_next_step_handler(message, receber_veiculo)

    def receber_veiculo(message):
        if (message.text == "❌ Cancelar"):
            bot.send_message(message.chat.id, "Operação de exclusão de veículo cancelada.", reply_markup=menu_principal())
            return
            
        placa_selecionada = message.text.split(" - ")[0].replace("-", "")
        veiculo = session.query(Veiculo).filter(Veiculo.placa == placa_selecionada).first()

        if not veiculo:
            bot.send_message(message.chat.id, "❌ Veículo não encontrado. Por favor, selecione um veículo válido.")
            bot.register_next_step_handler(message, receber_veiculo)
            return
        
        veiculo.status = "Deletado"

        bot.send_message(message.chat.id, "⏳ Removendo veículo...")
        finalizar_remocao(message)

    def finalizar_remocao(message):
        session.commit()
        session.close()

        bot.send_message(message.chat.id, f"✅ Veículo removido com sucesso.", reply_markup=menu_principal())
