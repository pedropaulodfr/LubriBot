"""Testes do despachante de notificações (entrega, retry e falha definitiva)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from lubribot.domain.notifications import RetryPolicy
from lubribot.notifications.dispatcher import NotificationDispatcher
from lubribot.notifications.ports import SendOutcome
from tests.fakes import FakeNotificationRepository, FakeSender, pendente

AGORA = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)


def _dispatcher(repo, sender, *, max_tentativas: int = 5) -> NotificationDispatcher:
    return NotificationDispatcher(
        repo,
        sender,
        retry_policy=RetryPolicy(max_tentativas=max_tentativas, base_segundos=60),
        agora_factory=lambda: AGORA,
    )


class TestEnvio:
    def test_envia_e_marca_como_enviada(self):
        repo = FakeNotificationRepository(pendentes=[pendente()])
        sender = FakeSender()
        resultado = _dispatcher(repo, sender).despachar()

        assert resultado.enviadas == 1
        assert repo.enviadas == [1]
        assert sender.chamadas[0][0] == 555

    def test_sem_pendentes_nao_faz_nada(self):
        repo = FakeNotificationRepository(pendentes=[])
        resultado = _dispatcher(repo, FakeSender()).despachar()
        assert resultado.pendentes == 0
        assert resultado.enviadas == 0

    def test_nao_reenvia_notificacao_ja_marcada(self):
        # O repositório real só devolve Pendente; aqui garantimos que o
        # despachante não inventa envio quando a lista vem vazia.
        repo = FakeNotificationRepository(pendentes=[])
        sender = FakeSender()
        _dispatcher(repo, sender).despachar()
        assert sender.chamadas == []


class TestFalhaTemporaria:
    def test_reagenda_com_backoff(self):
        repo = FakeNotificationRepository(pendentes=[pendente(tentativas=0)])
        sender = FakeSender([SendOutcome.transitorio("timeout")])
        resultado = _dispatcher(repo, sender).despachar()

        assert resultado.reagendadas == 1
        assert repo.enviadas == []
        assert len(repo.falhas_temporarias) == 1
        registro = repo.falhas_temporarias[0]
        assert registro["tentativas"] == 1
        assert registro["proxima"] == AGORA + timedelta(seconds=60)
        assert "timeout" in registro["erro"]

    def test_respeita_retry_after_do_telegram(self):
        repo = FakeNotificationRepository(pendentes=[pendente()])
        sender = FakeSender([SendOutcome.transitorio("rate limit", retry_after=300)])
        _dispatcher(repo, sender).despachar()

        registro = repo.falhas_temporarias[0]
        assert registro["proxima"] == AGORA + timedelta(seconds=300)

    def test_apos_max_tentativas_vira_falha_definitiva(self):
        repo = FakeNotificationRepository(pendentes=[pendente(tentativas=2)])
        sender = FakeSender([SendOutcome.transitorio("timeout")])
        resultado = _dispatcher(repo, sender, max_tentativas=3).despachar()

        assert resultado.falhas_definitivas == 1
        assert repo.falhas_temporarias == []
        assert repo.falhas_definitivas[0][0] == 1


class TestFalhaDefinitiva:
    def test_bloqueio_do_usuario_marca_falha_sem_retry(self):
        repo = FakeNotificationRepository(pendentes=[pendente()])
        sender = FakeSender([SendOutcome.definitivo("HTTP 403: bot was blocked")])
        resultado = _dispatcher(repo, sender).despachar()

        assert resultado.falhas_definitivas == 1
        assert repo.falhas_temporarias == []
        assert repo.enviadas == []

    def test_usuario_sem_telegram_id_nao_tenta_enviar(self):
        repo = FakeNotificationRepository(pendentes=[pendente(telegram_id=None)])
        sender = FakeSender()
        resultado = _dispatcher(repo, sender).despachar()

        assert sender.chamadas == []
        assert resultado.falhas_definitivas == 1


class TestCancelamento:
    def test_usuario_que_desativou_notificacoes_cancela_pendencia(self):
        repo = FakeNotificationRepository(
            pendentes=[pendente(receber_notificacoes=False)]
        )
        sender = FakeSender()
        resultado = _dispatcher(repo, sender).despachar()

        assert resultado.canceladas == 1
        assert repo.canceladas[0][0] == 1
        assert sender.chamadas == []


class TestToleranciaAFalhas:
    def test_falha_no_repositorio_nao_derruba_as_demais(self):
        class RepoComFalha(FakeNotificationRepository):
            def marcar_enviada(self, notificacao_id, agora):
                if notificacao_id == 1:
                    raise RuntimeError("banco caiu no meio")
                super().marcar_enviada(notificacao_id, agora)

        repo = RepoComFalha(pendentes=[pendente(id=1), pendente(id=2)])
        sender = FakeSender()
        resultado = _dispatcher(repo, sender).despachar()

        # A segunda foi processada mesmo com a falha na primeira.
        assert 2 in repo.enviadas
        assert resultado.falhas_temporarias >= 1
