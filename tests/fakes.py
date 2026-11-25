"""Dublês (test doubles) das portas do fluxo de notificações."""

from __future__ import annotations

from datetime import date, datetime

from lubribot.notifications.models import (
    CandidatoVeiculo,
    DadosNotificacao,
    NotificacaoPendente,
)
from lubribot.notifications.ports import SendOutcome


def candidato(
    *,
    veiculo_id: int = 1,
    usuario_id: int = 10,
    telegram_id: int | None = 555,
    nome_usuario: str | None = "Ana",
    receber_notificacoes: bool | None = True,
    dias_notificacao: int | None = 7,
    ultima_manutencao_id: int = 100,
    ultima_data: date = date(2026, 1, 1),
    intervalos_dias: tuple[int | None, ...] = (180,),
    descricao: str = "Honda Bros Vermelha 2022 (ABC1D23)",
) -> CandidatoVeiculo:
    return CandidatoVeiculo(
        veiculo_id=veiculo_id,
        usuario_id=usuario_id,
        telegram_id=telegram_id,
        nome_usuario=nome_usuario,
        receber_notificacoes=receber_notificacoes,
        dias_notificacao=dias_notificacao,
        ultima_manutencao_id=ultima_manutencao_id,
        ultima_data=ultima_data,
        intervalos_dias=intervalos_dias,
        descricao=descricao,
    )


def pendente(
    *,
    id: int = 1,
    chave: str | None = "ProximaManutencao:100",
    conteudo: str = "mensagem",
    tentativas: int = 0,
    proxima_tentativa_em: datetime | None = None,
    telegram_id: int | None = 555,
    usuario_id: int = 10,
    receber_notificacoes: bool | None = True,
) -> NotificacaoPendente:
    return NotificacaoPendente(
        id=id,
        chave=chave,
        conteudo=conteudo,
        tentativas=tentativas,
        proxima_tentativa_em=proxima_tentativa_em,
        telegram_id=telegram_id,
        usuario_id=usuario_id,
        receber_notificacoes=receber_notificacoes,
    )


class FakeNotificationRepository:
    """Repositório em memória com registro das chamadas."""

    def __init__(
        self,
        candidatos: list[CandidatoVeiculo] | None = None,
        pendentes: list[NotificacaoPendente] | None = None,
        *,
        chaves_existentes: set[str] | None = None,
        falhar_ao_criar: bool = False,
    ) -> None:
        self.candidatos = candidatos or []
        self.pendentes = pendentes or []
        self.chaves_existentes = chaves_existentes or set()
        self.falhar_ao_criar = falhar_ao_criar

        self.criadas: list[DadosNotificacao] = []
        self.enviadas: list[int] = []
        self.canceladas: list[tuple[int, str]] = []
        self.falhas_temporarias: list[dict] = []
        self.falhas_definitivas: list[tuple[int, str]] = []

    # leitura ---------------------------------------------------------------
    def listar_candidatos(self):
        return list(self.candidatos)

    def listar_pendentes(self, agora):
        return list(self.pendentes)

    # escrita ---------------------------------------------------------------
    def criar_se_nao_existir(self, dados: DadosNotificacao) -> bool:
        if self.falhar_ao_criar:
            raise RuntimeError("falha simulada no banco")
        if dados.chave in self.chaves_existentes:
            return False
        self.chaves_existentes.add(dados.chave)
        self.criadas.append(dados)
        return True

    def marcar_enviada(self, notificacao_id: int, agora: datetime) -> None:
        self.enviadas.append(notificacao_id)

    def registrar_falha_temporaria(
        self,
        notificacao_id: int,
        *,
        tentativas: int,
        proxima_tentativa_em: datetime,
        erro: str,
        agora: datetime,
    ) -> None:
        self.falhas_temporarias.append(
            {
                "id": notificacao_id,
                "tentativas": tentativas,
                "proxima": proxima_tentativa_em,
                "erro": erro,
                "agora": agora,
            }
        )

    def marcar_falha_definitiva(
        self, notificacao_id: int, *, erro: str, agora: datetime
    ) -> None:
        self.falhas_definitivas.append((notificacao_id, erro))

    def cancelar(self, notificacao_id: int, *, motivo: str, agora: datetime) -> None:
        self.canceladas.append((notificacao_id, motivo))


class FakeSender:
    """Enviador com fila de resultados pré-programados."""

    def __init__(self, resultados: list[SendOutcome] | None = None) -> None:
        self._resultados = list(resultados or [])
        self.chamadas: list[tuple[int, str]] = []

    def enviar(self, chat_id: int, texto: str) -> SendOutcome:
        self.chamadas.append((chat_id, texto))
        if self._resultados:
            return self._resultados.pop(0)
        return SendOutcome.sucesso()
