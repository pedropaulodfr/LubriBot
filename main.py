import telebot
import threading
import time
from config import TOKEN
from handlers.start_handle import start
from handlers.add_manutencao_handle import add_manutencao_handle
from handlers.add_veiculo_handle import add_veiculo_handle
from handlers.ver_veiculos_handle import ver_veiculo_handle
from handlers.ver_manutencoes_handle import ver_manutencao_handle
from handlers.gerenciar_veiculos_handle import gerenciar_veiculos_handle
from handlers.configuracoes_handle import configuracoes_handle, configuracoes_receber_notificacoes, configuracoes_dias_notificacao
from handlers.del_veiculo_handle import del_veiculo_handle
from services.notificacoes_service import ProcessarNotificacoes, EnviaNotificacoes

bot = telebot.TeleBot(TOKEN)

def tarefa_periodica():
    while True:
        print("Executando tarefa agendada...")

        # ➜ CHAME A FUNÇÃO QUE VOCÊ QUER EXECUTAR
        ProcessarNotificacoes()

        EnviaNotificacoes(bot)

        time.sleep(3600 * 24)

def iniciar_tarefa_periodica():
    thread = threading.Thread(target=tarefa_periodica)
    thread.daemon = True  # thread fecha junto com o programa
    thread.start()


# Registrar handlers
start(bot)
add_manutencao_handle(bot)
ver_manutencao_handle(bot)
add_veiculo_handle(bot)
ver_veiculo_handle(bot)
del_veiculo_handle(bot)
gerenciar_veiculos_handle(bot)
configuracoes_handle(bot)
configuracoes_receber_notificacoes(bot)
configuracoes_dias_notificacao(bot)

if __name__ == "__main__":
    print("Bot está rodando...")

    iniciar_tarefa_periodica()  # inicia a função que roda a cada 60 min

    bot.remove_webhook()
    bot.infinity_polling()