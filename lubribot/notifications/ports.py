"""Portas (interfaces) do fluxo de notificações.

As portas permitem testar planejador e despachante com dublês em memória, sem
banco e sem Telegram — que é como a suíte de testes roda no CI.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from lubribot.notifications.models import (
    CandidatoVeiculo,
    DadosNotificacao,
    NotificacaoPendente,
)


class NotificationRepositoryPort(Protocol):
    """Operações de persistência usadas pelo planejador e pelo despachante."""

    def listar_candidatos(self) -> list[CandidatoVeiculo]: ...

    def criar_se_nao_existir(self, dados: DadosNotificacao) -> bool:
        """Cria a notificação; retorna False se a chave já existir."""
        ...

    def listar_pendentes(self, agora: datetime) -> list[NotificacaoPendente]: ...

    def marcar_enviada(self, notificacao_id: int, agora: datetime) -> None: ...

    def registrar_falha_temporaria(
        self,
        notificacao_id: int,
        *,
        tentativas: int,
        proxima_tentativa_em: datetime,
        erro: str,
        agora: datetime,
    ) -> None: ...

    def marcar_falha_definitiva(
        self, notificacao_id: int, *, erro: str, agora: datetime
    ) -> None: ...

    def cancelar(self, notificacao_id: int, *, motivo: str, agora: datetime) -> None: ...


class SenderPort(Protocol):
    """Envio de mensagem para o usuário final."""

    def enviar(self, chat_id: int, texto: str) -> SendOutcome: ...


class SendOutcome:
    """Resultado de uma tentativa de envio.

    Atributos:
        ok: mensagem entregue.
        permanente: falha definitiva (ex.: usuário bloqueou o bot).
        retry_after: segundos sugeridos pelo Telegram (HTTP 429), se houver.
        erro: descrição curta da falha (nunca contém credencial).
    """

    __slots__ = ("ok", "permanente", "retry_after", "erro")

    def __init__(
        self,
        *,
        ok: bool = False,
        permanente: bool = False,
        retry_after: int | None = None,
        erro: str | None = None,
    ) -> None:
        self.ok = ok
        self.permanente = permanente
        self.retry_after = retry_after
        self.erro = erro

    @classmethod
    def sucesso(cls) -> SendOutcome:
        return cls(ok=True)

    @classmethod
    def transitorio(cls, erro: str, retry_after: int | None = None) -> SendOutcome:
        return cls(ok=False, permanente=False, retry_after=retry_after, erro=erro)

    @classmethod
    def definitivo(cls, erro: str) -> SendOutcome:
        return cls(ok=False, permanente=True, erro=erro)

    def __repr__(self) -> str:  # pragma: no cover - conveniência de debug
        return (
            f"SendOutcome(ok={self.ok}, permanente={self.permanente}, "
            f"retry_after={self.retry_after}, erro={self.erro!r})"
        )
