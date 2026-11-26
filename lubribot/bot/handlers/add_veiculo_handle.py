"""Cadastro de veículo.

Correção em relação ao código legado: o objeto ``Veiculo`` era um global do
módulo; na segunda utilização ele era reanexado à sessão e sobrescrevia o
registro do usuário anterior. Agora cada conversa tem seu próprio rascunho em
memória, chaveado por ``chat_id``, e a gravação acontece numa única transação.
"""

from __future__ import annotations

from dataclasses import dataclass

from telebot.types import (
    ForceReply,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)

from lubribot.bot.keyboards.menu_principal_keyboard import menu_principal
from lubribot.bot.keyboards.modelos_veiculos_keyboard import modelos_veiculos_keyboard
from lubribot.bot.keyboards.tipos_veiculos_keyboard import tipos_veiculos_keyboard
from lubribot.database.runtime import get_database
from lubribot.domain.validation import (
    normalizar_placa,
    normalizar_renavam,
    validar_ano,
    validar_placa,
)
from lubribot.bot.conversation_store import DraftMixin, get_registry
from lubribot.models import Usuario, Veiculo
from lubribot.utils.logging import get_logger
from services.vpic_service import get_modelos_por_marca_ano

logger = get_logger(__name__)


@dataclass
class RascunhoVeiculo(DraftMixin):
    """Dados coletados durante a conversa de cadastro (persistidos por chat)."""

    __fluxo__ = "veiculo"

    usuario_id: int
    placa: str | None = None
    tipo: str | None = None
    fabricante: str | None = None
    modelo: str | None = None
    cor: str | None = None
    ano_fabricacao: str | None = None
    ano_modelo: str | None = None
    renavam: str | None = None


_RASCUNHOS = get_registry("veiculo", RascunhoVeiculo)


def _rascunho(chat_id: int) -> RascunhoVeiculo | None:
    return _RASCUNHOS.get(chat_id)


def limpar_estado(chat_id: int) -> bool:
    """Descarta o rascunho de cadastro de veículo do chat (usado por /cancelar)."""
    return _RASCUNHOS.pop(chat_id, None) is not None


def add_veiculo_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "➕ Adicionar Veículo")
    def add_veiculo(message):
        bot.send_message(
            message.chat.id,
            "Iniciando o processo de registro de veículo. Por favor, preencha as informações.",
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

        _RASCUNHOS[message.chat.id] = RascunhoVeiculo(usuario_id=usuario_id)
        bot.send_message(message.chat.id, "Informe a placa:", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_placa)

    def receber_placa(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            bot.send_message(
                message.chat.id,
                "⚠️ Sessão de cadastro expirada. Toque em *Adicionar Veículo* novamente.",
                reply_markup=menu_principal(),
            )
            return

        placa = normalizar_placa(message.text)

        if validar_placa(placa) is None:
            bot.send_message(
                message.chat.id,
                "❌ Placa inválida! Envie uma placa no formato ABC1234 ou ABC1D23.",
                reply_markup=ForceReply(),
            )
            bot.register_next_step_handler(message, receber_placa)
            return

        placa = placa.upper()
        with get_database().unit_of_work(commit=False) as session:
            existe = (
                session.query(Veiculo)
                .filter(
                    Veiculo.placa == placa,
                    Veiculo.usuario_id == rascunho.usuario_id,
                    Veiculo.status != "Deletado",
                )
                .first()
            )
        if existe:
            bot.send_message(
                message.chat.id,
                "❌ Placa já cadastrada! Por favor, envie uma placa diferente.",
                reply_markup=ForceReply(),
            )
            bot.register_next_step_handler(message, receber_placa)
            return

        rascunho.placa = placa

        bot.send_message(message.chat.id, "Selecione o tipo", reply_markup=tipos_veiculos_keyboard())
        bot.register_next_step_handler(message, receber_tipo)

    def receber_tipo(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            bot.send_message(message.chat.id, "⚠️ Sessão de cadastro expirada.", reply_markup=menu_principal())
            return

        tipo = message.text
        if tipo == "Cancelar" or tipo == "❌ Cancelar":
            _RASCUNHOS.pop(message.chat.id, None)
            bot.send_message(
                message.chat.id,
                "Operação de adição de veículo cancelada.",
                reply_markup=menu_principal(),
            )
            return

        rascunho.tipo = tipo
        bot.send_message(message.chat.id, "Informe a marca:", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_fabricante)

    def receber_fabricante(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            bot.send_message(message.chat.id, "⚠️ Sessão de cadastro expirada.", reply_markup=menu_principal())
            return

        rascunho.fabricante = (message.text or "").strip()

        # Consulta externa (NHTSA) com degradação graciosa: se a API falhar,
        # o usuário digita o modelo manualmente em vez de ver um erro.
        try:
            modelos = get_modelos_por_marca_ano(
                marca=rascunho.fabricante, tipo_veiculo=rascunho.tipo
            )
        except Exception:
            logger.exception(
                "vpic_falhou_no_cadastro",
                extra={"fabricante": rascunho.fabricante},
            )
            modelos = []

        if modelos:
            bot.send_message(
                message.chat.id,
                "Selecione ou insira o modelo:",
                reply_markup=modelos_veiculos_keyboard(modelos),
            )
            bot.register_next_step_handler(message, receber_modelo)
        else:
            bot.send_message(message.chat.id, "Insira o modelo:", reply_markup=ForceReply())
            bot.register_next_step_handler(message, receber_modelo_manualmente)

    def receber_modelo(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            bot.send_message(message.chat.id, "⚠️ Sessão de cadastro expirada.", reply_markup=menu_principal())
            return

        modelo = message.text
        if modelo == "❌ Cancelar":
            _RASCUNHOS.pop(message.chat.id, None)
            bot.send_message(
                message.chat.id,
                "❌ Operação de adição de veículo cancelada.",
                reply_markup=menu_principal(),
            )
            return
        if modelo == "⌨️ Inserir manualmente:":
            bot.send_message(message.chat.id, "Insira o modelo:", reply_markup=ForceReply())
            bot.register_next_step_handler(message, receber_modelo_manualmente)
            return

        rascunho.modelo = modelo
        mostrar_cores_disponiveis(message)

    def receber_modelo_manualmente(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            bot.send_message(message.chat.id, "⚠️ Sessão de cadastro expirada.", reply_markup=menu_principal())
            return
        rascunho.modelo = (message.text or "").strip()
        mostrar_cores_disponiveis(message)

    def mostrar_cores_disponiveis(message):
        markup_cores = InlineKeyboardMarkup()
        markup_cores.row(
            InlineKeyboardButton("🔴", callback_data="receber_cor:vermelha"),
            InlineKeyboardButton("🟠", callback_data="receber_cor:laranja"),
            InlineKeyboardButton("🟡", callback_data="receber_cor:amarela"),
            InlineKeyboardButton("🟢", callback_data="receber_cor:verde"),
            InlineKeyboardButton("🔵", callback_data="receber_cor:azul"),
        )
        markup_cores.row(
            InlineKeyboardButton("🟣", callback_data="receber_cor:roxa"),
            InlineKeyboardButton("🟤", callback_data="receber_cor:marrom"),
            InlineKeyboardButton("⚫", callback_data="receber_cor:preta"),
            InlineKeyboardButton("⚪", callback_data="receber_cor:branca"),
        )
        markup_cores.row(
            InlineKeyboardButton("⌨️ Inserir manualmente:", callback_data="receber_cor:digitar"),
            InlineKeyboardButton("❌ Cancelar", callback_data="receber_cor:cancelar"),
        )
        bot.send_message(message.chat.id, "Selecione a cor:", reply_markup=markup_cores)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("receber_cor"))
    def callback_receber_cor(call):
        chat_id = call.message.chat.id
        rascunho = _rascunho(chat_id)
        if rascunho is None:
            bot.answer_callback_query(call.id, "Sessão expirada. Recomece o cadastro.")
            return

        cor = call.data.split(":")[1]

        if cor == "digitar":
            bot.send_message(chat_id, "Informe a cor:", reply_markup=ForceReply())
            bot.register_next_step_handler(call.message, receber_cor)
        elif cor == "cancelar":
            _RASCUNHOS.pop(chat_id, None)
            bot.send_message(chat_id, "❌ Operação de adição de veículo cancelada.", reply_markup=menu_principal())
            bot.delete_message(chat_id, call.message.message_id)
        else:
            rascunho.cor = cor.capitalize()
            bot.delete_message(chat_id, call.message.message_id)
            bot.send_message(chat_id, "Informe o ano de fabricação:", reply_markup=ForceReply())
            bot.register_next_step_handler(call.message, receber_ano_fabricacao)
        bot.answer_callback_query(call.id)

    def receber_cor(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            bot.send_message(message.chat.id, "⚠️ Sessão de cadastro expirada.", reply_markup=menu_principal())
            return
        rascunho.cor = (message.text or "").capitalize()
        bot.send_message(message.chat.id, "Informe o ano de fabricação:", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_ano_fabricacao)

    def receber_ano_fabricacao(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            bot.send_message(message.chat.id, "⚠️ Sessão de cadastro expirada.", reply_markup=menu_principal())
            return

        ano = validar_ano(message.text)
        if ano is None:
            bot.send_message(
                message.chat.id,
                "❌ Ano inválido! Informe um ano com 4 dígitos. Ex: 2026",
            )
            bot.register_next_step_handler(message, receber_ano_fabricacao)
            return

        rascunho.ano_fabricacao = ano
        bot.send_message(message.chat.id, "Informe o ano do modelo:", reply_markup=ForceReply())
        bot.register_next_step_handler(message, receber_ano_modelo)

    def receber_ano_modelo(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            bot.send_message(message.chat.id, "⚠️ Sessão de cadastro expirada.", reply_markup=menu_principal())
            return

        ano = validar_ano(message.text)
        if ano is None:
            bot.send_message(
                message.chat.id,
                "❌ Ano inválido! Informe um ano com 4 dígitos. Ex: 2026",
            )
            bot.register_next_step_handler(message, receber_ano_modelo)
            return

        rascunho.ano_modelo = ano
        bot.send_message(
            message.chat.id, "Informe o RENAVAM: (Opcional)", reply_markup=ForceReply()
        )
        bot.send_message(
            message.chat.id, "<i>Digite . se não quiser adicionar</i>", parse_mode="HTML"
        )
        bot.register_next_step_handler(message, receber_renavam)

    def receber_renavam(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            bot.send_message(message.chat.id, "⚠️ Sessão de cadastro expirada.", reply_markup=menu_principal())
            return

        texto = (message.text or "").strip()
        rascunho.renavam = normalizar_renavam(texto)

        bot.send_message(message.chat.id, "⏳ Registrando veículo...")
        finalizar_registro(message, rascunho)

    def finalizar_registro(message, rascunho: RascunhoVeiculo):
        try:
            with get_database().unit_of_work() as session:
                session.add(
                    Veiculo(
                        usuario_id=rascunho.usuario_id,
                        tipo=rascunho.tipo,
                        placa=rascunho.placa,
                        renavam=rascunho.renavam,
                        fabricante=rascunho.fabricante,
                        modelo=rascunho.modelo,
                        anoModelo=rascunho.ano_modelo,
                        anoFabricacao=rascunho.ano_fabricacao,
                        cor=rascunho.cor,
                        status="Ativo",
                    )
                )
        except Exception:
            logger.exception(
                "falha_ao_registrar_veiculo",
                extra={"usuario_id": rascunho.usuario_id},
            )
            bot.send_message(
                message.chat.id,
                "😕 Não foi possível registrar o veículo agora. Tente novamente.",
                reply_markup=menu_principal(),
            )
            _RASCUNHOS.pop(message.chat.id, None)
            return

        _RASCUNHOS.pop(message.chat.id, None)
        bot.send_message(message.chat.id, "✅ Veículo registrado com sucesso!")
        bot.send_message(message.chat.id, "Escolha uma opção:", reply_markup=menu_principal())
