"""Exclusão de veículo (soft delete) com confirmação.

Correções:
- confirma antes de remover (antes o clique excluía direto);
- exige o dono do veículo (antes buscava só pela placa);
- sem objeto de módulo e sem sessão global.
"""

from __future__ import annotations

from lubribot.bot.keyboards.markups_genericos_keyboard import markups_genericos_keyboard
from lubribot.bot.keyboards.menu_principal_keyboard import menu_principal
from lubribot.bot.keyboards.veiculos_keyboard import veiculos_keyboard
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

        with get_database().unit_of_work(commit=False) as session:
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
            descricao = f"{veiculo.fabricante or ''} {veiculo.modelo or ''}".strip() or placa

        opcoes = markups_genericos_keyboard(
            [{"identificacao": "Sim"}, {"identificacao": "Não"}], "identificacao"
        )
        bot.send_message(
            message.chat.id,
            f"⚠️ Confirmar a remoção do veículo *{descricao}* ({placa})?\n"
            "O histórico de manutenções é preservado.",
            parse_mode="Markdown",
            reply_markup=opcoes,
        )
        bot.register_next_step_handler(message, confirmar_remocao, usuario_id, placa)

    def confirmar_remocao(message, usuario_id: int, placa: str):
        if message.text != "Sim":
            bot.send_message(
                message.chat.id,
                "❌ Exclusão cancelada.",
                reply_markup=menu_principal(),
            )
            return

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
                        "❌ Veículo não encontrado.",
                        reply_markup=menu_principal(),
                    )
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
