from telebot.types import ReplyKeyboardRemove, ForceReply
from repository.models import Usuario, ManutencaoServico, Servico, _Session
from keyboards.menu_principal_keyboard import menu_principal
from services.manutencoes_service import get_manutencoes_by_usuario

session = _Session()

def ver_manutencao_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "Ver Manutenções")
    def ver_manutencao(message):
        try:
            usuario = session.query(Usuario).filter(Usuario.telegram_id == message.from_user.id).first()
            
            if not usuario:
                bot.send_message(message.chat.id, "❌ Usuário não encontrado.")
                return

            manutencoes = get_manutencoes_by_usuario(usuario.id)

            bot.send_message(message.chat.id, f"{usuario.primeiroNome}, aqui estão as suas manutenções registradas:", reply_markup=ReplyKeyboardRemove())

            for manutencao in manutencoes:
                manutencao_servicos = session.query(ManutencaoServico).join(Servico).filter(ManutencaoServico.manutencao_id == manutencao.id).first()
                info_manutencao = (
                    f"🚘 Veículo: {manutencao.veiculo.tipo} {manutencao.veiculo.fabricante} {manutencao.veiculo.modelo} {manutencao.veiculo.cor} - {manutencao.veiculo.anoModelo} ({manutencao.veiculo.placa[:3]}-{manutencao.veiculo.placa[-4:]})\n"
                    f"📅 Data: {manutencao.data.strftime('%d/%m/%Y')}\n"
                    f"🔧 Serviço: {manutencao_servicos.servico.descricao}\n"
                    f"💲 Custo: R$ {manutencao.custo:.2f}\n"
                )
                bot.send_message(message.chat.id, info_manutencao) 

            bot.send_message(message.chat.id, f"Escolha uma opção:", reply_markup=menu_principal())

        finally:
            session.close()
