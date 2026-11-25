"""Implementação SQLAlchemy do repositório de notificações.

Desempenho: o planejador faz **duas** consultas por ciclo (candidatos +
intervalos), independentemente da quantidade de veículos. O despacho também faz
uma consulta única com o necessário (join com usuário/parâmetros).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from lubribot.domain.maintenance import (
    descricao_veiculo,
)
from lubribot.domain.notifications import NotificationStatus
from lubribot.models import (
    Manutencao,
    ManutencaoServico,
    Notificacao,
    Servico,
    Usuario,
    UsuarioParametro,
    Veiculo,
)
from lubribot.notifications.models import (
    CandidatoVeiculo,
    DadosNotificacao,
    NotificacaoPendente,
)
from lubribot.utils.logging import get_logger

logger = get_logger(__name__)


class SQLAlchemyNotificationRepository:
    """Persistência de notificações sobre uma sessão existente."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ----------------------------------------------------------------- leitura
    def listar_candidatos(self) -> list[CandidatoVeiculo]:
        """Veículos ativos com última manutenção finalizada e intervalos.

        Usa window function para pegar a manutenção mais recente por veículo
        (data, depois id) em uma única passada.
        """
        ranking = (
            select(
                Manutencao.id.label("manutencao_id"),
                Manutencao.veiculo_id.label("veiculo_id"),
                Manutencao.data.label("data"),
                func.row_number()
                .over(
                    partition_by=Manutencao.veiculo_id,
                    order_by=(Manutencao.data.desc(), Manutencao.id.desc()),
                )
                .label("ordem"),
            )
            .where(
                Manutencao.status == "Finalizada",
                Manutencao.data.is_not(None),
                Manutencao.veiculo_id.is_not(None),
            )
            .subquery()
        )
        ultima = (
            select(ranking.c.manutencao_id, ranking.c.veiculo_id, ranking.c.data)
            .where(ranking.c.ordem == 1)
            .subquery()
        )

        stmt = (
            select(
                Veiculo.id,
                Veiculo.fabricante,
                Veiculo.modelo,
                Veiculo.cor,
                Veiculo.anoModelo,
                Veiculo.placa,
                Usuario.id.label("usuario_id"),
                Usuario.telegram_id,
                Usuario.primeiroNome,
                UsuarioParametro.receberNotificacoes,
                UsuarioParametro.diasNotificacao,
                ultima.c.manutencao_id,
                ultima.c.data,
            )
            .join(Usuario, Usuario.id == Veiculo.usuario_id)
            .join(ultima, ultima.c.veiculo_id == Veiculo.id)
            .outerjoin(UsuarioParametro, UsuarioParametro.usuario_id == Usuario.id)
            .where(Veiculo.status == "Ativo")
            .order_by(Veiculo.id)
        )

        linhas = self._session.execute(stmt).all()
        if not linhas:
            return []

        ids_manutencao = [linha.manutencao_id for linha in linhas]
        intervalos = self._intervalos_por_manutencao(ids_manutencao)

        candidatos: list[CandidatoVeiculo] = []
        for linha in linhas:
            candidatos.append(
                CandidatoVeiculo(
                    veiculo_id=linha.id,
                    usuario_id=linha.usuario_id,
                    telegram_id=linha.telegram_id,
                    nome_usuario=linha.primeiroNome,
                    receber_notificacoes=linha.receberNotificacoes,
                    dias_notificacao=linha.diasNotificacao,
                    ultima_manutencao_id=linha.manutencao_id,
                    ultima_data=linha.data,
                    intervalos_dias=tuple(intervalos.get(linha.manutencao_id, ())),
                    descricao=descricao_veiculo(
                        linha.fabricante,
                        linha.modelo,
                        linha.cor,
                        linha.anoModelo,
                        linha.placa,
                    ),
                )
            )
        return candidatos

    def _intervalos_por_manutencao(
        self, manutencao_ids: list[int]
    ) -> dict[int, list[int | None]]:
        """Uma consulta para todos os intervalos dos serviços realizados."""
        if not manutencao_ids:
            return {}
        stmt = (
            select(ManutencaoServico.manutencao_id, Servico.intervaloDias)
            .join(Servico, Servico.id == ManutencaoServico.servico_id, isouter=True)
            .where(ManutencaoServico.manutencao_id.in_(manutencao_ids))
        )
        agrupado: dict[int, list[int | None]] = {}
        for manutencao_id, intervalo in self._session.execute(stmt).all():
            agrupado.setdefault(manutencao_id, []).append(intervalo)
        return agrupado

    def listar_pendentes(self, agora: datetime) -> list[NotificacaoPendente]:
        """Pendentes prontas para envio, com destinatário já resolvido."""
        stmt = (
            select(
                Notificacao.id,
                Notificacao.chave,
                Notificacao.conteudo,
                Notificacao.tentativas,
                Notificacao.proximaTentativaEm,
                Notificacao.usuario_id,
                Usuario.telegram_id,
                UsuarioParametro.receberNotificacoes,
            )
            .join(Usuario, Usuario.id == Notificacao.usuario_id)
            .outerjoin(UsuarioParametro, UsuarioParametro.usuario_id == Usuario.id)
            .where(
                Notificacao.status == NotificationStatus.PENDENTE,
                (Notificacao.proximaTentativaEm.is_(None))
                | (Notificacao.proximaTentativaEm <= agora),
            )
            .order_by(Notificacao.id)
        )
        return [
            NotificacaoPendente(
                id=linha.id,
                chave=linha.chave,
                conteudo=linha.conteudo or "",
                tentativas=linha.tentativas or 0,
                proxima_tentativa_em=linha.proximaTentativaEm,
                telegram_id=linha.telegram_id,
                usuario_id=linha.usuario_id,
                receber_notificacoes=linha.receberNotificacoes,
            )
            for linha in self._session.execute(stmt).all()
        ]

    def existe_pendente_para_manutencao(self, manutencao_id: int, tipo: str) -> bool:
        """Compatibilidade com o comportamento legado de deduplicação."""
        stmt = (
            select(func.count(Notificacao.id))
            .where(
                Notificacao.manutencao_id == manutencao_id,
                Notificacao.tipoNotificacao == tipo,
                Notificacao.status == NotificationStatus.PENDENTE,
            )
        )
        return (self._session.execute(stmt).scalar_one() or 0) > 0

    # ----------------------------------------------------------------- escrita
    def criar_se_nao_existir(self, dados: DadosNotificacao) -> bool:
        """Cria a notificação de forma idempotente (índice único em ``chave``)."""
        existente = self._session.execute(
            select(Notificacao.id).where(Notificacao.chave == dados.chave)
        ).first()
        if existente is not None:
            return False

        notificacao = Notificacao(
            dataNotificacao=dados.data_notificacao,
            tipoNotificacao=dados.tipo,
            usuario_id=dados.usuario_id,
            manutencao_id=dados.manutencao_id,
            veiculo_id=dados.veiculo_id,
            titulo=dados.titulo,
            conteudo=dados.conteudo,
            status=NotificationStatus.PENDENTE,
            chave=dados.chave,
            tentativas=0,
        )
        self._session.add(notificacao)
        try:
            self._session.flush()
        except IntegrityError:
            # Corrida entre duas instâncias: a outra venceu, sem duplicar.
            self._session.rollback()
            logger.warning(
                "notificacao_corrida_chave_duplicada",
                extra={"chave": dados.chave},
            )
            return False
        return True

    def marcar_enviada(self, notificacao_id: int, agora: datetime) -> None:
        self._atualizar(
            notificacao_id,
            status=NotificationStatus.ENVIADA,
            enviadaEm=agora,
            ultimaTentativaEm=agora,
            proximaTentativaEm=None,
            ultimoErro=None,
        )

    def registrar_falha_temporaria(
        self,
        notificacao_id: int,
        *,
        tentativas: int,
        proxima_tentativa_em: datetime,
        erro: str,
        agora: datetime,
    ) -> None:
        self._atualizar(
            notificacao_id,
            status=NotificationStatus.PENDENTE,
            tentativas=tentativas,
            proximaTentativaEm=proxima_tentativa_em,
            ultimaTentativaEm=agora,
            ultimoErro=erro,
        )

    def marcar_falha_definitiva(
        self, notificacao_id: int, *, erro: str, agora: datetime
    ) -> None:
        self._atualizar(
            notificacao_id,
            status=NotificationStatus.FALHA,
            ultimaTentativaEm=agora,
            ultimoErro=erro,
            proximaTentativaEm=None,
        )

    def cancelar(self, notificacao_id: int, *, motivo: str, agora: datetime) -> None:
        self._atualizar(
            notificacao_id,
            status=NotificationStatus.CANCELADA,
            ultimaTentativaEm=agora,
            ultimoErro=motivo,
            proximaTentativaEm=None,
        )

    def _atualizar(self, notificacao_id: int, **campos) -> None:
        notificacao = self._session.get(Notificacao, notificacao_id)
        if notificacao is None:
            logger.warning(
                "notificacao_inexistente_ao_atualizar",
                extra={"id": notificacao_id},
            )
            return
        for campo, valor in campos.items():
            setattr(notificacao, campo, valor)
