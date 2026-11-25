"""DTOs do fluxo de notificações (independentes do ORM e do Telegram)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class CandidatoVeiculo:
    """Veículo ativo com dados necessários para decidir a notificação.

    Vem de duas consultas em lote (candidatos + intervalos), nunca de N+1.
    """

    veiculo_id: int
    usuario_id: int
    telegram_id: int | None
    nome_usuario: str | None
    receber_notificacoes: bool | None
    dias_notificacao: int | None
    ultima_manutencao_id: int
    ultima_data: date
    intervalos_dias: tuple[int | None, ...]
    descricao: str


@dataclass(frozen=True, slots=True)
class DadosNotificacao:
    """Dados para criar uma notificação persistida."""

    chave: str
    tipo: str
    titulo: str
    conteudo: str
    usuario_id: int
    veiculo_id: int
    manutencao_id: int
    data_notificacao: date


@dataclass(frozen=True, slots=True)
class NotificacaoPendente:
    """Notificação pronta para despacho."""

    id: int
    chave: str | None
    conteudo: str
    tentativas: int
    proxima_tentativa_em: datetime | None
    telegram_id: int | None
    usuario_id: int
    receber_notificacoes: bool | None


@dataclass(slots=True)
class PlanningResult:
    """Contadores de um ciclo de planejamento (para log e teste)."""

    avaliados: int = 0
    criadas: int = 0
    ja_existentes: int = 0
    sem_confirmacao: int = 0
    fora_da_janela: int = 0
    erros: int = 0

    def texto(self) -> str:
        return (
            f"avaliados={self.avaliados} criadas={self.criadas} "
            f"ja_existentes={self.ja_existentes} sem_confirmacao={self.sem_confirmacao} "
            f"fora_da_janela={self.fora_da_janela} erros={self.erros}"
        )


@dataclass(slots=True)
class DispatchResult:
    """Contadores de um ciclo de despacho."""

    pendentes: int = 0
    enviadas: int = 0
    canceladas: int = 0
    reagendadas: int = 0
    falhas_definitivas: int = 0
    falhas_temporarias: int = 0
    detalhes: list[str] = field(default_factory=list)

    def texto(self) -> str:
        return (
            f"pendentes={self.pendentes} enviadas={self.enviadas} "
            f"canceladas={self.canceladas} reagendadas={self.reagendadas} "
            f"falhas_definitivas={self.falhas_definitivas} "
            f"falhas_temporarias={self.falhas_temporarias}"
        )
