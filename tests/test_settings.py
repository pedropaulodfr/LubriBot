"""Testes da configuração: normalização de ambiente e falha rápida."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from lubribot.config.settings import Settings, normalizar_ambiente


def _settings(**overrides) -> Settings:
    base = {
        "token_qa": "123:qa-token",
        "db_url_qa": "postgresql://user:pass@localhost:5432/lubribot",
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)


class TestNormalizacaoAmbiente:
    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [
            ("PRODUÇÃO", "PRODUCAO"),
            ("producao", "PRODUCAO"),
            (" Produção ", "PRODUCAO"),
            ("QA", "QA"),
            ("qa", "QA"),
        ],
    )
    def test_normaliza_acento_espaco_e_caixa(self, entrada, esperado):
        assert normalizar_ambiente(entrada) == esperado


class TestSelecaoDeAmbiente:
    def test_producao_usa_token_e_banco_de_producao(self):
        settings = _settings(
            ambiente="PRODUÇÃO",
            token_producao="999:prod-token",
            db_url_producao="postgresql://prod@db:5432/lubribot",
            token_qa="111:qa-token",
            db_url_qa="postgresql://qa@db:5432/lubribot_qa",
        )
        assert settings.is_producao is True
        assert settings.telegram_token == "999:prod-token"
        assert "prod@" in settings.database_url

    def test_producao_sem_acento_tambem_e_reconhecida(self):
        settings = _settings(
            ambiente="PRODUCAO",
            token_producao="999:prod-token",
            db_url_producao="postgresql://prod@db:5432/lubribot",
        )
        assert settings.is_producao is True

    def test_qa_usa_token_e_banco_de_qa(self):
        settings = _settings(ambiente="QA")
        assert settings.is_producao is False
        assert settings.telegram_token == "123:qa-token"
        assert "lubribot" in settings.database_url

    def test_qa_sem_configuracao_propria_cai_para_producao(self):
        settings = _settings(
            ambiente="QA",
            token_qa=None,
            db_url_qa=None,
            token_producao="999:prod-token",
            db_url_producao="postgresql://prod@db:5432/lubribot",
        )
        assert settings.telegram_token == "999:prod-token"
        assert "prod@" in settings.database_url


class TestValidacao:
    def test_sem_token_nenhum_falha_no_boot(self):
        with pytest.raises(ValidationError):
            Settings(
                _env_file=None,
                token_qa=None,
                token_producao=None,
                db_url_qa="postgresql://qa@db:5432/lubribot",
            )

    def test_sem_banco_nenhum_falha_no_boot(self):
        with pytest.raises(ValidationError):
            Settings(
                _env_file=None,
                token_qa="123:token",
                token_producao=None,
                db_url_qa=None,
                db_url_producao=None,
            )

    def test_producao_sem_token_falha_mesmo_com_qa_configurado(self):
        with pytest.raises(ValidationError):
            Settings(
                _env_file=None,
                ambiente="PRODUÇÃO",
                token_qa="123:token",
                token_producao=None,
                db_url_producao="postgresql://prod@db:5432/lubribot",
            )

    def test_intervalo_negativo_e_rejeitado(self):
        with pytest.raises(ValidationError):
            _settings(intervalo_notificacao_minutos=0)

    def test_nivel_de_log_invalido_e_rejeitado(self):
        with pytest.raises(ValidationError):
            _settings(log_level="BARULHENTO")


class TestDerivados:
    def test_intervalo_em_segundos(self):
        assert _settings(intervalo_notificacao_minutos=15).intervalo_notificacao_segundos == 900

    def test_padrao_de_manutencao_e_180_dias(self):
        assert _settings().intervalo_manutencao_padrao_dias == 180

    def test_padrao_de_backoff(self):
        settings = _settings()
        assert settings.notificacoes_max_tentativas == 5
        assert settings.notificacoes_backoff_base_segundos == 60
