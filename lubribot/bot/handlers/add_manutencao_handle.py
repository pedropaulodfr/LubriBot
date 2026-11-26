"""Registro de manutenção.

Correções em relação ao código legado:

- ``manutencao``, ``manutencaoServico`` e ``manutencaoProdutos`` eram globais do
  módulo e vazavam entre usuários (a manutenção seguinte herdava produtos da
  anterior). Agora cada conversa tem um rascunho próprio, chaveado por chat.
- A gravação era feita em três commits separados (manutenção, produtos,
  serviço), deixando registro pela metade se algo falhasse no meio. Agora é uma
  única transação.
- O serviço era resolvido por descrição **sem filtrar o dono**, podendo vincular
  o serviço de outro usuário. Agora resolve dentro do catálogo do usuário.
"""

from __future__ import annotations

import base64 as b64
from dataclasses import dataclass, field
from datetime import date, datetime

from telebot.types import ForceReply, ReplyKeyboardRemove

from lubribot.bot.keyboards.checkbox_genericos_keyboard import start_checkbox
from lubribot.bot.keyboards.markups_genericos_keyboard import markups_genericos_keyboard
from lubribot.bot.keyboards.menu_principal_keyboard import menu_principal
from lubribot.bot.keyboards.veiculos_keyboard import veiculos_keyboard
from lubribot.database.runtime import get_database
from lubribot.domain.validation import (
    normalizar_texto_livre,
    validar_custo,
    validar_km,
)
from lubribot.models import (
    Manutencao,
    ManutencaoProduto,
    ManutencaoServico,
    Servico,
    Usuario,
    Veiculo,
)
from lubribot.utils.logging import get_logger
from services.produtos_service import get_all_produtos_manutencao, get_produto_by_descricao_completa
from services.veiculos_service import get_veiculos_by_usuario
from services.servicos_service import get_all_servicos
from lubribot.bot.conversation_store import DraftMixin, get_registry
from lubribot.utils.upload_file_async import upload as upload_s3

logger = get_logger(__name__)

OPCAO_OUTRO_SERVICO = "⌨️ Outro:"


@dataclass
class RascunhoManutencao(DraftMixin):
    """Estado da conversa de registro de manutenção (persistido por chat)."""

    __fluxo__ = "manutencao"

    usuario_id: int
    veiculo_id: int | None = None
    data: date | None = None
    servico_id: int | None = None
    km: int | None = None
    imagem: str | None = None
    imagem_nota_servico: str | None = None
    custo: float | None = None
    observacao: str | None = None
    produtos: list[int] = field(default_factory=list)


_RASCUNHOS = get_registry("manutencao", RascunhoManutencao)


def _rascunho(chat_id: int) -> RascunhoManutencao | None:
    return _RASCUNHOS.get(chat_id)


def limpar_estado(chat_id: int) -> bool:
    """Descarta o rascunho de manutenção do chat (usado por /cancelar)."""
    return _RASCUNHOS.pop(chat_id, None) is not None


def _reiniciar(bot, message) -> None:
    _RASCUNHOS.pop(message.chat.id, None)
    bot.send_message(
        message.chat.id,
        "⚠️ Sua sessão de registro expirou. Toque em *🛠️ Registrar Manutenção* para começar de novo.",
        reply_markup=menu_principal(),
    )


def _perguntar_custo(bot, message) -> None:
    bot.send_message(message.chat.id, "Informe o custo do serviço (em R$):", reply_markup=ForceReply())
    bot.register_next_step_handler(message, receber_custo)


def _perguntar_observacoes(bot, message) -> None:
    bot.send_message(message.chat.id, "Alguma observação a ser feita? (Opcional)", reply_markup=ForceReply())
    bot.send_message(message.chat.id, "<i>Digite . se não quiser adicionar</i>", parse_mode="HTML")
    bot.register_next_step_handler(message, receber_observacoes)


def add_manutencao_handle(bot):
    @bot.message_handler(func=lambda message: message.text == "🛠️ Registrar Manutenção")
    def add_manutencao(message):
        bot.send_message(
            message.chat.id,
            "Iniciando o processo de registro de manutenção. Por favor, envie os detalhes da manutenção.",
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
                bot.send_message(message.chat.id, "🔄 Clique em /start para tentar novamente.")
                return
            usuario_id = usuario.id

        veiculos = get_veiculos_by_usuario(usuario_id)
        if not veiculos:
            bot.send_message(
                message.chat.id,
                "❌ Nenhum veículo encontrado. Por favor, adicione um veículo primeiro.",
            )
            bot.send_message(message.chat.id, "Escolha uma opção:", reply_markup=menu_principal())
            return

        _RASCUNHOS[message.chat.id] = RascunhoManutencao(usuario_id=usuario_id)
        bot.send_message(
            message.chat.id,
            "Selecione um Veículo para manutenção:",
            reply_markup=veiculos_keyboard(veiculos),
        )
        bot.register_next_step_handler(message, receber_veiculo)

    # ------------------------------------------------------------------ etapas
    def receber_veiculo(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            _reiniciar(bot, message)
            return

        if message.text == "❌ Cancelar":
            _RASCUNHOS.pop(message.chat.id, None)
            bot.send_message(
                message.chat.id,
                "Registro de manutenção cancelado.",
                reply_markup=menu_principal(),
            )
            return

        placa_selecionada = (message.text or "").split(" - ")[0].replace("-", "").strip().upper()

        with get_database().unit_of_work(commit=False) as session:
            veiculo = (
                session.query(Veiculo)
                .filter(
                    Veiculo.placa == placa_selecionada,
                    Veiculo.usuario_id == rascunho.usuario_id,
                    Veiculo.status == "Ativo",
                )
                .first()
            )
            if veiculo is None:
                bot.send_message(
                    message.chat.id,
                    "❌ Veículo não encontrado. Por favor, selecione um veículo válido.",
                )
                bot.register_next_step_handler(message, receber_veiculo)
                return
            rascunho.veiculo_id = veiculo.id

        data_opcoes = markups_genericos_keyboard(
            [{"identificacao": "Hoje"}, {"identificacao": "Outra Data"}], "identificacao"
        )
        bot.send_message(message.chat.id, "Data da manutenção:", reply_markup=data_opcoes)
        bot.register_next_step_handler(message, receber_opcao_data)

    def receber_opcao_data(message):
        if _rascunho(message.chat.id) is None:
            _reiniciar(bot, message)
            return

        if message.text == "Hoje":
            receber_data(message)
            return

        bot.send_message(
            message.chat.id,
            "Informe a data da manutenção (DD/MM/AAAA):",
            reply_markup=ForceReply(),
        )
        bot.register_next_step_handler(message, receber_data)

    def receber_data(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            _reiniciar(bot, message)
            return

        texto = (message.text or "").strip()
        try:
            if texto == "Hoje":
                rascunho.data = date.today()
            else:
                rascunho.data = datetime.strptime(texto, "%d/%m/%Y").date()
        except ValueError:
            bot.send_message(
                message.chat.id,
                "❌ Data inválida. Use o formato DD/MM/AAAA (ex.: 05/02/2026):",
                reply_markup=ForceReply(),
            )
            bot.register_next_step_handler(message, receber_data)
            return

        servicos_disponiveis = list(get_all_servicos(usuario_id=rascunho.usuario_id))
        opcoes = [{"descricao": s.descricao} for s in servicos_disponiveis if s.descricao]
        opcoes.append({"descricao": OPCAO_OUTRO_SERVICO})
        bot.send_message(
            message.chat.id,
            "Descreva o serviço realizado:",
            reply_markup=markups_genericos_keyboard(opcoes, "descricao"),
        )
        bot.register_next_step_handler(message, receber_servico)

    def receber_servico(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            _reiniciar(bot, message)
            return

        descricao = (message.text or "").strip()

        if descricao == OPCAO_OUTRO_SERVICO:
            bot.send_message(
                message.chat.id,
                "Por favor, descreva o serviço realizado:",
                reply_markup=ForceReply(),
            )
            bot.register_next_step_handler(message, receber_descricao_servico_personalizado)
            return

        # Resolve somente dentro do catálogo do usuário (globais + próprios).
        servico_id = None
        for servico in get_all_servicos(usuario_id=rascunho.usuario_id):
            if servico.descricao == descricao:
                servico_id = servico.id
                break

        if servico_id is None:
            bot.send_message(
                message.chat.id,
                "❌ Serviço não encontrado. Escolha uma das opções do teclado:",
            )
            opcoes = [
                {"descricao": s.descricao}
                for s in get_all_servicos(usuario_id=rascunho.usuario_id)
                if s.descricao
            ]
            opcoes.append({"descricao": OPCAO_OUTRO_SERVICO})
            bot.send_message(
                message.chat.id,
                "Descreva o serviço realizado:",
                reply_markup=markups_genericos_keyboard(opcoes, "descricao"),
            )
            bot.register_next_step_handler(message, receber_servico)
            return

        rascunho.servico_id = servico_id
        bot.send_message(
            message.chat.id,
            "Informe a quilometragem do veículo (KM):",
            reply_markup=ForceReply(),
        )
        bot.register_next_step_handler(message, receber_quilometragem)

    def receber_descricao_servico_personalizado(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            _reiniciar(bot, message)
            return

        descricao = (message.text or "").strip().capitalize()
        if not descricao:
            bot.send_message(
                message.chat.id,
                "❌ Descreva o serviço realizado:",
                reply_markup=ForceReply(),
            )
            bot.register_next_step_handler(message, receber_descricao_servico_personalizado)
            return

        try:
            with get_database().unit_of_work() as session:
                novo_servico = Servico(
                    descricao=descricao,
                    usuario_id=rascunho.usuario_id,
                    status="Ativo",
                )
                session.add(novo_servico)
                session.flush()
                rascunho.servico_id = novo_servico.id
        except Exception:
            logger.exception("falha_ao_criar_servico_personalizado")
            bot.send_message(
                message.chat.id,
                "😕 Não foi possível salvar o serviço. Tente novamente.",
                reply_markup=menu_principal(),
            )
            _RASCUNHOS.pop(message.chat.id, None)
            return

        bot.send_message(
            message.chat.id,
            "Informe a quilometragem do veículo (KM):",
            reply_markup=ForceReply(),
        )
        bot.register_next_step_handler(message, receber_quilometragem)

    def receber_quilometragem(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            _reiniciar(bot, message)
            return

        km = validar_km(message.text)
        if km is None:
            bot.send_message(
                message.chat.id,
                "❌ Quilometragem inválida. Informe um número (ex.: 45000):",
                reply_markup=ForceReply(),
            )
            bot.register_next_step_handler(message, receber_quilometragem)
            return
        rascunho.km = km

        bot.send_message(
            message.chat.id,
            "Por favor, tire uma foto do painel mostrando a quilometragem:",
            reply_markup=ForceReply(),
        )
        bot.register_next_step_handler(message, receber_foto)

    def receber_foto(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            _reiniciar(bot, message)
            return

        if message.content_type != "photo":
            bot.send_message(message.chat.id, "❌ Por favor, envie uma foto válida.")
            bot.register_next_step_handler(message, receber_foto)
            return

        file_id = message.photo[-1].file_id
        if _enviar_para_s3(bot, message, file_id, "imagens"):
            rascunho.imagem = f"{file_id}.jpg"
        else:
            bot.send_message(
                message.chat.id,
                "⚠️ Não foi possível salvar a foto agora. A manutenção será registrada sem ela.",
            )

        opcoes = markups_genericos_keyboard(
            [{"identificacao": "Sim"}, {"identificacao": "Não"}], "identificacao"
        )
        bot.send_message(
            message.chat.id,
            "Deseja informar os produtos utilizados?",
            reply_markup=opcoes,
        )
        bot.register_next_step_handler(message, receber_resposta_mostrar_produtos)

    def receber_resposta_mostrar_produtos(message):
        if _rascunho(message.chat.id) is None:
            _reiniciar(bot, message)
            return
        if message.text == "Sim":
            mostrar_checkbox_produtos(message)
        else:
            _perguntar_custo(bot, message)

    def mostrar_checkbox_produtos(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            _reiniciar(bot, message)
            return

        produtos = get_all_produtos_manutencao(rascunho.usuario_id)
        opcoes = [p.descricao_completa for p in produtos]

        if not opcoes:
            bot.send_message(
                message.chat.id,
                "⚠️ Você ainda não possui produtos cadastrados.",
            )
            _perguntar_custo(bot, message)
            return

        def finalizado(chat_id: int, selecionadas: list[str]) -> None:
            ids: list[int] = []
            for descricao_completa in selecionadas:
                produto = get_produto_by_descricao_completa(descricao_completa)
                if produto is not None:
                    ids.append(produto.id)
            if chat_id in _RASCUNHOS:
                _RASCUNHOS[chat_id].produtos = ids
            _perguntar_custo(bot, message)

        start_checkbox(bot, message.chat.id, opcoes, finalizado)

    def receber_custo(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            _reiniciar(bot, message)
            return

        custo = validar_custo(message.text)
        if custo is None:
            bot.send_message(
                message.chat.id,
                "❌ Valor inválido. Informe o custo em reais (ex.: 120,50):",
                reply_markup=ForceReply(),
            )
            bot.register_next_step_handler(message, receber_custo)
            return
        rascunho.custo = custo

        _perguntar_observacoes(bot, message)

    def receber_observacoes(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            _reiniciar(bot, message)
            return

        texto = (message.text or "").strip()
        rascunho.observacao = normalizar_texto_livre(texto, limite=100)

        opcoes = markups_genericos_keyboard(
            [{"identificacao": "Sim"}, {"identificacao": "Não"}], "identificacao"
        )
        bot.send_message(
            message.chat.id,
            "Deseja anexar a nota de serviço ou recibo?",
            reply_markup=opcoes,
        )
        bot.register_next_step_handler(message, receber_resposta_adicionar_nota_servico)

    def receber_resposta_adicionar_nota_servico(message):
        if _rascunho(message.chat.id) is None:
            _reiniciar(bot, message)
            return
        if message.text == "Sim":
            bot.send_message(
                message.chat.id,
                "Por favor, envie a foto da nota/recibo:",
                reply_markup=ForceReply(),
            )
            bot.register_next_step_handler(message, receber_foto_recibo)
        else:
            finalizar_registro(message)

    def receber_foto_recibo(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            _reiniciar(bot, message)
            return

        if message.content_type != "photo":
            bot.send_message(message.chat.id, "❌ Por favor, envie uma foto válida.")
            bot.register_next_step_handler(message, receber_foto_recibo)
            return

        file_id = message.photo[-1].file_id
        if _enviar_para_s3(bot, message, file_id, "imagens"):
            rascunho.imagem_nota_servico = f"{file_id}.jpg"

        finalizar_registro(message)

    # ------------------------------------------------------------------ gravação
    def finalizar_registro(message):
        rascunho = _rascunho(message.chat.id)
        if rascunho is None:
            _reiniciar(bot, message)
            return

        if rascunho.veiculo_id is None or rascunho.data is None or rascunho.servico_id is None:
            bot.send_message(
                message.chat.id,
                "❌ Faltam dados essenciais para registrar a manutenção. Recomece o registro.",
                reply_markup=menu_principal(),
            )
            _RASCUNHOS.pop(message.chat.id, None)
            return

        bot.send_message(message.chat.id, "⏳ Gravando Manutenção...")
        try:
            with get_database().unit_of_work() as session:
                manutencao = Manutencao(
                    data=rascunho.data,
                    veiculo_id=rascunho.veiculo_id,
                    km=rascunho.km,
                    observacao=rascunho.observacao,
                    status="Finalizada",
                    custo=rascunho.custo,
                    imagem=rascunho.imagem,
                    imagemNotaServico=rascunho.imagem_nota_servico,
                )
                session.add(manutencao)
                session.flush()

                session.add(
                    ManutencaoServico(
                        manutencao_id=manutencao.id, servico_id=rascunho.servico_id
                    )
                )
                for produto_id in rascunho.produtos:
                    session.add(
                        ManutencaoProduto(
                            manutencao_id=manutencao.id, produto_id=produto_id
                        )
                    )
        except Exception:
            logger.exception(
                "falha_ao_registrar_manutencao",
                extra={"veiculo_id": rascunho.veiculo_id, "usuario_id": rascunho.usuario_id},
            )
            bot.send_message(
                message.chat.id,
                "😕 Não foi possível registrar a manutenção. Nenhum dado foi gravado. Tente novamente.",
                reply_markup=menu_principal(),
            )
            _RASCUNHOS.pop(message.chat.id, None)
            return

        _RASCUNHOS.pop(message.chat.id, None)
        bot.send_message(message.chat.id, "✅ Manutenção registrada com sucesso!")
        bot.send_message(message.chat.id, "Escolha uma opção:", reply_markup=menu_principal())


def _enviar_para_s3(bot, message, file_id: str, tipo: str) -> bool:
    """Baixa a foto do Telegram e envia ao S3; retorna se deu certo."""
    from lubribot.utils.timing import medir

    try:
        with medir("telegram_s3_upload", file_id=file_id):
            informacoes = bot.get_file(file_id)
            conteudo = bot.download_file(informacoes.file_path)
            url = upload_s3(
                base64=b64.b64encode(conteudo).decode("utf-8"),
                tipo=tipo,
                filename=f"{file_id}.jpg",
            )
        return bool(url)
    except Exception:
        logger.exception("falha_no_upload_da_foto", extra={"file_id": file_id})
        return False
