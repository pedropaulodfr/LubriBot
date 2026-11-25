"""Trava de instância única usando advisory lock do PostgreSQL.

Uso::

    with AdvisoryLock(db, chave) as adquiriu:
        if adquiriu:
            ...  # seção crítica

A trava é liberada automaticamente se a conexão cair, o que é mais seguro que um
arquivo de lock ou um flag em memória.
"""

from __future__ import annotations

from types import TracebackType

from sqlalchemy import text

from lubribot.database.engine import Database
from lubribot.utils.logging import get_logger

logger = get_logger(__name__)


class AdvisoryLock:
    """Context manager de ``pg_try_advisory_lock`` (não bloqueante)."""

    def __init__(self, db: Database, chave: int) -> None:
        self._db = db
        self._chave = chave
        self._conn = None
        self._adquiriu = False

    def __enter__(self) -> bool:
        try:
            self._conn = self._db.engine.connect()
            resultado = self._conn.execute(
                text("SELECT pg_try_advisory_lock(:chave)"), {"chave": self._chave}
            ).scalar()
            self._adquiriu = bool(resultado)
        except Exception:
            # Banco sem suporte (ex.: SQLite em teste) não deve impedir o ciclo.
            logger.warning("advisory_lock_indisponivel", extra={"chave": self._chave})
            self._adquiriu = True
        return self._adquiriu

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._conn is None:
            return
        try:
            if self._adquiriu:
                self._conn.execute(
                    text("SELECT pg_advisory_unlock(:chave)"), {"chave": self._chave}
                )
        except Exception:  # pragma: no cover - conexão já encerrada
            logger.warning("advisory_unlock_falhou", extra={"chave": self._chave})
        finally:
            self._conn.close()
            self._conn = None
