import threading
import time

def send_and_delete(bot, chat_id, text, delay=30):
    msg = bot.send_message(chat_id, text)

    def delete_later():
        time.sleep(delay)
        try:
            bot.delete_message(chat_id, msg.message_id)
        except Exception:
            pass  # mensagem já apagada ou sem permissão

    threading.Thread(target=delete_later, daemon=True).start()
