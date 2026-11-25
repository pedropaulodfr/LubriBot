"""Visualização do histórico de manutenções.

Correções em relação ao código legado:
- o veículo era buscado só pela placa (IDOR); agora exige dono;
- o serviço era lido com inner join e ``.first()`` sem checar ``None``, o que
  derrubava a listagem quando a manutenção não tinha serviço vinculado;
- ``custo`` e ``data`` nulos quebravam a formatação;
- o botão da nota de serviço só aparecia quando existia foto do painel (aninhado
  no ``if`` errado).
"""

from __future__ import annotations

import os

from dotenv import find_dotenv, load_dotenv
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove

from lubribot.bot.keyboards.markups_genericos_keyboard import markups_genericos_keyboard
from lubribot.bot.keyboards.menu_principal_keyboard import menu_principal
from lubribot.bot.keyboards.veiculos_keyboard import veiculos_keyboard
from lubribot.database.runtime import get_database
from lubribot.models import (
    Manutencao,
    ManutencaoProduto,
    ManutencaoServico,
    Produto,
    Servico,
    Usuario,
    Veiculo,
)
from lubribot.utils.logging import get_logger
from services.manutencoes_service import get_manutencoes_by_usuario, get_manutencoes_by_veiculos
from services.veiculos_service import get_veiculos_by_usuario

logger = get_logger(__name__)

load_dotenv(find_dotenv())

AWS_REGION = os.getenv("AWS_Region")
AWS_BUCKET = os.getenv("AWS_BucketName")


def ver_manutencao_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "🔎 Ver Manutenções")
    def tipo_manutencao(message):
        opcoes = markups_genericos_keyboard(
            [
                {"identificacao": "🚗 Ver por veículo"},
                {"identificacao": "📑 Ver todas"},
            ],
            "identificacao",
        )
        bot.send_message(
            message.chat.id,
            "Deseja ver todas as manutenções ou somente as de um veículo específico?",
            reply_markup=opcoes,
        )
        bot.register_next_step_handler(message, receber_tipo_manutencao)

    def receber_tipo_manutencao(message):
        tipo_escolhido = message.text

        if tipo_escolhido == "🚗 Ver por veículo":
            with get_database().unit_of_work(commit=False) as session:
                usuario = (
                    session.query(Usuario)
                    .filter(Usuario.telegram_id == message.from_user.id)
                    .first()
                )
                if not usuario:
                    bot.send_message(message.chat.id, "❌ Usuário não encontrado.")
                    bot.send_message(
                        message.chat.id, "🔄 Clique em /start para tentar novamente."
                    )
                    return
                usuario_id = usuario.id

            veiculos = get_veiculos_by_usuario(usuario_id)
            if not veiculos:
                bot.send_message(
                    message.chat.id,
                    "❌ Nenhum veículo encontrado. Por favor, adicione um veículo primeiro.",
                )
                bot.send_message(
                    message.chat.id, "Escolha uma opção:", reply_markup=menu_principal()
                )
                return

            bot.send_message(
                message.chat.id,
                "Selecione um Veículo:",
                reply_markup=veiculos_keyboard(veiculos),
            )
            bot.register_next_step_handler(message, receber_veiculo, usuario_id)
        else:
            ver_manutencao(message, tipo_escolhido)

    def receber_veiculo(message, usuario_id: int):
        if message.text == "❌ Cancelar":
            bot.send_message(
                message.chat.id,
                "Visualização de manutenção cancelada.",
                reply_markup=menu_principal(),
            )
            return

        placa_selecionada = (
            (message.text or "").split(" - ")[0].replace("-", "").strip().upper()
        )

        with get_database().unit_of_work(commit=False) as session:
            veiculo = (
                session.query(Veiculo)
                .filter(
                    Veiculo.placa == placa_selecionada,
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

        ver_manutencao(message, "🚗 Ver por veículo", veiculo_id)

    def ver_manutencao(message, tipo, veiculo_id=None):
        with get_database().unit_of_work(commit=False) as session:
            usuario = (
                session.query(Usuario)
                .filter(Usuario.telegram_id == message.from_user.id)
                .first()
            )
            if not usuario:
                bot.send_message(message.chat.id, "❌ Usuário não encontrado.")
                return

            if tipo == "🚗 Ver por veículo":
                if veiculo_id is None:
                    bot.send_message(
                        message.chat.id,
                        "❌ Veículo não informado.",
                        reply_markup=menu_principal(),
                    )
                    return
                manutencoes = get_manutencoes_by_veiculos(veiculo_id)
            else:
                manutencoes = get_manutencoes_by_usuario(usuario.id)

            if not manutencoes:
                bot.send_message(
                    message.chat.id,
                    "⚠️ Você ainda não tem manutenções registradas para este veículo!"
                    if tipo == "🚗 Ver por veículo"
                    else "⚠️ Você ainda não tem veículos com manutenções registradas!",
                    reply_markup=menu_principal(),
                )
                return

            bot.send_message(
                message.chat.id,
                f"{message.from_user.first_name}, aqui estão as suas manutenções registradas"
                f"{' para este veículo' if tipo == '🚗 Ver por veículo' else ''}:",
                reply_markup=ReplyKeyboardRemove(),
            )

            itens = [
                {
                    "texto": _formatar_manutencao(session, manutencao),
                    "id": manutencao.id,
                    "imagem": bool(manutencao.imagem),
                    "nota": bool(manutencao.imagemNotaServico),
                }
                for manutencao in manutencoes
            ]

        _HISTORICOS[message.chat.id] = {"itens": itens, "nav_msg_id": None}
        _enviar_pagina(bot, message.chat.id, 0)

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("ver_img_")
        and not call.data.startswith("ver_img_nota_servico_")
    )
    def callback_ver_imagem(call):
        manutencao_id = int(call.data.replace("ver_img_", ""))
        with get_database().unit_of_work(commit=False) as session:
            manutencao = session.get(Manutencao, manutencao_id)
            if manutencao is None or not manutencao.imagem:
                bot.answer_callback_query(call.id, "❌ Nenhuma imagem encontrada.")
                return
            url = _url_imagem(manutencao.imagem)
        bot.send_photo(call.message.chat.id, url)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ver_img_nota_servico_"))
    def callback_ver_imagem_nota_servico(call):
        manutencao_id = int(call.data.replace("ver_img_nota_servico_", ""))
        with get_database().unit_of_work(commit=False) as session:
            manutencao = session.get(Manutencao, manutencao_id)
            if manutencao is None or not manutencao.imagemNotaServico:
                bot.answer_callback_query(call.id, "❌ Nenhuma imagem encontrada.")
                return
            url = _url_imagem(manutencao.imagemNotaServico)
        bot.send_photo(call.message.chat.id, url)
        bot.answer_callback_query(call.id)

    # ------------------------------------------------------------ paginação
    @bot.callback_query_handler(func=lambda call: call.data in {"hist:prev", "hist:next"})
    def callback_paginar_historico(call):
        estado = _HISTORICOS.get(call.message.chat.id)
        bot.answer_callback_query(call.id)
        if estado is None:
            bot.send_message(
                call.message.chat.id,
                "⚠️ Histórico expirado. Abra *🔎 Ver Manutenções* novamente.",
            )
            return
        pagina_atual = estado.get("pagina", 0)
        nova = pagina_atual - 1 if call.data == "hist:prev" else pagina_atual + 1
        _enviar_pagina(bot, call.message.chat.id, nova)


PAGINA_TAMANHO = 5
_HISTORICOS: dict[int, dict] = {}


def _enviar_pagina(bot, chat_id: int, pagina: int) -> None:
    """Envia uma página de manutenções (evita 30 mensagens de uma vez)."""
    estado = _HISTORICOS.get(chat_id)
    if estado is None:
        return

    itens: list[dict] = estado["itens"]
    total = len(itens)
    total_paginas = max(1, (total + PAGINA_TAMANHO - 1) // PAGINA_TAMANHO)
    pagina = max(0, min(pagina, total_paginas - 1))
    estado["pagina"] = pagina

    # Remove o rodapé anterior para não acumular mensagens de navegação.
    if estado.get("nav_msg_id"):
        try:
            bot.delete_message(chat_id, estado["nav_msg_id"])
        except Exception:
            pass

    inicio = pagina * PAGINA_TAMANHO
    for item in itens[inicio : inicio + PAGINA_TAMANHO]:
        keyboard = _teclado_imagens(item)
        if keyboard is not None:
            bot.send_message(chat_id, item["texto"], reply_markup=keyboard)
        else:
            bot.send_message(chat_id, item["texto"])

    navegacao = InlineKeyboardMarkup()
    if pagina > 0:
        navegacao.add(InlineKeyboardButton("◀ Anterior", callback_data="hist:prev"))
    if pagina < total_paginas - 1:
        navegacao.add(InlineKeyboardButton("Próxima ▶", callback_data="hist:next"))

    rodape = (
        f"📄 Página {pagina + 1} de {total_paginas} · {total} manutenção(ões)"
    )
    mensagem = bot.send_message(
        chat_id,
        rodape,
        reply_markup=navegacao if navegacao.keyboard else menu_principal(),
    )
    estado["nav_msg_id"] = mensagem.message_id


def _formatar_manutencao(session, manutencao: Manutencao) -> str:
    """Monta o texto de uma manutenção tolerando campos nulos."""
    veiculo = manutencao.veiculo
    descricao_veiculo = "veículo"
    if veiculo is not None:
        descricao_veiculo = (
            f"{veiculo.tipo or ''} {veiculo.fabricante or ''} {veiculo.modelo or ''} "
            f"{veiculo.cor or ''} - {veiculo.anoModelo or ''}"
        ).strip()
        if veiculo.placa:
            descricao_veiculo += f" ({veiculo.placa[:3]}-{veiculo.placa[-4:]})"

    itens_servico = (
        session.query(ManutencaoServico).filter(
            ManutencaoServico.manutencao_id == manutencao.id
        ).first()
    )
    servico_nome = "—"
    if itens_servico is not None and itens_servico.servico is not None:
        servico_nome = itens_servico.servico.descricao or "—"

    itens_produto = (
        session.query(ManutencaoProduto)
        .join(Produto, Produto.id == ManutencaoProduto.produto_id)
        .filter(ManutencaoProduto.manutencao_id == manutencao.id)
        .all()
    )
    produtos = ", ".join(
        item.produto.descricao for item in itens_produto if item.produto and item.produto.descricao
    ) or "—"

    data_texto = (
        manutencao.data.strftime("%d/%m/%Y") if manutencao.data else "—"
    )
    custo_texto = f"R$ {manutencao.custo:.2f}" if manutencao.custo is not None else "—"

    return (
        f"🚘 Veículo: {descricao_veiculo}\n"
        f"📅 Data: {data_texto}\n"
        f"🔧 Serviço: {servico_nome}\n"
        f"🛢️ Produtos: {produtos}\n"
        f"💲 Custo: {custo_texto}\n"
        f"📝 Observações: {manutencao.observacao or '—'}"
    )


def _teclado_imagens(item: dict) -> InlineKeyboardMarkup | None:
    """Teclado com os botões de imagem existentes (independentes entre si)."""
    botoes = []
    if item.get("imagem"):
        botoes.append(
            InlineKeyboardButton("📷 Ver imagem", callback_data=f"ver_img_{item['id']}")
        )
    if item.get("nota"):
        botoes.append(
            InlineKeyboardButton(
                "📄 Ver nota de serviço/recibo",
                callback_data=f"ver_img_nota_servico_{item['id']}",
            )
        )
    if not botoes:
        return None
    keyboard = InlineKeyboardMarkup()
    for botao in botoes:
        keyboard.add(botao)
    return keyboard


def _url_imagem(arquivo: str) -> str:
    return f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/uploads/imagens/{arquivo}"
