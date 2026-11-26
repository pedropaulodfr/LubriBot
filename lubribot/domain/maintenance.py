"""Regras de negócio puras — sem banco, sem Telegram, sem rede.

Este módulo existe para que a regra mais crítica do produto (quando avisar sobre
a próxima manutenção) seja testável sem infraestrutura.

Regra reconstruída a partir do comportamento documentado e do código legado:

    proxima_data = ultima_manutencao.data + max(intervalo_dias dos serviços)

- ``intervalo_dias`` de cada serviço vem de ``servicos.intervaloDias`` quando
  preenchido; caso contrário usa o padrão configurado
  (``INTERVALO_MANUTENCAO_DIAS``, 180 dias).
- A notificação entra na janela quando ``hoje <= proxima_data <= hoje + antecedencia``.
- A chave de idempotência é ``ProximaManutencao:<manutencao_id>``: no máximo uma
  notificação por manutenção, independentemente de quantas vezes o job rodar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

TIPO_PROXIMA_MANUTENCAO = "ProximaManutencao"
TITULO_PROXIMA_MANUTENCAO = "Proxima Manutencao"
STATUS_ATIVO = "Ativo"
STATUS_FINALIZADA = "Finalizada"

INTERVALO_PADRAO_DIAS = 180
ANTECEDENCIA_PADRAO_DIAS = 7


@dataclass(frozen=True, slots=True)
class MaintenanceSchedule:
    """Resultado do cálculo de agendamento para um veículo."""

    ultima_manutencao_id: int
    ultima_data: date
    intervalo_dias: int
    proxima_data: date
    ultima_km: int | None = None
    intervalo_km: int | None = None
    proxima_km: int | None = None

    @property
    def dias_restantes(self) -> int:
        return (self.proxima_data - date.today()).days


def intervalo_efetivo(
    intervalos: list[int | None] | tuple[int | None, ...] | None,
    *,
    padrao: int = INTERVALO_PADRAO_DIAS,
) -> int:
    """Retorna o maior intervalo válido, ou o padrão quando não há nenhum.

    >>> intervalo_efetivo([90, 180, None])
    180
    >>> intervalo_efetivo([None], padrao=30)
    30
    >>> intervalo_efetivo([])
    180
    >>> intervalo_efetivo([0, -5])
    180
    """
    validos = [i for i in (intervalos or []) if i is not None and i > 0]
    return max(validos) if validos else padrao


def calcular_agendamento(
    ultima_manutencao_id: int,
    ultima_data: date,
    intervalos: list[int | None] | None,
    *,
    padrao: int = INTERVALO_PADRAO_DIAS,
) -> MaintenanceSchedule:
    """Calcula a data da próxima manutenção de um veículo."""
    intervalo = intervalo_efetivo(intervalos, padrao=padrao)
    return MaintenanceSchedule(
        ultima_manutencao_id=ultima_manutencao_id,
        ultima_data=ultima_data,
        intervalo_dias=intervalo,
        proxima_data=ultima_data + timedelta(days=intervalo),
    )


def esta_na_janela(
    proxima_data: date,
    hoje: date,
    antecedencia_dias: int | None,
) -> bool:
    """Indica se a próxima manutenção está dentro da janela de aviso.

    >>> from datetime import date
    >>> esta_na_janela(date(2026, 1, 10), date(2026, 1, 5), 7)
    True
    >>> esta_na_janela(date(2026, 1, 10), date(2026, 1, 1), 7)
    False
    >>> esta_na_janela(date(2025, 12, 30), date(2026, 1, 1), 7)  # já venceu
    False
    """
    antecedencia = antecedencia_dias if antecedencia_dias and antecedencia_dias > 0 else ANTECEDENCIA_PADRAO_DIAS
    return hoje <= proxima_data <= hoje + timedelta(days=antecedencia)


def chave_notificacao(manutencao_id: int, tipo: str = TIPO_PROXIMA_MANUTENCAO) -> str:
    """Chave de idempotência de uma notificação."""
    return f"{tipo}:{manutencao_id}"


def descricao_veiculo(
    fabricante: str | None,
    modelo: str | None,
    cor: str | None,
    ano: str | None,
    placa: str | None,
) -> str:
    """Monta a descrição legível do veículo, sem campos vazios."""
    partes = [fabricante or "", modelo or "", cor or ""]
    base = " ".join(p for p in partes if p).strip()
    complemento = []
    if ano:
        complemento.append(str(ano))
    if placa:
        complemento.append(f"({placa})")
    if complemento:
        return f"{base} {' '.join(complemento)}".strip() if base else " ".join(complemento)
    return base or "veículo"


def intervalo_km_efetivo(
    intervalos: list[int | None] | tuple[int | None, ...] | None,
    *,
    padrao: int | None = None,
) -> int | None:
    """Maior intervalo em km válido, ou ``padrao`` (que por omissão é None).

    >>> intervalo_km_efetivo([5000, 10000, None])
    10000
    >>> intervalo_km_efetivo([]) is None
    True
    >>> intervalo_km_efetivo([0, -1]) is None
    True
    """
    validos = [i for i in (intervalos or []) if i is not None and i > 0]
    if validos:
        return max(validos)
    return padrao


def calcular_vencimento_km(
    ultima_km: int | None,
    intervalos_km: list[int | None] | tuple[int | None, ...] | None,
    *,
    padrao: int | None = None,
) -> int | None:
    """Odômetro em que a próxima manutenção vence (None se não há dados).

    >>> calcular_vencimento_km(10000, [5000])
    15000
    >>> calcular_vencimento_km(None, [5000]) is None
    True
    >>> calcular_vencimento_km(10000, [None]) is None
    True
    """
    if ultima_km is None:
        return None
    intervalo = intervalo_km_efetivo(intervalos_km, padrao=padrao)
    if intervalo is None:
        return None
    return ultima_km + intervalo


def km_vencido(km_atual: int | None, proxima_km: int | None) -> bool:
    """Indica se o odômetro informado já alcançou (ou passou) o vencimento.

    >>> km_vencido(15000, 15000)
    True
    >>> km_vencido(14999, 15000)
    False
    >>> km_vencido(None, 15000)
    False
    """
    if km_atual is None or proxima_km is None:
        return False
    return km_atual >= proxima_km


def montar_conteudo_notificacao(
    nome_usuario: str | None,
    veiculo: str,
    proxima_data: date | None = None,
    *,
    proxima_km: int | None = None,
) -> str:
    """Mensagem enviada ao usuário, por data e/ou por quilometragem."""
    saudacao = f"Ola, {nome_usuario}!" if nome_usuario else "Ola!"
    partes: list[str] = []

    if proxima_data is not None:
        partes.append(
            f"A data da proxima manutencao do seu veiculo {veiculo} e: "
            f"{proxima_data.strftime('%d/%m/%Y')}."
        )
    if proxima_km is not None:
        partes.append(
            f"O seu veiculo {veiculo} atingiu {proxima_km:,} km,"
            " dentro do intervalo de manutencao recomendado.".replace(",", ".")
        )
    if not partes:
        partes.append(f"Esta na hora de revisar o seu veiculo {veiculo}.")
    return f"{saudacao} {' '.join(partes)}"
