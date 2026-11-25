"""Testes do classificador de erros do Telegram."""

from __future__ import annotations

from lubribot.integrations.telegram_sender import TelegramSender


class FakeBot:
    def __init__(self, erro: Exception | None = None) -> None:
        self.erro = erro
        self.mensagens: list[dict] = []

    def send_message(self, **kwargs):
        if self.erro is not None:
            raise self.erro
        self.mensagens.append(kwargs)


class ErroTelegram(Exception):
    def __init__(self, error_code: int, description: str, result_json=None):
        super().__init__(description)
        self.error_code = error_code
        self.description = description
        self.result_json = result_json or {}


class TestEnvioComSucesso:
    def test_retorna_sucesso(self):
        bot = FakeBot()
        resultado = TelegramSender(bot).enviar(123, "oi")
        assert resultado.ok is True
        assert bot.mensagens[0]["chat_id"] == 123

    def test_conteudo_vazio_nao_chama_api(self):
        bot = FakeBot()
        resultado = TelegramSender(bot).enviar(123, "")
        assert resultado.ok is False
        assert resultado.permanente is True
        assert bot.mensagens == []


class TestClassificacao:
    def test_429_e_transitorio_com_retry_after(self):
        erro = ErroTelegram(429, "Too Many Requests", {"parameters": {"retry_after": 42}})
        resultado = TelegramSender(FakeBot(erro)).enviar(1, "oi")
        assert resultado.ok is False
        assert resultado.permanente is False
        assert resultado.retry_after == 42

    def test_403_e_definitivo(self):
        erro = ErroTelegram(403, "bot was blocked by the user")
        resultado = TelegramSender(FakeBot(erro)).enviar(1, "oi")
        assert resultado.permanente is True

    def test_400_e_definitivo(self):
        erro = ErroTelegram(400, "chat not found")
        resultado = TelegramSender(FakeBot(erro)).enviar(1, "oi")
        assert resultado.permanente is True

    def test_500_e_transitorio_sem_retry_after(self):
        erro = ErroTelegram(502, "Bad Gateway")
        resultado = TelegramSender(FakeBot(erro)).enviar(1, "oi")
        assert resultado.permanente is False
        assert resultado.retry_after is None

    def test_erro_de_rede_generico_e_transitorio(self):
        resultado = TelegramSender(FakeBot(ConnectionError("reset"))).enviar(1, "oi")
        assert resultado.permanente is False
        assert resultado.retry_after is None
