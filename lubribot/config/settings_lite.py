"""Configuração sem Pydantic (perfil "lite", ex.: Termux/ARM).

Motivo: em Android ARM 32 bits não há wheel de ``pydantic-core``. Esta variante
lê as mesmas variáveis de ambiente, aplica as mesmas regras de obrigatoriedade e
expõe a mesma interface pública (``telegram_token``, ``database_url``, etc.).

Diferenças conscientes:
- erros são ``ValueError``/``ConfigurationError`` (não ``ValidationError``);
- segredos ficam como ``str`` simples em memória (mesmo processo que já os lê do
  ambiente — não há ganho real de proteção no dispositivo).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Literal

from lubribot.config.settings_common import PROJECT_ROOT, normalizar_ambiente
from lubribot.errors import ConfigurationError

__all__ = ["Settings"]

_VERDADEIROS = {"1", "true", "sim", "yes", "on", "y"}
_NAO_ACEITOS = {"0", "false", "nao", "não", "no", "off", "n"}


def _texto(env: Mapping[str, str], chave: str, padrao: str | None = None) -> str | None:
    valor = env.get(chave)
    if valor is None:
        return padrao
    valor = valor.strip()
    return valor if valor else padrao


def _inteiro(
    env: Mapping[str, str],
    chave: str,
    padrao: int | None,
    *,
    minimo: int | None = None,
    maximo: int | None = None,
    opcional: bool = False,
) -> int | None:
    bruto = _texto(env, chave)
    if bruto is None:
        return None if opcional else padrao
    try:
        valor = int(bruto)
    except ValueError as exc:
        raise ValueError(f"{chave} deve ser um número inteiro (recebido: {bruto!r})") from exc
    if minimo is not None and valor < minimo:
        raise ValueError(f"{chave} deve ser >= {minimo}")
    if maximo is not None and valor > maximo:
        raise ValueError(f"{chave} deve ser <= {maximo}")
    return valor


def _booleano(env: Mapping[str, str], chave: str, padrao: bool) -> bool:
    bruto = _texto(env, chave)
    if bruto is None:
        return padrao
    normalizado = bruto.lower()
    if normalizado in _VERDADEIROS:
        return True
    if normalizado in _NAO_ACEITOS:
        return False
    raise ValueError(f"{chave} deve ser booleano (recebido: {bruto!r})")


def _carregar_dotenv() -> None:
    """Carrega ``.env`` do projeto, se ``python-dotenv`` estiver disponível."""
    try:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")
    except Exception:  # pragma: no cover - ausência do dotenv é aceitável
        return


class Settings:
    """Configuração da aplicação (implementação sem Pydantic)."""

    def __init__(self, env: Mapping[str, str] | None = None) -> None:
        if env is None:
            _carregar_dotenv()
            env = os.environ

        self.ambiente = normalizar_ambiente(_texto(env, "AMBIENTE", "QA") or "QA")

        self.token_producao = _texto(env, "TOKEN")
        self.token_qa = _texto(env, "TOKEN_QA")

        self.db_url_producao = _texto(env, "STRING_CONNECTION")
        self.db_url_qa = _texto(env, "STRING_CONNECTION_LOCAL")

        self.gemini_api_key = _texto(env, "GEMINI_ApiKey")
        self.aws_access_key = _texto(env, "AWS_AccessKey")
        self.aws_secret_key = _texto(env, "AWS_SecretKey")
        self.aws_region = _texto(env, "AWS_Region")
        self.aws_bucket_name = _texto(env, "AWS_BucketName")

        self.notificacoes_habilitadas = _booleano(env, "NOTIFICACOES_HABILITADAS", True)
        self.intervalo_notificacao_minutos = _inteiro(
            env, "INTERVALO_NOTIFICACAO", 60, minimo=1
        )
        self.intervalo_manutencao_padrao_dias = _inteiro(
            env, "INTERVALO_MANUTENCAO_DIAS", 180, minimo=1, maximo=3650
        )
        self.intervalo_km_padrao = _inteiro(
            env, "INTERVALO_KM_PADRAO", None, minimo=1, maximo=500_000, opcional=True
        )
        self.notificacoes_max_tentativas = _inteiro(
            env, "NOTIFICACOES_MAX_TENTATIVAS", 5, minimo=1, maximo=50
        )
        self.notificacoes_backoff_base_segundos = _inteiro(
            env, "NOTIFICACOES_BACKOFF_BASE_SEGUNDOS", 60, minimo=1
        )

        self.ia_diagnosticos_por_dia = _inteiro(env, "IA_DIAGNOSTICOS_DIA", 3, minimo=1, maximo=100)
        self.ia_dicas_por_dia = _inteiro(env, "IA_DICAS_DIA", 10, minimo=1, maximo=100)

        self.db_pool_size = _inteiro(env, "DB_POOL_SIZE", 5, minimo=1, maximo=50)
        self.db_max_overflow = _inteiro(env, "DB_MAX_OVERFLOW", 10, minimo=0, maximo=100)
        self.db_pool_recycle_segundos = _inteiro(
            env, "DB_POOL_RECYCLE_SEGUNDOS", 1800, minimo=60
        )
        self.db_pool_pre_ping = _booleano(env, "DB_POOL_PRE_PING", True)
        self.db_echo = _booleano(env, "DB_ECHO", False)

        self.log_level = (_texto(env, "LOG_LEVEL", "INFO") or "INFO").strip().upper()
        if self.log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(f"nível de log inválido: {self.log_level!r}")
        self.log_json = _booleano(env, "LOG_JSON", False)
        self.debug_commands = _booleano(env, "DEBUG_COMMANDS", False)
        self.http_habilitado = _booleano(env, "HTTP_HABILITADO", True)
        self.http_host = _texto(env, "HTTP_HOST", "0.0.0.0") or "0.0.0.0"
        self.http_port = _inteiro(env, "PORT", 10000, minimo=1, maximo=65535)
        self.scheduler_lock_key = _inteiro(env, "SCHEDULER_LOCK_KEY", 872_001_337)

        self._validar_segredos()

    # ---------------------------------------------------------------- validação
    def _validar_segredos(self) -> None:
        if self.is_producao:
            if self.token_producao is None:
                raise ValueError("AMBIENTE=PRODUÇÃO exige TOKEN configurado")
            if self.db_url_producao is None:
                raise ValueError("AMBIENTE=PRODUÇÃO exige STRING_CONNECTION configurada")
        else:
            if self.token_qa is None and self.token_producao is None:
                raise ValueError("Nenhum token do Telegram configurado (TOKEN_QA ou TOKEN)")
            if self.db_url_qa is None and self.db_url_producao is None:
                raise ValueError(
                    "Nenhuma string de conexão configurada "
                    "(STRING_CONNECTION_LOCAL ou STRING_CONNECTION)"
                )

    # ---------------------------------------------------------------- derivados
    @property
    def is_producao(self) -> bool:
        return self.ambiente in {"PRODUCAO", "PROD"}

    @property
    def ambiente_rotulo(self) -> Literal["producao", "qa"]:
        return "producao" if self.is_producao else "qa"

    @property
    def telegram_token(self) -> str:
        token = self.token_producao if self.is_producao else self.token_qa
        if token is None:
            token = self.token_producao
        if token is None:
            raise ConfigurationError("Token do Telegram não configurado")
        return token

    @property
    def database_url(self) -> str:
        url = self.db_url_producao if self.is_producao else self.db_url_qa
        if url is None:
            url = self.db_url_producao
        if url is None:
            raise ConfigurationError("String de conexão do banco não configurada")
        return url

    @property
    def intervalo_notificacao_segundos(self) -> int:
        return self.intervalo_notificacao_minutos * 60
