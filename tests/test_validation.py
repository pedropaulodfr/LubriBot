"""Testes da validação de entradas (placa, ano, km, custo, RENAVAM)."""

from __future__ import annotations

import pytest

from lubribot.domain.validation import (
    normalizar_placa,
    normalizar_renavam,
    normalizar_texto_livre,
    validar_ano,
    validar_custo,
    validar_km,
    validar_placa,
)


class TestPlaca:
    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [
            ("ABC1D23", "ABC1D23"),      # Mercosul
            ("ABC-1234", "ABC1234"),     # antigo com hífen
            ("abc1234", "ABC1234"),
            (" ABC 1D23 ", "ABC1D23"),
        ],
    )
    def test_aceita_formatos_validos(self, entrada, esperado):
        assert validar_placa(entrada) == esperado

    @pytest.mark.parametrize("invalida", ["ABC123", "AB12345", "1234567", "", None, "ABC12D3"])
    def test_rejeita_formatos_invalidos(self, invalida):
        assert validar_placa(invalida) is None

    def test_normaliza_sem_validar(self):
        assert normalizar_placa("abc-1d23") == "ABC1D23"


class TestAno:
    @pytest.mark.parametrize("ano", ["1900", "1999", "2026", "2100"])
    def test_aceita_faixa_plausivel(self, ano):
        assert validar_ano(ano) == ano

    @pytest.mark.parametrize("ano", ["1899", "2101", "26", "20266", "abcd", "", None])
    def test_rejeita_fora_da_faixa_ou_formato(self, ano):
        assert validar_ano(ano) is None


class TestKm:
    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [("0", 0), ("45000", 45000), ("45.000", 45000), (" 1200 ", 1200)],
    )
    def test_aceita_numeros(self, entrada, esperado):
        assert validar_km(entrada) == esperado

    @pytest.mark.parametrize("invalida", ["-1", "abc", "", None, "9999999999"])
    def test_rejeita_invalidos(self, invalida):
        assert validar_km(invalida) is None


class TestCusto:
    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [("120", 120.0), ("120,50", 120.5), ("1.200,50", 1200.5), ("R$ 89,90", 89.9)],
    )
    def test_aceita_formatos_brasileiros(self, entrada, esperado):
        assert validar_custo(entrada) == esperado

    @pytest.mark.parametrize("invalida", ["abc", "", None, "-5"])
    def test_rejeita_invalidos(self, invalida):
        assert validar_custo(invalida) is None


class TestRenavam:
    def test_aceita_9_a_11_digitos(self):
        assert normalizar_renavam("01284111501") == "01284111501"
        assert normalizar_renavam("123456789") == "123456789"

    def test_ponto_ou_vazio_vira_none(self):
        assert normalizar_renavam(".") is None
        assert normalizar_renavam("") is None
        assert normalizar_renavam(None) is None

    def test_tamanho_invalido_vira_none(self):
        assert normalizar_renavam("123") is None
        assert normalizar_renavam("12345678") is None


class TestTexto:
    def test_ponto_vira_none(self):
        assert normalizar_texto_livre(".") is None

    def test_limita_tamanho(self):
        assert normalizar_texto_livre("a" * 500, limite=100) == "a" * 100
