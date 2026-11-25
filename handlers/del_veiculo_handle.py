"""Exclusão de veículo (soft delete).

Correções: o veículo era buscado só pela placa, permitindo remover o veículo de
outro usuário; o objeto de módulo ``veiculo`` era reutilizado; e a sessão global
nunca era fechada em caso de erro.
"""

from __future__ import annotations

from keyboards.menu_principal_keyboard import menu_principal
from keyboards.veiculos_keyboard import veiculos_keyboard
from lubribot.database.runtime import get_database
from lubribot.models import Usuario, Veiculo
from lubribot.utils.logging import get_logger
from services.veiculos_service import get_veiculos_by_usuario

logger = get_logger(__name__)


def del_veiculo_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "➖ Remover Veículo")
    def del_veiculo(message):
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

        veiculos_usuario = get_veiculos_by_usuario(usuario_id)
        if not veiculos_usuario:
            bot.send_message(
                message.chat.id,
                "⚠️ Você ainda não possui veículos registrados!",
                reply_markup=menu_principal(),
            )
            return

        bot.send_message(
            message.chat.id,
            "Selecione um veículo para deletar:",
            reply_markup=veiculos_keyboard(veiculos_usuario),
        )
        bot.register_next_step_handler(message, receber_veiculo, usuario_id)

    def receber_veiculo(message, usuario_id: int):
        if message.text == "❌ Cancelar":
            bot.send_message(
                message.chat.id,
                "Operação de exclusão de veículo cancelada.",
                reply_markup=menu_principal(),
            )
            return

        placa = (message.text or "").split(" - ")[0].replace("-", "").strip().upper()

        try:
            with get_database().unit_of_work() as session:
                veiculo = (
                    session.query(Veiculo)
                    .filter(
                        Veiculo.placa == placa,
                        Veiculo.usuario_id == usuario_id,
                        Veiculo.status == "Ativo",
                    )
                    .first()
                )
                if veiculo is None:
                    bot.send_message(
                        message.chat.id,
                        "❌ Veículo não encontrado. Por favor, selecione um veículo válido.",
                    )
                    bot.register_next_step_handler(message, receber_veiculo, usuario_id)
                    return
                veiculo.status = "Deletado"
        except Exception:
            logger.exception(
                "falha_ao_remover_veiculo", extra={"usuario_id": usuario_id}
            )
            bot.send_message(
                message.chat.id,
                "😕 Não foi possível remover o veículo agora. Tente novamente.",
                reply_markup=menu_principal(),
            )
            return

        bot.send_message(
            message.chat.id,
            "✅ Veículo removido com sucesso.",
            reply_markup=menu_principal(),
        )
