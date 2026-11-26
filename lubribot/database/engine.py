"""Fábrica de engine, sessões e unidade de trabalho.

Pontos importantes:
- ``pool_pre_ping`` evita usar conexão morta depois de o Supabase reciclar.
- ``expire_on_commit=False`` mantém atributos legíveis após o commit — os
  handlers atuais devolvem objetos ORM para fora da camada de dados.
- ``unit_of_work`` garante rollback em exceção e ``close`` sempre: era o que
  faltava no código legado, que deixava transações abertas em caminhos de erro.
"""

from __future__ import annotations

import importlib.util
import os
import ssl
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from lubribot.config.settings import Settings, get_settings
from lubribot.utils.logging import get_logger

logger = get_logger(__name__)


def _driver_disponivel(nome: str) -> bool:
    try:
        return importlib.util.find_spec(nome) is not None
    except (ImportError, ValueError):  # pragma: no cover - ambiente exótico
        return False


def _ajustar_url(url: str) -> str:
    """Escolhe o driver disponível.

    Em Android/Termux ARM 32 bits não existe wheel de ``psycopg2``; nesse caso o
    mesmo DSN PostgreSQL é servido pelo driver puro ``pg8000``.
    """
    if url.startswith("postgresql://") and not _driver_disponivel("psycopg2"):
        if _driver_disponivel("pg8000"):
            return url.replace("postgresql://", "postgresql+pg8000://", 1)
        logger.error("nenhum_driver_postgres_disponivel")
    return url


def _ler_booleano(nome: str, padrao: bool) -> bool:
    valor = os.getenv(nome)
    if valor is None or not valor.strip():
        return padrao
    return valor.strip().lower() in {"1", "true", "sim", "yes", "on"}


def _connect_args(url: str) -> dict:
    """Argumentos específicos do driver (TLS para pg8000 em host remoto).

    O pooler do Supabase usa CA própria, que não está nos repositórios do Termux.
    O padrão é TLS **sem validação de CA** (equivalente a ``sslmode=require``):
    o tráfego é cifrado, mas não há pinning. Para validação completa, aponte
    ``DB_SSL_CA`` para o ``prod-ca-2021.crt`` do Supabase.
    """
    if "pg8000" not in url:
        return {}
    host = (make_url(url).host or "").lower()
    argumentos: dict = {"timeout": 20}
    if not host or host in {"localhost", "127.0.0.1"}:
        return argumentos

    ca = os.getenv("DB_SSL_CA")
    verificar = _ler_booleano("DB_SSL_VERIFY", bool(ca))
    try:
        contexto = ssl.create_default_context(cafile=ca) if ca else ssl.create_default_context()
    except Exception:
        contexto = ssl.create_default_context()
    if not verificar:
        contexto.check_hostname = False
        contexto.verify_mode = ssl.CERT_NONE
        logger.warning(
            "tls_sem_verificacao_de_ca",
            extra={"host": host, "dica": "defina DB_SSL_CA para validar o certificado"},
        )
    argumentos["ssl_context"] = contexto
    return argumentos


class Database:
    """Encapsula o engine e o sessionmaker de uma conexão PostgreSQL."""

    def __init__(self, url: str, *, settings: Settings | None = None) -> None:
        cfg = settings
        url = _ajustar_url(url)
        self._engine: Engine = create_engine(
            url,
            pool_pre_ping=cfg.db_pool_pre_ping if cfg else True,
            pool_size=cfg.db_pool_size if cfg else 5,
            max_overflow=cfg.db_max_overflow if cfg else 10,
            pool_recycle=cfg.db_pool_recycle_segundos if cfg else 1800,
            echo=cfg.db_echo if cfg else False,
            future=True,
            connect_args=_connect_args(url),
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
