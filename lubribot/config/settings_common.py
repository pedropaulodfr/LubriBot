"""Utilitários de configuração compartilhados pelas variantes (pydantic/lite)."""

from __future__ import annotations

import unicodedata
from pathlib import Path

from lubribot.errors import ConfigurationError

PROJECT_ROOT = Path(__file__).resolve().parents[2]

__all__ = ["PROJECT_ROOT", "ConfigurationError", "normalizar_ambiente"]


def normalizar_ambiente(valor: str) -> str:
    """Normaliza o nome do ambiente removendo acentos, espaços e caixa.

    >>> normalizar_ambiente("PRODUÇÃO")
    'PRODUCAO'
    >>> normalizar_ambiente(" producao ")
    'PRODUCAO'
    """
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", valor) if not unicodedata.combining(c)
    )
    return sem_acento.strip().upper()
