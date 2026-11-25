"""Validação e normalização de entradas (F7).

Centraliza o que antes era validação ad-hoc dentro dos handlers, para que as
mesmas regras valham em qualquer fluxo e sejam testáveis sem Telegram.
"""

from __future__ import annotations

import re

PLACA_ANTIGA = re.compile(r"^[A-Z]{3}[0-9]{4}$")
PLACA_MERCOSUL = re.compile(r"^[A-Z]{3}[0-9][A-Z][0-9]{2}$")
ANO_MINIMO = 1900
ANO_MAXIMO = 2100
KM_MAXIMO = 3_000_000
CUSTO_MAXIMO = 10_000_000.0


def normalizar_placa(texto: str | None) -> str:
    """Remove separadores, espaços e caixa. Não valida formato."""
    if not texto:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", texto).upper()


def validar_placa(texto: str | None) -> str | None:
    """Retorna a placa normalizada se válida (padrão antigo ou Mercosul)."""
    placa = normalizar_placa(texto)
    if PLACA_ANTIGA.match(placa) or PLACA_MERCOSUL.match(placa):
        return placa
    return None


def validar_ano(texto: str | None) -> str | None:
    """Retorna o ano (4 dígitos) se estiver numa faixa plausível."""
    if not texto:
        return None
    ano = texto.strip()
    if not ano.isdigit() or len(ano) != 4:
        return None
    numero = int(ano)
    if ANO_MINIMO <= numero <= ANO_MAXIMO:
        return ano
    return None


def validar_km(texto: str | None) -> int | None:
    """Quilometragem inteira não negativa (aceita separador de milhar)."""
    if texto is None:
        return None
    limpo = texto.strip().replace(".", "").replace(" ", "")
    if not limpo.isdigit():
        return None
    valor = int(limpo)
    if 0 <= valor <= KM_MAXIMO:
        return valor
    return None


def validar_custo(texto: str | None) -> float | None:
    """Valor monetário em reais (aceita vírgula ou ponto decimal)."""
    if texto is None:
        return None
    limpo = texto.strip().replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    # "1.200,50" -> removemos pontos de milhar e trocamos vírgula por ponto.
    try:
        valor = float(limpo)
    except ValueError:
        return None
    if 0 <= valor <= CUSTO_MAXIMO:
        return round(valor, 2)
    return None


def normalizar_renavam(texto: str | None) -> str | None:
    """RENAVAM opcional: 9 a 11 dígitos. '.'/vazio viram None."""
    if texto is None:
        return None
    limpo = re.sub(r"[^0-9]", "", texto)
    if not limpo:
        return None
    if 9 <= len(limpo) <= 11:
        return limpo
    return None


def normalizar_texto_livre(texto: str | None, *, limite: int = 100) -> str | None:
    """Texto livre opcional: strip, limite de tamanho e '.' vira None."""
    if texto is None:
        return None
    limpo = texto.strip()
    if limpo in {"", "."}:
        return None
    return limpo[:limite]
