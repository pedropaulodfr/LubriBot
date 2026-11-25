"""Consultas de usuário.

Correções: ``add_usuario`` usava ``username=`` (coluna inexistente; o certo é
``usuarioNome``) e não tratava erro. As funções agora operam numa unidade de
trabalho e devolvem dados simples, evitando objetos presos a uma sessão fechada.
"""

from __future__ import annotations

from lubribot.database.runtime import get_database
from lubribot.models import Usuario


def get_usuario_by_telegram_id(telegram_id: int) -> Usuario | None:
    with get_database().unit_of_work(commit=False) as session:
        return session.query(Usuario).filter(Usuario.telegram_id == telegram_id).first()


def add_usuario(
    telegram_id: int,
    perfil: str,
    primeiro_nome: str,
    ultimo_nome: str,
    usuario_nome: str,
    status: str = "Ativo",
) -> Usuario:
    """Cria um usuário e devolve a instância já persistida."""
    with get_database().unit_of_work() as session:
        usuario = Usuario(
            telegram_id=telegram_id,
            perfil=perfil,
            primeiroNome=primeiro_nome,
            ultimoNome=ultimo_nome,
            usuarioNome=usuario_nome,
            status=status,
        )
        session.add(usuario)
        session.flush()
        return usuario
