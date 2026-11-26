"""Testes da regra de próxima manutenção (domínio puro, sem banco)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from lubribot.domain.maintenance import (
    ANTECEDENCIA_PADRAO_DIAS,
    INTERVALO_PADRAO_DIAS,
    calcular_agendamento,
    calcular_vencimento_km,
    chave_notificacao,
    descricao_veiculo,
    esta_na_janela,
    intervalo_efetivo,
    intervalo_km_efetivo,
    km_vencido,
    montar_conteudo_notificacao,
)


class TestIntervaloEfetivo:
    def test_usa_o_maior_intervalo_dos_servicos(self):
        assert intervalo_efetivo([90, 180, 30]) == 180

    def test_ignora_nulos_e_invalidos(self):
        assert intervalo_efetivo([None, 0, -10, 90]) == 90

    def test_sem_intervalo_usa_padrao(self):
        assert intervalo_efetivo([]) == INTERVALO_PADRAO_DIAS
        assert intervalo_efetivo([None, None]) == INTERVALO_PADRAO_DIAS

    def test_padrao_configuravel(self):
        assert intervalo_efetivo([], padrao=30) == 30


class TestAgendamento:
    def test_soma_intervalo_a_data_da_ultima_manutencao(self):
        ultima = date(2026, 1, 1)
        agenda = calcular_agendamento(10, ultima, [90])
        assert agenda.proxima_data == date(2026, 4, 1)
        assert agenda.intervalo_dias == 90
        assert agenda.ultima_manutencao_id == 10

    def test_usa_padrao_quando_servico_nao_tem_intervalo(self):
        agenda = calcular_agendamento(1, date(2026, 1, 1), [None], padrao=180)
        assert agenda.proxima_data == date(2026, 6, 30)

    def test_ultima_data_invalida_nao_e_silenciada(self):
        with pytest.raises(TypeError):
            calcular_agendamento(1, None, [30])  # type: ignore[arg-type]


class TestJanelaDeAviso:
    HOJE = date(2026, 1, 1)

    @pytest.mark.parametrize(
        ("dias_no_futuro", "esperado"),
        [
            (0, True),    # vence hoje
            (1, True),
            (7, True),    # último dia da janela padrão
            (8, False),   # um dia depois da janela
            (30, False),
            (-1, False),  # já venceu: não notifica retroativamente
            (-30, False),
        ],
    )
    def test_janela_de_7_dias(self, dias_no_futuro, esperado):
        proxima = self.HOJE + timedelta(days=dias_no_futuro)
        assert esta_na_janela(proxima, self.HOJE, 7) is esperado

    def test_antecedencia_configurada_pelo_usuario(self):
        proxima = self.HOJE + timedelta(days=10)
        assert esta_na_janela(proxima, self.HOJE, 10) is True
        assert esta_na_janela(proxima, self.HOJE, 5) is False

    def test_antecedencia_ausente_usa_padrao(self):
        proxima = self.HOJE + timedelta(days=ANTECEDENCIA_PADRAO_DIAS)
        assert esta_na_janela(proxima, self.HOJE, None) is True


class TestIntervaloKm:
    def test_usa_o_maior_intervalo(self):
        assert intervalo_km_efetivo([5000, 10000, None]) == 10000

    def test_sem_dados_retorna_none(self):
        assert intervalo_km_efetivo([]) is None
        assert intervalo_km_efetivo([None, 0, -1]) is None

    def test_padrao_opcional(self):
        assert intervalo_km_efetivo([], padrao=8000) == 8000


class TestVencimentoKm:
    def test_soma_intervalo_ao_ultimo_km(self):
        assert calcular_vencimento_km(10000, [5000]) == 15000

    def test_sem_ultimo_km_nao_calcula(self):
        assert calcular_vencimento_km(None, [5000]) is None

    def test_sem_intervalo_nao_calcula(self):
        assert calcular_vencimento_km(10000, [None]) is None
        assert calcular_vencimento_km(10000, []) is None


class TestKmVencido:
    @pytest.mark.parametrize(
        ("km_atual", "proxima_km", "esperado"),
        [
            (15000, 15000, True),   # exatamente no vencimento
            (16000, 15000, True),   # passou
            (14999, 15000, False),  # ainda não
            (None, 15000, False),   # sem odômetro
            (15000, None, False),   # sem vencimento calculado
        ],
    )
    def test_comparacao(self, km_atual, proxima_km, esperado):
        assert km_vencido(km_atual, proxima_km) is esperado


class TestMensagemPorKm:
    def test_apenas_km(self):
        texto = montar_conteudo_notificacao("Ana", "Honda Bros", None, proxima_km=11500)
        assert "11.500 km" in texto
        assert "Ana" in texto

    def test_data_e_km(self):
        texto = montar_conteudo_notificacao(
            "Ana", "Honda Bros", date(2026, 2, 3), proxima_km=11500
        )
        assert "03/02/2026" in texto
        assert "11.500 km" in texto

    def test_sem_gatilho_menciona_revisao(self):
        texto = montar_conteudo_notificacao("Ana", "Honda Bros")
        assert "revisar" in texto


class TestChaveDeIdempotencia:
    def test_chave_estavel_por_manutencao(self):
        assert chave_notificacao(42) == "ProximaManutencao:42"
        assert chave_notificacao(42) == chave_notificacao(42)

    def test_chaves_diferentes_para_manutencoes_diferentes(self):
        assert chave_notificacao(1) != chave_notificacao(2)


class TestMensagens:
    def test_descricao_monta_veiculo_completo(self):
        assert (
            descricao_veiculo("Honda", "Bros", "Vermelha", "2022", "ABC1D23")
            == "Honda Bros Vermelha 2022 (ABC1D23)"
        )

    def test_descricao_ignora_campos_vazios(self):
        assert descricao_veiculo("Honda", "", None, "", None) == "Honda"

    def test_descricao_com_tudo_vazio_nao_quebra(self):
        assert descricao_veiculo(None, None, None, None, None) == "veículo"

    def test_conteudo_com_nome(self):
        texto = montar_conteudo_notificacao("Ana", "Honda Bros", date(2026, 2, 3))
        assert "Ana" in texto
        assert "03/02/2026" in texto

    def test_conteudo_sem_nome(self):
        texto = montar_conteudo_notificacao(None, "Honda Bros", date(2026, 2, 3))
        assert texto.startswith("Ola!")
