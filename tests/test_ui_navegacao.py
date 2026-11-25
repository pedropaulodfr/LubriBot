"""Testes de navegação: menu principal, submenu e comandos globais."""

from __future__ import annotations

from types import SimpleNamespace

from lubribot.bot.keyboards.menu_principal_keyboard import menu_principal


def _mensagem(chat_id: int = 10, texto: str = "") -> SimpleNamespace:
    return SimpleNamespace(chat=SimpleNamespace(id=chat_id), text=texto)


def _rotulo(botao) -> str:
    if isinstance(botao, dict):
        return botao.get("text", "")
    return getattr(botao, "text", "")


class FakeBot:
    """Bot mínimo que registra handlers em vez de falar com o Telegram."""

    def __init__(self) -> None:
        self.registros: list[tuple[dict, callable]] = []
        self.mensagens: list[dict] = []

    def message_handler(self, **kwargs):
        def decorador(funcao):
            self.registros.append((kwargs, funcao))
            return funcao

        return decorador

    def send_message(self, chat_id, text, **kwargs):
        self.mensagens.append({"chat_id": chat_id, "text": text, **kwargs})
        return SimpleNamespace(message_id=1)

    def handler_para(self, texto: str):
        for kwargs, funcao in self.registros:
            filtro = kwargs.get("func")
            if filtro is not None and filtro(_mensagem(texto=texto)):
                return funcao
        return None

    def handler_de_comandos(self, comando: str):
        for kwargs, funcao in self.registros:
            if comando in (kwargs.get("commands") or []):
                return funcao
        return None


def _rotulos_do_menu() -> list[str]:
    markup = menu_principal()
    return [_rotulo(botao) for linha in markup.keyboard for botao in linha]


class TestMenuPrincipal:
    def test_historico_esta_no_primeiro_nivel(self):
        assert "🔎 Ver Manutenções" in _rotulos_do_menu()

    def test_botao_antigo_de_reticencias_nao_existe(self):
        assert "..." not in _rotulos_do_menu()

    def test_submenu_tem_rotulo_claro(self):
        assert "🗂️ Mais opções" in _rotulos_do_menu()

    def test_acoes_principais_continuam_presentes(self):
        rotulos = _rotulos_do_menu()
        for esperado in (
            "🛠️ Registrar Manutenção",
            "🚘 Gerenciar Veículos",
            "💡 Dicas",
            "⚠️ Diagnósticos",
            "⚙️ Configurações",
        ):
            assert esperado in rotulos


class TestSubmenuMaisOpcoes:
    def test_aceita_rotulo_novo_e_antigo(self):
        from lubribot.bot.handlers.mais_handle import mais_handle

        bot = FakeBot()
        mais_handle(bot)

        assert bot.handler_para("🗂️ Mais opções") is not None
        assert bot.handler_para("...") is not None  # teclados antigos continuam válidos
        assert bot.handler_para("🛠️ Registrar Manutenção") is None

    def test_envia_opcoes_de_catalogo(self):
        from lubribot.bot.handlers.mais_handle import mais_handle

        bot = FakeBot()
        mais_handle(bot)
        handler = bot.handler_para("🗂️ Mais opções")
        handler(_mensagem(texto="🗂️ Mais opções"))

        assert len(bot.mensagens) == 1
        markup = bot.mensagens[0]["reply_markup"]
        rotulos = [_rotulo(botao) for linha in markup.keyboard for botao in linha]
        assert "🛢️ Gerenciar Produtos" in rotulos
        assert "🧰 Gerenciar Serviços" in rotulos


class TestComandosDeNavegacao:
    def _registrar(self):
        import lubribot.bot.handlers.navegacao_handle as modulo

        bot = FakeBot()
        modulo.navegacao_handle(bot)
        return modulo, bot

    def test_menu_restaura_teclado(self):
        _, bot = self._registrar()
        handler = bot.handler_de_comandos("menu")
        handler(_mensagem())

        assert bot.mensagens[0]["reply_markup"] is not None

    def test_cancelar_sem_fluxo_ativo_avisa(self, monkeypatch):
        modulo, bot = self._registrar()
        monkeypatch.setattr(modulo, "_limpar_estados", lambda chat_id: 0)

        handler = bot.handler_de_comandos("cancelar")
        handler(_mensagem())

        assert "não havia" in bot.mensagens[0]["text"].lower()

    def test_cancelar_com_fluxo_ativo_confirma(self, monkeypatch):
        modulo, bot = self._registrar()
        monkeypatch.setattr(modulo, "_limpar_estados", lambda chat_id: 1)

        handler = bot.handler_de_comandos("cancelar")
        handler(_mensagem())

        assert "cancelada" in bot.mensagens[0]["text"].lower()

    def test_ajuda_lista_comandos(self):
        _, bot = self._registrar()
        handler = bot.handler_de_comandos("ajuda")
        handler(_mensagem())

        texto = bot.mensagens[0]["text"]
        assert "/menu" in texto and "/cancelar" in texto
