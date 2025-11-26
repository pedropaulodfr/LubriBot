import telebot
import threading
import time
import os
from http.server import SimpleHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv, find_dotenv

# Handlers
from handlers.start_handle import start
from handlers.add_manutencao_handle import add_manutencao_handle
from handlers.add_veiculo_handle import add_veiculo_handle
from handlers.ver_veiculos_handle import ver_veiculo_handle
from handlers.ver_manutencoes_handle import ver_manutencao_handle
from handlers.gerenciar_veiculos_handle import gerenciar_veiculos_handle
from handlers.configuracoes_handle import (
    configuracoes_handle,
    configuracoes_receber_notificacoes,
    configuracoes_dias_notificacao
)
from handlers.del_veiculo_handle import del_veiculo_handle

from services.notificacoes_service import ProcessarNotificacoes, EnviaNotificacoes

# Carrega .env
load_dotenv(find_dotenv())

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

# -----------------------------
# TAREFA PERIÓDICA
# -----------------------------
def tarefa_periodica():
    while True:
        print("Executando tarefa agendada...")

        ProcessarNotificacoes()
        EnviaNotificacoes(bot)

        time.sleep(3600 * 24)  # 24h

def iniciar_tarefa_periodica():
    thread = threading.Thread(target=tarefa_periodica)
    thread.daemon = True
    thread.start()

# -----------------------------
# SERVIDOR HTTP (necessário no Render FREE)
# -----------------------------
def start_server():
    port = int(os.getenv("PORT", 10000))  # Render define $PORT
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    print(f"Servidor HTTP ativo na porta {port}")
    server.serve_forever()

# -----------------------------
# REGISTRA HANDLERS
# -----------------------------
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

# -----------------------------
# INÍCIO DO BOT
# -----------------------------
def start_bot():
    print("Bot está rodando...")
    bot.remove_webhook()
    bot.infinity_polling(timeout=30, long_polling_timeout=30)


# -----------------------------
# EXECUTAR TUDO
# -----------------------------
if __name__ == "__main__":
    # Thread do bot
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Thread da tarefa periódica
    iniciar_tarefa_periodica()

    # Processo principal → servidor HTTP
    # (Render exige que um server esteja rodando)
    start_server()
