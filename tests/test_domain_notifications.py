"""Testes da política de retentativa."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from lubribot.domain.notifications import (
    NotificationStatus,
    RetryPolicy,
    esta_pronta,
)

AGORA = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


class TestBackoff:
    def test_cresce_exponencialmente(self):
        policy = RetryPolicy(base_segundos=60)
        assert policy.atraso(1) == 60
        assert policy.atraso(2) == 120
        assert policy.atraso(3) == 240
        assert policy.atraso(4) == 480

    def test_respeita_teto(self):
        policy = RetryPolicy(base_segundos=60, maximo_segundos=300)
        assert policy.atraso(10) == 300

    def test_tentativa_zero_nao_gera_atraso_zero(self):
        assert RetryPolicy(base_segundos=60).atraso(0) == 60

    def test_proxima_tentativa_e_calculada(self):
        policy = RetryPolicy(base_segundos=60)
        assert policy.proxima_tentativa(2, AGORA) == AGORA + timedelta(seconds=120)


class TestEsgotamento:
    def test_esgota_no_limite(self):
        policy = RetryPolicy(max_tentativas=3)
        assert policy.esgotou(2) is False
        assert policy.esgotou(3) is True
        assert policy.esgotou(4) is True


class TestProntidao:
    @pytest.mark.parametrize("status", ["Enviada", "Cancelada", "Falha", None])
    def test_nao_processa_fora_de_pendente(self, status):
        assert esta_pronta(status, None, AGORA) is False

    def test_pendente_sem_agendamento_esta_pronta(self):
        assert esta_pronta(NotificationStatus.PENDENTE, None, AGORA) is True

    def test_pendente_agendada_para_o_futuro_espera(self):
        futuro = AGORA + timedelta(minutes=5)
        assert esta_pronta(NotificationStatus.PENDENTE, futuro, AGORA) is False

    def test_pendente_vencida_esta_pronta(self):
        passado = AGORA - timedelta(minutes=5)
        assert esta_pronta(NotificationStatus.PENDENTE, passado, AGORA) is True
