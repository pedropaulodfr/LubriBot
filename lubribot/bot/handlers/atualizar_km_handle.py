"""Atualização do odômetro do veículo.

A notificação por quilometragem precisa saber o KM atual. Este fluxo permite ao
usuário informar o odômetro sem registrar uma manutenção; o valor também é
atualizado automaticamente quando uma manutenção é registrada.
"""

from __future__ import annotations

from datetime import UTC, datetime

from telebot.types import ForceReply

from lubribot.bot.keyboards.menu_principal_keyboard import menu_principal
from lubribot.bot.keyboards.veiculos_keyboard import veiculos_keyboard
from lubribot.database.runtime import get_database
from lubribot.domain.validation import validar_km
from lubribot.models import Usuario, Veiculo
from lubribot.utils.logging import get_logger
from services.veiculos_service import get_veiculos_by_usuario

logger = get_logger(__name__)


def atualizar_km_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "📍 Atualizar KM")
    def atualizar_km(message):
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

        veiculos = get_veiculos_by_usuario(usuario_id)
        if not veiculos:
            bot.send_message(
                message.chat.id,
                "⚠️ Você ainda não possui veículos registrados!",
                reply_markup=menu_principal(),
            )
            return

        bot.send_message(
            message.chat.id,
            "Selecione o veículo para atualizar o KM:",
            reply_markup=veiculos_keyboard(veiculos),
        )
        bot.register_next_step_handler(message, receber_veiculo, usuario_id)

    def receber_veiculo(message, usuario_id: int):
        if message.text == "❌ Cancelar":
            bot.send_message(
                message.chat.id,
                "Atualização de KM cancelada.",
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
            veiculo_id = veiculo.id
            km_anterior = veiculo.kmAtual

        referencia = (
            f" (último informado: {km_anterior} km)" if km_anterior is not None else ""
        )
        bot.send_message(
            message.chat.id,
            f"Informe o KM atual do veículo{referencia}:",
            reply_markup=ForceReply(),
        )
        bot.register_next_step_handler(message, receber_km, veiculo_id)

    def receber_km(message, veiculo_id: int):
        if message.text == "❌ Cancelar":
            bot.send_message(
                message.chat.id,
                "Atualização de KM cancelada.",
                reply_markup=menu_principal(),
            )
            return

        km = validar_km(message.text)
        if km is None:
            bot.send_message(
                message.chat.id,
                "❌ Quilometragem inválida. Informe um número (ex.: 45000):",
                reply_markup=ForceReply(),
            )
            bot.register_next_step_handler(message, receber_km, veiculo_id)
            return

        try:
            with get_database().unit_of_work() as session:
                veiculo = session.get(Veiculo, veiculo_id)
                if veiculo is None:
                    bot.send_message(
                        message.chat.id,
                        "❌ Veículo não encontrado.",
                        reply_markup=menu_principal(),
                    )
                    return
                veiculo.kmAtual = km
                veiculo.kmAtualizadoEm = datetime.now(UTC)
        except Exception:
            logger.exception("falha_ao_atualizar_km", extra={"veiculo_id": veiculo_id})
            bot.send_message(
                message.chat.id,
                "😕 Não foi possível atualizar o KM agora. Tente novamente.",
                reply_markup=menu_principal(),
            )
            return

        logger.info("km_atualizado", extra={"veiculo_id": veiculo_id, "km": km})
        bot.send_message(
            message.chat.id,
            f"✅ KM atualizado para {km} km.",
            reply_markup=menu_principal(),
        )
