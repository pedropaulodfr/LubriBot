"""Configuração central da aplicação.

Regras:
- Nenhuma credencial vive no código. Tudo vem do ambiente (ou de `.env` local).
- A configuração é validada no boot: se faltar algo obrigatório, o processo falha
  de forma explícita em vez de subir num ambiente errado.
- O valor de ``AMBIENTE`` é normalizado (aceita "PRODUÇÃO", "PRODUCAO",
  "production", com espaços e acentos), eliminando o risco de o bot subir com o
  token de QA em produção por causa de acentuação.
"""

from __future__ import annotations

import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ConfigurationError(RuntimeError):
    """Erro de configuração que impede a aplicação de iniciar com segurança."""


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


class Settings(BaseSettings):
    """Configuração da aplicação carregada do ambiente."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    # ---------------------------------------------------------------- ambiente
    ambiente: str = Field(default="QA", validation_alias="AMBIENTE")

    # ---------------------------------------------------------------- telegram
    token_producao: SecretStr | None = Field(default=None, validation_alias="TOKEN")
    token_qa: SecretStr | None = Field(default=None, validation_alias="TOKEN_QA")

    # ---------------------------------------------------------------- banco
    db_url_producao: SecretStr | None = Field(
        default=None, validation_alias="STRING_CONNECTION"
    )
    db_url_qa: SecretStr | None = Field(
        default=None, validation_alias="STRING_CONNECTION_LOCAL"
    )

    # ---------------------------------------------------------------- integrações
    gemini_api_key: SecretStr | None = Field(default=None, validation_alias="GEMINI_ApiKey")
    aws_access_key: SecretStr | None = Field(default=None, validation_alias="AWS_AccessKey")
    aws_secret_key: SecretStr | None = Field(default=None, validation_alias="AWS_SecretKey")
    aws_region: str | None = Field(default=None, validation_alias="AWS_Region")
    aws_bucket_name: str | None = Field(default=None, validation_alias="AWS_BucketName")

    # ---------------------------------------------------------------- notificações
    notificacoes_habilitadas: bool = True
    intervalo_notificacao_minutos: int = Field(default=60, ge=1, validation_alias="INTERVALO_NOTIFICACAO")
    intervalo_manutencao_padrao_dias: int = Field(
        default=180,
        ge=1,
        le=3650,
        validation_alias="INTERVALO_MANUTENCAO_DIAS",
    )
    # Intervalo padrão em km quando o serviço não define ``intervaloKm``.
    # Vazio/ausente = notificação por km desabilitada (comportamento seguro).
    intervalo_km_padrao: int | None = Field(
        default=None, ge=1, le=500_000, validation_alias="INTERVALO_KM_PADRAO"
    )
    notificacoes_max_tentativas: int = Field(default=5, ge=1, le=50)
    notificacoes_backoff_base_segundos: int = Field(default=60, ge=1)

    # ---------------------------------------------------------------- limites de IA
    ia_diagnosticos_por_dia: int = Field(default=3, ge=1, le=100, validation_alias="IA_DIAGNOSTICOS_DIA")
    ia_dicas_por_dia: int = Field(default=10, ge=1, le=100, validation_alias="IA_DICAS_DIA")

    # ---------------------------------------------------------------- pool
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_max_overflow: int = Field(default=10, ge=0, le=100)
    db_pool_recycle_segundos: int = Field(default=1800, ge=60)
    db_pool_pre_ping: bool = True
    db_echo: bool = False

    # ---------------------------------------------------------------- operação
    log_level: str = "INFO"
    log_json: bool = False
    debug_commands: bool = False
    http_habilitado: bool = True
    http_host: str = "0.0.0.0"
    http_port: int = Field(default=10000, ge=1, le=65535, validation_alias="PORT")
    scheduler_lock_key: int = 872_001_337

    # ---------------------------------------------------------------- validadores
    @field_validator("ambiente")
    @classmethod
    def _normalizar(cls, valor: str) -> str:
        return normalizar_ambiente(valor)

    @field_validator("log_level")
    @classmethod
    def _normalizar_log_level(cls, valor: str) -> str:
        nivel = valor.strip().upper()
        if nivel not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(f"nível de log inválido: {valor!r}")
        return nivel

    @model_validator(mode="after")
    def _validar_segredos(self) -> Settings:
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
        return self

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
        if token is None:  # QA sem TOKEN_QA: usa o de produção como fallback
            token = self.token_producao
        if token is None:
            raise ConfigurationError("Token do Telegram não configurado")
        return token.get_secret_value()

    @property
    def database_url(self) -> str:
        url = self.db_url_producao if self.is_producao else self.db_url_qa
        if url is None:  # QA sem banco local: usa o de produção como fallback
            url = self.db_url_producao
        if url is None:
            raise ConfigurationError("String de conexão do banco não configurada")
        return url.get_secret_value()

    @property
    def intervalo_notificacao_segundos(self) -> int:
        return self.intervalo_notificacao_minutos * 60


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna a configuração carregada (memoizada)."""
    return Settings()  # type: ignore[call-arg]


def reload_settings() -> Settings:
    """Descarta o cache e recarrega a configuração."""
    get_settings.cache_clear()
    return get_settings()
