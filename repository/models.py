"""Compatibilidade com os handlers legados.

Os modelos agora vivem em :mod:`lubribot.models` (fonte única) e a sessão vem do
pool gerenciado em :mod:`lubribot.database`. Este módulo existe apenas para que os
imports antigos (``from repository.models import Usuario, _Session``) continuem
funcionando durante a migração incremental da fase F5.

Diferenças importantes em relação ao arquivo antigo:
- **não** roda ``Base.metadata.create_all`` no import (o schema é do Alembic);
- não cria um engine próprio (o pool é compartilhado com o resto da aplicação).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from lubribot.database.runtime import get_database
from lubribot.models import *  # noqa: F401,F403 (reexporta todos os modelos)
from lubribot.models import Base  # noqa: F401


class _LazySessionFactory:
    """Callable que devolve uma sessão do pool no momento do uso."""

    def __call__(self) -> Session:
        return get_database().session()


_Session = _LazySessionFactory()


def __getattr__(nome: str):
    """Resolve ``engine`` sob demanda, sem abrir conexão na importação."""
    if nome == "engine":
        return get_database().engine
    raise AttributeError(f"módulo {__name__!r} não tem atributo {nome!r}")
