"""Testes do registro de conversas (rascunhos persistidos)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from types import SimpleNamespace

import pytest

from lubribot.bot.conversation_store import (
    DraftMixin,
    MemoryConversationRegistry,
    get_registry,
    limpar_registros,
)


@pytest.fixture(autouse=True)
def _registros_limpos():
    limpar_registros()
    yield
    limpar_registros()


@dataclass
class RascunhoTeste(DraftMixin):
    __fluxo__ = "teste"

    usuario_id: int
    km: int | None = None
    data: date | None = None
    produtos: list[int] = field(default_factory=list)


def _registro() -> MemoryConversationRegistry:
    return get_registry("teste", RascunhoTeste, persistente=False)  # type: ignore[return-value]


class TestRascunho:
    def test_cria_e_le(self):
        registro = _registro()
        registro[10] = RascunhoTeste(usuario_id=1, km=1000)

        carregado = registro.get(10)
        assert carregado.usuario_id == 1
        assert carregado.km == 1000

    def test_mutacao_e_persistida(self):
        registro = _registro()
        registro[10] = RascunhoTeste(usuario_id=1)

        rascunho = registro.get(10)
        rascunho.km = 45000

        # Nova leitura (simula outro handler) enxerga o valor.
        assert registro.get(10).km == 45000

    def test_mutacao_de_lista_e_persistida(self):
        registro = _registro()
        registro[10] = RascunhoTeste(usuario_id=1)

        rascunho = registro.get(10)
        rascunho.produtos = [1, 2, 3]

        assert registro.get(10).produtos == [1, 2, 3]

    def test_data_sobrevive_ao_ciclo(self):
        registro = _registro()
        registro[10] = RascunhoTeste(usuario_id=1, data=date(2026, 2, 5))

        assert registro.get(10).data == date(2026, 2, 5)

    def test_versions_isoladas_por_chat(self):
        registro = _registro()
        registro[10] = RascunhoTeste(usuario_id=1, km=100)
        registro[20] = RascunhoTeste(usuario_id=2, km=200)

        assert registro.get(10).km == 100
        assert registro.get(20).km == 200


class TestApiDict:
    def test_contains(self):
        registro = _registro()
        assert 10 not in registro
        registro[10] = RascunhoTeste(usuario_id=1)
        assert 10 in registro

    def test_get_com_default(self):
        assert _registro().get(99) is None
        assert _registro().get(99, "x") == "x"

    def test_pop_remove(self):
        registro = _registro()
        registro[10] = RascunhoTeste(usuario_id=1, km=5)

        removido = registro.pop(10)
        assert removido.km == 5
        assert registro.get(10) is None
        assert registro.pop(10, None) is None

    def test_item_inexistente_gera_keyerror(self):
        try:
            _registro()[1]
        except KeyError:
            pass
        else:  # pragma: no cover
            raise AssertionError("esperava KeyError")


class TestEtapas:
    def test_guarda_proxima_etapa(self):
        registro = _registro()
        registro[10] = RascunhoTeste(usuario_id=1)

        registro.definir_etapa(10, "receber_km")
        assert registro.obter_etapa(10) == "receber_km"

    def test_sem_rascunho_nao_cria_linha(self):
        registro = _registro()
        registro.definir_etapa(10, "receber_km")
        assert registro.get(10) is None

    def test_limpar_apaga(self):
        registro = _registro()
        registro[10] = RascunhoTeste(usuario_id=1)

        assert registro.limpar(10) is True
        assert registro.limpar(10) is False

    def test_etapa_sobrevive_a_nova_instancia(self):
        registro = _registro()
        registro[10] = RascunhoTeste(usuario_id=1)
        registro.definir_etapa(10, "receber_km")

        assert registro.obter_etapa(10) == "receber_km"


class TestModeloDict:
    def test_estado_dict_roundtrip(self):
        registro = get_registry("diagnostico", dict, persistente=False)
        registro[10] = {"veiculo_id": 7, "problema": "barulho"}

        assert registro.get(10)["veiculo_id"] == 7
        registro[10] = {"veiculo_id": 7, "problema": "barulho", "resolvido": True}
        assert registro.get(10)["resolvido"] is True


class TestRegistroMemoizado:
    def test_get_registry_memoiza(self):
        primeiro = get_registry("teste-memo", RascunhoTeste, persistente=False)
        segundo = get_registry("teste-memo", RascunhoTeste, persistente=False)
        assert primeiro is segundo
class TestFacade:
    def _facade(self, monkeypatch, registro):
        import lubribot.bot.facade as modulo

        monkeypatch.setattr(modulo, "registros_ativos", lambda: [registro])
        bot = SimpleNamespace(
            register_next_step_handler=lambda message, callback, *a, **k: None,
            send_message=lambda *a, **k: None,
        )
        return modulo.BotFacade(bot)

    def test_registra_etapa_do_proximo_passo(self, monkeypatch):
        registro = _registro()
        registro[10] = RascunhoTeste(usuario_id=1)
        facade = self._facade(monkeypatch, registro)

        def receber_km(message):
            return message

        facade.register_next_step_handler(
            SimpleNamespace(chat=SimpleNamespace(id=10)), receber_km
        )

        assert registro.obter_etapa(10) == "receber_km"

    def test_retoma_passo_salvo(self, monkeypatch):
        registro = _registro()
        registro[10] = RascunhoTeste(usuario_id=1)
        facade = self._facade(monkeypatch, registro)

        def receber_km(message):
            return "ok"

        facade.register_next_step_handler(
            SimpleNamespace(chat=SimpleNamespace(id=10)), receber_km
        )
        retomada = facade.retomar(10)

        assert retomada is not None
        _registro_, etapa, callback = retomada
        assert etapa == "receber_km"
        assert callback(SimpleNamespace()) == "ok"

    def test_sem_conversa_nao_retoma(self, monkeypatch):
        facade = self._facade(monkeypatch, _registro())
        assert facade.retomar(99) is None
