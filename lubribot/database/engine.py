"""Fábrica de engine, sessões e unidade de trabalho.

Pontos importantes:
- ``pool_pre_ping`` evita usar conexão morta depois de o Supabase reciclar.
- ``expire_on_commit=False`` mantém atributos legíveis após o commit — os
  handlers atuais devolvem objetos ORM para fora da camada de dados.
- ``unit_of_work`` garante rollback em exceção e ``close`` sempre: era o que
  faltava no código legado, que deixava transações abertas em caminhos de erro.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from lubribot.config.settings import Settings, get_settings
from lubribot.utils.logging import get_logger

logger = get_logger(__name__)


class Database:
    """Encapsula o engine e o sessionmaker de uma conexão PostgreSQL."""

    def __init__(self, url: str, *, settings: Settings | None = None) -> None:
        cfg = settings
        self._engine: Engine = create_engine(
            url,
            pool_pre_ping=cfg.db_pool_pre_ping if cfg else True,
            pool_size=cfg.db_pool_size if cfg else 5,
            max_overflow=cfg.db_max_overflow if cfg else 10,
            pool_recycle=cfg.db_pool_recycle_segundos if cfg else 1800,
            echo=cfg.db_echo if cfg else False,
            future=True,
        )
        self.session_factory: sessionmaker[Session] = sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            autoflush=False,
        )

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> Database:
        cfg = settings or get_settings()
        return cls(cfg.database_url, settings=cfg)

    @classmethod
    def from_url(cls, url: str, settings: Settings | None = None) -> Database:
        """Cria a partir de uma URL explícita (testes, scripts, ferramentas)."""
        return cls(url, settings=settings)

    @property
    def engine(self) -> Engine:
        return self._engine

    def session(self) -> Session:
        """Cria uma sessão avulsa (uso em scripts e compatibilidade)."""
        return self.session_factory()

    @contextmanager
    def unit_of_work(self, *, commit: bool = True) -> Iterator[Session]:
        """Abre uma sessão com commit/rollback automáticos.

        Uso::

            with db.unit_of_work() as session:
                session.add(entidade)
        """
        sessao = self.session_factory()
        try:
            yield sessao
            if commit:
                sessao.commit()
        except Exception:
            sessao.rollback()
            logger.exception("unidade_de_trabalho_rollback")
            raise
        finally:
            sessao.close()

    def dispose(self) -> None:
        """Fecha o pool (shutdown gracioso)."""
        self._engine.dispose()
