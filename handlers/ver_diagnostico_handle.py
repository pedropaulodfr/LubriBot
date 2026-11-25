"""Diagnóstico de problemas com IA.

Correções em relação ao código legado:

- ``diagnostico`` e ``veiculo`` eram objetos globais de módulo, compartilhados
  entre usuários; agora o estado é por conversa;
- havia vírgula acidental em ``diagnostico.veiculo_id = veiculo.id,``, gravando
  uma tupla e falhando no commit (o limite diário de 3 nunca era atingido);
- o veículo era buscado só pela placa; agora exige ``usuario_id`` do dono.
"""

from __future__ import annotations

import datetime
import os

import google.generativeai as genai
from dotenv import find_dotenv, load_dotenv
from telebot.types import ForceReply

from keyboards.markups_genericos_keyboard import markups_genericos_keyboard
from keyboards.menu_principal_keyboard import menu_principal
from keyboards.veiculos_keyboard import veiculos_keyboard
from lubribot.database.runtime import get_database
from lubribot.models import Usuario, Veiculo, VeiculoDiagnosticos
from lubribot.utils.logging import get_logger
from prompts.diagnosticos_prompt import get_diagnostico_prompt
from services.veiculos_service import get_veiculos_by_usuario
from utils.envio_mensagem import send_and_delete

logger = get_logger(__name__)

load_dotenv(find_dotenv())
genai.configure(api_key=os.getenv("GEMINI_ApiKey"))
modelo = genai.GenerativeModel("gemini-2.5-flash")

LIMITE_DIARIO = 3

# chat_id -> {"veiculo_id": int, "veiculo_texto": str, "problema": str, "diagnostico": str}
_ESTADOS: dict[int, dict] = {}


def ver_diagnostico_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "⚠️ Diagnósticos")
    def ver_diagnostico(message):
        with get_database().unit_of_work(commit=False) as session:
            usuario = (
                session.query(Usuario)
                .filter(Usuario.telegram_id == message.from_user.id)
                .first()
            )
            if not usuario:
                send_and_delete(bot, message.chat.id, "❌ Usuário não encontrado.")
                send_and_delete(bot, message.chat.id, "🔄 Clique em /start para tentar novamente.")
                return
            usuario_id = usuario.id

        veiculos = get_veiculos_by_usuario(usuario_id)
        if not veiculos:
            send_and_delete(
                bot,
                message.chat.id,
                "❌ Nenhum veículo encontrado. Por favor, adicione um veículo primeiro.",
            )
            bot.send_message(message.chat.id, "Escolha uma opção:", reply_markup=menu_principal())
            return

        bot.send_message(
            message.chat.id,
            "Selecione um veículo:",
            reply_markup=veiculos_keyboard(veiculos),
        )
        bot.register_next_step_handler(message, receber_veiculo, usuario_id)

    def receber_veiculo(message, usuario_id: int):
        if message.text == "❌ Cancelar":
            _ESTADOS.pop(message.chat.id, None)
            bot.send_message(
                message.chat.id,
                "Solicitação de diagnóstico cancelada.",
                reply_markup=menu_principal(),
            )
            return

        partes = (message.text or "").split(" - ")
        placa = partes[0].replace("-", "").strip().upper()

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
                    "❌ Veículo não encontrado. Recomece em ⚠️ Diagnósticos.",
                    reply_markup=menu_principal(),
                )
                return
            _ESTADOS[message.chat.id] = {
                "veiculo_id": veiculo.id,
                "veiculo_texto": f"{veiculo.tipo} {veiculo.fabricante} {veiculo.modelo}",
                "usuario_id": usuario_id,
            }

        bot.send_message(
            message.chat.id,
            "Relate o problema do veículo:",
            reply_markup=ForceReply(),
        )
        bot.register_next_step_handler(message, receber_problema)

    def receber_problema(message):
        estado = _ESTADOS.get(message.chat.id)
        if estado is None:
            bot.send_message(
                message.chat.id,
                "⚠️ Sessão expirada. Recomece em ⚠️ Diagnósticos.",
                reply_markup=menu_principal(),
            )
            return

        if message.text == "❌ Cancelar":
            _ESTADOS.pop(message.chat.id, None)
            bot.send_message(
                message.chat.id,
                "Solicitação de diagnóstico cancelada.",
                reply_markup=menu_principal(),
            )
            return

        problema = (message.text or "").strip()
        if not problema:
            bot.send_message(message.chat.id, "❌ Descreva o problema do veículo:", reply_markup=ForceReply())
            bot.register_next_step_handler(message, receber_problema)
            return

        processar_enviar_diagnostico(message, estado, problema)

    def processar_enviar_diagnostico(message, estado: dict, problema: str):
        hoje = datetime.date.today()
        with get_database().unit_of_work(commit=False) as session:
            diagnosticos_hoje = (
                session.query(VeiculoDiagnosticos)
                .filter(
                    VeiculoDiagnosticos.veiculo.has(
                        Veiculo.usuario_id == estado["usuario_id"]
                    ),
                    VeiculoDiagnosticos.datacriacao == hoje,
                )
                .count()
            )

        if diagnosticos_hoje >= LIMITE_DIARIO:
            bot.send_message(
                message.chat.id,
                "❌ Você atingiu o limite diário de 3 diagnósticos. Por favor, tente novamente amanhã.",
                reply_markup=menu_principal(),
            )
            _ESTADOS.pop(message.chat.id, None)
            return

        send_and_delete(
            bot,
            message.chat.id,
            "🧠 Diagnosticando o problema do seu veículo. Por favor, aguarde...",
            delay=60,
        )

        try:
            bot.send_chat_action(message.chat.id, "typing")
            resposta = modelo.generate_content(
                get_diagnostico_prompt(estado["veiculo_texto"], problema)
            )
            texto = (resposta.text or "").strip()
            if not texto:
                raise RuntimeError("resposta vazia da IA")
        except Exception:
            logger.exception("falha_ao_gerar_diagnostico")
            send_and_delete(
                bot,
                message.chat.id,
                "😕 Ocorreu um erro ao tentar procurar um diagnóstico. Por favor, tente novamente!",
                reply_markup=menu_principal(),
            )
            _ESTADOS.pop(message.chat.id, None)
            return

        estado["problema"] = problema
        estado["diagnostico"] = texto

        bot.send_message(message.chat.id, texto, reply_markup=menu_principal(), parse_mode="HTML")
        opcoes = markups_genericos_keyboard(
            [{"identificacao": "✅ Sim"}, {"identificacao": "❌ Não"}], "identificacao"
        )
        bot.send_message(message.chat.id, "O seu problema foi resolvido?", reply_markup=opcoes)
        bot.register_next_step_handler(message, receber_resolucao)

    def receber_resolucao(message):
        estado = _ESTADOS.pop(message.chat.id, None)
        if estado is None:
            bot.send_message(
                message.chat.id,
                "⚠️ Sessão expirada. Recomece em ⚠️ Diagnósticos.",
                reply_markup=menu_principal(),
            )
            return

        if message.text == "✅ Sim":
            resolvido = True
            bot.send_message(
                message.chat.id,
                "✅ Que ótimo! Fico feliz em ajudar.",
                reply_markup=menu_principal(),
            )
        elif message.text == "❌ Não":
            resolvido = False
            bot.send_message(
                message.chat.id,
                "❌ Sinto muito por não ter ajudado. Recomendo procurar um mecânico de confiança para uma avaliação mais detalhada.",
                reply_markup=menu_principal(),
            )
        else:
            _ESTADOS[message.chat.id] = estado
            bot.send_message(
                message.chat.id,
                "❌ Opção inválida. Por favor, tente novamente.",
                reply_markup=menu_principal(),
            )
            return

        try:
            with get_database().unit_of_work() as session:
                session.add(
                    VeiculoDiagnosticos(
                        veiculo_id=estado["veiculo_id"],
                        problema=estado["problema"],
                        diagnostico=estado["diagnostico"],
                        datacriacao=datetime.date.today(),
                        resolvido=resolvido,
                    )
                )
        except Exception:
            logger.exception("falha_ao_salvar_diagnostico")
            bot.send_message(
                message.chat.id,
                "⚠️ O diagnóstico foi exibido, mas não conseguimos salvá-lo no histórico.",
                reply_markup=menu_principal(),
            )
