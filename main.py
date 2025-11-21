import telebot
from config import TOKEN
from handlers.start_handle import start
from handlers.add_manutencao_handle import add_manutencao_handle
from handlers.add_veiculo_handle import add_veiculo_handle
from handlers.ver_veiculos_handle import ver_veiculo_handle
from handlers.ver_manutencoes_handle import ver_manutencao_handle
from handlers.gerenciar_veiculos_handle import gerenciar_veiculos_handle
from handlers.del_veiculo_handle import del_veiculo_handle

bot = telebot.TeleBot(TOKEN)

# Registrar handlers
start(bot)
add_manutencao_handle(bot)
ver_manutencao_handle(bot)
add_veiculo_handle(bot)
ver_veiculo_handle(bot)
del_veiculo_handle(bot)
gerenciar_veiculos_handle(bot)

print("Bot está rodando...")
bot.remove_webhook()
bot.infinity_polling()