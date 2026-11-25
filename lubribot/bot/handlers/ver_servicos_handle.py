"""Listagem e exclusão de serviços do usuário.

Mesmas correções aplicadas em ``ver_produtos_handle``: sem registro dinâmico de
handler de confirmação e com verificação de dono na exclusão.
"""

from __future__ import annotations

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove

from lubribot.bot.keyboards.markups_genericos_keyboard import markups_genericos_keyboard
from lubribot.bot.keyboards.menu_principal_keyboard import menu_principal
from lubribot.database.runtime import get_database
from lubribot.models import Servico, Usuario
from lubribot.utils.logging import get_logger
from services.servicos_service import get_servicos_by_usuario

logger = get_logger(__name__)


def ver_servicos_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "🔍🧰 Ver Serviços")
    def ver_servicos(message):
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

        servicos = get_servicos_by_usuario(usuario_id)
        if not servicos:
            bot.send_message(
                message.chat.id,
                "⚠️ Você ainda não possui serviços registrados!",
                reply_markup=menu_principal(),
            )
            return

        bot.send_message(
            message.chat.id,
            f"{message.from_user.first_name}, aqui estão os seus serviços cadastrados:",
            reply_markup=ReplyKeyboardRemove(),
        )

        for servico in servicos:
            info_servico = (
                f"🔖 Descrição: {servico.descricao}\n"
                f"🔎 Status: {servico.status}\n"
                "➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖"
            )
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton(
                    "🗑️ Excluir Serviço", callback_data=f"excluir_servico_{servico.id}"
                )
            )
            bot.send_message(message.chat.id, info_servico, reply_markup=keyboard)

        bot.send_message(message.chat.id, "Escolha uma opção:", reply_markup=menu_principal())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("excluir_servico_"))
    def callback_excluir_servico(call):
        servico_id = int(call.data.replace("excluir_servico_", ""))
        bot.answer_callback_query(call.id)

        with get_database().unit_of_work(commit=False) as session:
            usuario = (
                session.query(Usuario)
                .filter(Usuario.telegram_id == call.from_user.id)
                .first()
            )
            servico = (
                session.query(Servico)
                .filter(
                    Servico.id == servico_id,
                    Servico.usuario_id == (usuario.id if usuario else None),
                )
                .first()
            )
            if servico is None:
                bot.send_message(
                    call.message.chat.id,
                    "❌ Serviço não encontrado.",
                    reply_markup=menu_principal(),
                )
                return
            usuario_id = usuario.id

        bot.send_message(
            call.message.chat.id,
            "⚠️ Tem certeza que deseja excluir este serviço?",
            reply_markup=ReplyKeyboardRemove(),
        )
        opcoes = markups_genericos_keyboard(
            [{"identificacao": "Sim"}, {"identificacao": "Não"}], "identificacao"
        )
        bot.send_message(call.message.chat.id, "Escolha:", reply_markup=opcoes)
        bot.register_next_step_handler(
            call.message, confirmar_exclusao_servico, servico_id, usuario_id
        )

    def confirmar_exclusao_servico(message, servico_id: int, usuario_id: int):
        if message.text != "Sim":
            bot.send_message(
                message.chat.id,
                "❌ Exclusão cancelada.",
                reply_markup=menu_principal(),
            )
            return

        try:
            with get_database().unit_of_work() as session:
                servico = (
                    session.query(Servico)
                    .filter(Servico.id == servico_id, Servico.usuario_id == usuario_id)
                    .first()
                )
                if servico is None:
                    bot.send_message(
                        message.chat.id,
                        "❌ Serviço não encontrado.",
                        reply_markup=menu_principal(),
                    )
                    return
                servico.status = "Excluido"
        except Exception:
            logger.exception("falha_ao_excluir_servico", extra={"servico_id": servico_id})
            bot.send_message(
                message.chat.id,
                "😕 Não foi possível excluir o serviço agora.",
                reply_markup=menu_principal(),
            )
            return

        bot.send_message(
            message.chat.id,
            "✅ Serviço excluído com sucesso!",
            reply_markup=menu_principal(),
        )
