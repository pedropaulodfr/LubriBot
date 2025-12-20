from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# Estado global por usuário (cada chat tem seu próprio fluxo)
CHECKBOX_STATE = {}

def start_checkbox(bot, message, options, on_finish, text="Selecione as opções:"):
    chat_id = message if isinstance(message, int) else message.chat.id
    """
    Inicia um fluxo de 'checkbox' para um usuário.
    - options: lista de strings
    - on_finish: função callback(chat_id, selecionados)
    """

    # Salva o estado inicial
    CHECKBOX_STATE[chat_id] = {
        "options": options,
        "selected": set(),
        "callback": on_finish,
        "message_id": None,
        "text": text
    }

    # Envia mensagem inicial
    msg = bot.send_message(chat_id, text, reply_markup=_make_checkbox_markup(chat_id))
    CHECKBOX_STATE[chat_id]["message_id"] = msg.message_id


def _make_checkbox_markup(chat_id):
    """Gera o teclado inline do checkbox para um chat específico."""
    data = CHECKBOX_STATE[chat_id]
    options = data["options"]
    selected = data["selected"]

    markup = InlineKeyboardMarkup()

    for opt in options:
        marcado = "☑" if opt in selected else "☐"
        markup.row(
            InlineKeyboardButton(f"{marcado} {opt}", callback_data=f"cb:{opt}")
        )

    markup.row(
        InlineKeyboardButton("✅ Confirmar", callback_data="cb:confirmar")
    )

    return markup


def register_checkbox_handlers(bot):
    """
    Registra um handler universal que processa todos os checkboxes.
    Isso permite múltiplos usuários simultâneos sem travar nada.
    """

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cb:"))
    def checkbox_callback(call):
        chat_id = call.message.chat.id
        if chat_id not in CHECKBOX_STATE:
            bot.answer_callback_query(call.id)
            return

        state = CHECKBOX_STATE[chat_id]

        # Verifica se é o mesmo message_id para evitar interferência entre fluxos
        if call.message.message_id != state["message_id"]:
            bot.answer_callback_query(call.id)
            return

        data = call.data.replace("cb:", "")

        # CONFIRMAR -------------------------------------------------------
        if data == "confirmar":
            selecionados = list(state["selected"])

            # Edita mensagem final
            resultado = ", ".join(selecionados) if selecionados else "Nenhum"
            bot.edit_message_text(
                f"{state['text']}\n\nSelecionado: {resultado}",
                chat_id,
                state["message_id"]
            )

            # Executa callback do usuário
            callback_fn = state["callback"]
            del CHECKBOX_STATE[chat_id]  # limpa memória

            callback_fn(chat_id, selecionados)
            bot.answer_callback_query(call.id)
            return

        # TOGGLE ----------------------------------------------------------
        else:
            if data in state["selected"]:
                state["selected"].remove(data)
            else:
                state["selected"].add(data)

            # Atualiza apenas o teclado
            bot.edit_message_reply_markup(
                chat_id,
                state["message_id"],
                reply_markup=_make_checkbox_markup(chat_id)
            )
            bot.answer_callback_query(call.id)
