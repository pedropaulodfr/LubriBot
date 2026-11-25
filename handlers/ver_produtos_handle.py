"""Listagem e exclusão de produtos do usuário.

Correções: o handler de confirmação era registrado **dentro** do callback a cada
clique, acumulando handlers que capturavam qualquer "Sim"/"Não" do bot inteiro.
Agora a confirmação é registrada como próximo passo daquela conversa. A exclusão
também confere o dono do produto.
"""

from __future__ import annotations

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove

from keyboards.markups_genericos_keyboard import markups_genericos_keyboard
from keyboards.menu_principal_keyboard import menu_principal
from lubribot.database.runtime import get_database
from lubribot.models import Produto, Usuario
from lubribot.utils.logging import get_logger
from services.produtos_service import get_produtos_by_usuario

logger = get_logger(__name__)


def ver_produtos_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "🔍🛢️ Ver Produtos")
    def ver_produtos(message):
        with get_database().unit_of_work(commit=False) as session:
            usuario = (
                session.query(Usuario)
                .filter(Usuario.telegram_id == message.from_user.id)
                .first()
            )
            if not usuario:
                bot.send_message(message.chat.id, "❌ Usuário não encontrado.")
                return
            usuario_id = usuario.id

        produtos = get_produtos_by_usuario(usuario_id)
        if not produtos:
            bot.send_message(
                message.chat.id,
                "⚠️ Você ainda não possui produtos registrados!",
                reply_markup=menu_principal(),
            )
            return

        bot.send_message(
            message.chat.id,
            f"{message.from_user.first_name}, aqui estão os seus produtos cadastrados:",
            reply_markup=ReplyKeyboardRemove(),
        )

        for produto in produtos:
            info_produto = (
                f"🔖 Descrição: {produto.descricao}\n"
                f"🔎 Status: {produto.status}\n"
                "➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖"
            )
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton(
                    "🗑️ Excluir Produto", callback_data=f"excluir_produto_{produto.id}"
                )
            )
            bot.send_message(message.chat.id, info_produto, reply_markup=keyboard)

        bot.send_message(message.chat.id, "Escolha uma opção:", reply_markup=menu_principal())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("excluir_produto_"))
    def callback_excluir_produto(call):
        produto_id = int(call.data.replace("excluir_produto_", ""))
        bot.answer_callback_query(call.id)

        with get_database().unit_of_work(commit=False) as session:
            usuario = (
                session.query(Usuario)
                .filter(Usuario.telegram_id == call.from_user.id)
                .first()
            )
            produto = (
                session.query(Produto)
                .filter(
                    Produto.id == produto_id,
                    Produto.usuario_id == (usuario.id if usuario else None),
                )
                .first()
            )
            if produto is None:
                bot.send_message(
                    call.message.chat.id,
                    "❌ Produto não encontrado.",
                    reply_markup=menu_principal(),
                )
                return
            usuario_id = usuario.id

        bot.send_message(
            call.message.chat.id,
            "⚠️ Tem certeza que deseja excluir este produto?",
            reply_markup=ReplyKeyboardRemove(),
        )
        opcoes = markups_genericos_keyboard(
            [{"identificacao": "Sim"}, {"identificacao": "Não"}], "identificacao"
        )
        bot.send_message(call.message.chat.id, "Escolha:", reply_markup=opcoes)
        bot.register_next_step_handler(
            call.message, confirmar_exclusao_produto, produto_id, usuario_id
        )

    def confirmar_exclusao_produto(message, produto_id: int, usuario_id: int):
        if message.text != "Sim":
            bot.send_message(
                message.chat.id,
                "❌ Exclusão cancelada.",
                reply_markup=menu_principal(),
            )
            return

        try:
            with get_database().unit_of_work() as session:
                produto = (
                    session.query(Produto)
                    .filter(Produto.id == produto_id, Produto.usuario_id == usuario_id)
                    .first()
                )
                if produto is None:
                    bot.send_message(
                        message.chat.id,
                        "❌ Produto não encontrado.",
                        reply_markup=menu_principal(),
                    )
                    return
                produto.status = "Excluido"
        except Exception:
            logger.exception("falha_ao_excluir_produto", extra={"produto_id": produto_id})
            bot.send_message(
                message.chat.id,
                "😕 Não foi possível excluir o produto agora.",
                reply_markup=menu_principal(),
            )
            return

        bot.send_message(
            message.chat.id,
            "✅ Produto excluído com sucesso!",
            reply_markup=menu_principal(),
        )
