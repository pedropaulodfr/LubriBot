"""Instância única de banco para a aplicação e para os handlers legados."""

from __future__ import annotations

from functools import lru_cache

from lubribot.config.settings import Settings
from lubribot.database.engine import Database


@lru_cache(maxsize=1)
def get_database() -> Database:
    """Retorna a instância de banco memoizada (lazy: só cria engine no 1º uso)."""
    return Database.from_settings()


def reset_database() -> None:
    """Descarta o cache (usado em testes e em reinicialização)."""
    get_database.cache_clear()


def database_from(settings: Settings) -> Database:
    """Cria um banco a partir de configuração explícita (testes/injeção)."""
    return Database.from_settings(settings)
