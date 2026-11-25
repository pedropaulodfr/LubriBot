"""Cadastro de produto do catálogo do usuário.

Correção: o módulo criava ``usuario = Usuario()`` no escopo global (instância ORM
compartilhada e inútil) e fechava a sessão global, que era reaproveitada depois.
Agora o produto é criado por fluxo e gravado numa unidade de trabalho.
"""

from __future__ import annotations

from telebot.types import ForceReply, ReplyKeyboardRemove

from lubribot.bot.keyboards.menu_principal_keyboard import menu_principal
from lubribot.database.runtime import get_database
from lubribot.models import Produto, Usuario
from lubribot.utils.logging import get_logger

logger = get_logger(__name__)


def add_produto_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "➕🛢️ Adicionar Produtos")
    def add_produto(message):
        bot.send_message(
            message.chat.id,
            "Iniciando o processo de registro do produto. Por favor, preencha as informações.",
            reply_markup=ReplyKeyboardRemove(),
        )

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

        bot.send_message(
            message.chat.id,
            "Informe a descrição do produto:",
            reply_markup=ForceReply(),
        )
        bot.register_next_step_handler(message, receber_descricao, usuario_id)

    def receber_descricao(message, usuario_id: int):
        descricao = (message.text or "").strip().capitalize()
        if not descricao:
            bot.send_message(
                message.chat.id,
                "❌ Descrição vazia. Informe a descrição do produto:",
                reply_markup=ForceReply(),
            )
            bot.register_next_step_handler(message, receber_descricao, usuario_id)
            return

        bot.send_message(message.chat.id, "⏳ Registrando produto...")
        try:
            with get_database().unit_of_work() as session:
                session.add(
                    Produto(descricao=descricao, usuario_id=usuario_id, status="Ativo")
                )
        except Exception:
            logger.exception("falha_ao_registrar_produto", extra={"usuario_id": usuario_id})
            bot.send_message(
                message.chat.id,
                "😕 Não foi possível registrar o produto agora. Tente novamente.",
                reply_markup=menu_principal(),
            )
            return

        bot.send_message(message.chat.id, "✅ Produto registrado com sucesso!")
        bot.send_message(message.chat.id, "Escolha uma opção:", reply_markup=menu_principal())
