"""Conversas em andamento: rascunhos de fluxo persistidos por chat.

Antes, os rascunhos viviam só em memória (`_RASCUNHOS[chat_id] = ...`): reiniciar
o processo descartava o progresso do usuário. Agora cada chat tem uma linha em
`conversas` com o rascunho serializado e a etapa atual.

A interface imita um `dict` (`get`, `[]`, `pop`, `in`) para que os handlers
existam sem grandes mudanças: trocar `_RASCUNHOS = {}` por
`get_registry("manutencao", RascunhoManutencao)` mantém o código de cada etapa
intacto, e a gravação acontece a cada alteração de campo.
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, date, datetime
from typing import Any, Protocol

from lubribot.database.runtime import get_database
from lubribot.models import Conversa
from lubribot.utils.logging import get_logger

logger = get_logger(__name__)


def _json_safe(valor: Any) -> Any:
    if isinstance(valor, datetime):
        return {"__tipo__": "datetime", "valor": valor.isoformat()}
    if isinstance(valor, date):
        return {"__tipo__": "date", "valor": valor.isoformat()}
    if isinstance(valor, list):
        return [_json_safe(item) for item in valor]
    if isinstance(valor, dict):
        return {chave: _json_safe(item) for chave, item in valor.items()}
    return valor


def _restaurar(valor: Any) -> Any:
    if isinstance(valor, dict):
        if valor.get("__tipo__") == "date":
            return date.fromisoformat(valor["valor"])
        if valor.get("__tipo__") == "datetime":
            return datetime.fromisoformat(valor["valor"])
        return {chave: _restaurar(item) for chave, item in valor.items()}
    if isinstance(valor, list):
        return [_restaurar(item) for item in valor]
    return valor


def _serializar(instancia: Any) -> dict[str, Any]:
    if dataclasses.is_dataclass(instancia):
        dados = {
            campo.name: getattr(instancia, campo.name, None)
            for campo in dataclasses.fields(instancia)
        }
    elif isinstance(instancia, dict):
        dados = dict(instancia)
    else:  # pragma: no cover - uso indevido
        raise TypeError(f"rascunho não suportado: {type(instancia)!r}")
    return {chave: _json_safe(valor) for chave, valor in dados.items()}


def _desserializar(modelo: type, dados: dict[str, Any] | None) -> Any:
    restaurado = {chave: _restaurar(valor) for chave, valor in (dados or {}).items()}
    if dataclasses.is_dataclass(modelo):
        validos = {campo.name for campo in dataclasses.fields(modelo)}
        return modelo(**{c: v for c, v in restaurado.items() if c in validos})  # type: ignore[misc]
    return restaurado


def _registro_para_modelo(modelo: type) -> _BaseRegistry | None:
    """Encontra o registro já instanciado para um modelo (usado no autossalvar)."""
    for registro in _REGISTRIES.values():
        if registro.modelo is modelo:
            return registro
    return None


class DraftMixin:
    """Mixin para rascunhos dataclass que se gravam sozinhos.

    Cada atributo definido após o rascunho estar associado a um chat dispara um
    upsert. Assim os handlers continuam fazendo ``rascunho.km = km`` e o estado
    já fica persistido — sem mudar a lógica de cada etapa.
    """

    __fluxo__: str = ""

    def __setattr__(self, nome: str, valor: Any) -> None:
        object.__setattr__(self, nome, valor)
        if nome.startswith("_"):
            return
        chat_id = self.__dict__.get("_chat_id")
        if chat_id is None:
            return
        registro = self.__dict__.get("_registro") or _registro_para_modelo(type(self))
        if registro is None:
            return
        try:
            registro.salvar(chat_id, self)
        except Exception:  # pragma: no cover - persistência não pode derrubar fluxo
            logger.exception("falha_ao_autossalvar_rascunho", extra={"fluxo": self.__fluxo__})


class RascunhoPersistente(Protocol):
    """Contrato mínimo esperado pelos handlers."""

    def get(self, chat_id: int, default: Any = None) -> Any: ...
    def pop(self, chat_id: int, default: Any = None) -> Any: ...
    def __getitem__(self, chat_id: int) -> Any: ...
    def __setitem__(self, chat_id: int, valor: Any) -> None: ...
    def __contains__(self, chat_id: object) -> bool: ...


class _BaseRegistry:
    def __init__(self, fluxo: str, modelo: type) -> None:
        self.fluxo = fluxo
        self.modelo = modelo

    # ------------------------------------------------------------- hooks
    def _carregar(self, chat_id: int) -> tuple[dict | None, str | None]: ...
    def _gravar(self, chat_id: int, dados: dict, etapa: str | None) -> None: ...
    def _apagar(self, chat_id: int) -> bool: ...

    # ------------------------------------------------------------- API dict
    def _marcar(self, valor: Any, chat_id: int) -> Any:
        """Associa o rascunho ao chat/registro para permitir autossalvamento."""
        if valor is not None and dataclasses.is_dataclass(valor):
            object.__setattr__(valor, "_chat_id", chat_id)
            object.__setattr__(valor, "_registro", self)
        return valor

    def get(self, chat_id: int, default: Any = None) -> Any:
        dados, _etapa = self._carregar(chat_id)
        if dados is None:
            return default
        return self._marcar(_desserializar(self.modelo, dados), chat_id)

    def __getitem__(self, chat_id: int) -> Any:
        valor = self.get(chat_id)
        if valor is None:
            raise KeyError(chat_id)
        return valor

    def __setitem__(self, chat_id: int, valor: Any) -> None:
        self._marcar(valor, chat_id)
        self.salvar(chat_id, valor)

    def __contains__(self, chat_id: object) -> bool:
        if not isinstance(chat_id, int):
            return False
        return self._carregar(chat_id)[0] is not None

    def pop(self, chat_id: int, default: Any = None) -> Any:
        dados, _etapa = self._carregar(chat_id)
        if dados is None:
            return default
        self._apagar(chat_id)
        return self._marcar(_desserializar(self.modelo, dados), chat_id)

    def tem_conversa(self, chat_id: int) -> bool:
        return self._carregar(chat_id)[0] is not None

    # ------------------------------------------------------------- persistência
    def salvar(self, chat_id: int, valor: Any) -> None:
        dados = _serializar(valor)
        _dados_atuais, etapa = self._carregar(chat_id)
        self._gravar(chat_id, dados, etapa)

    def definir_etapa(self, chat_id: int, etapa: str | None) -> None:
        dados, etapa_atual = self._carregar(chat_id)
        if dados is None:
            return  # sem rascunho ativo, nada a retomar
        if etapa_atual == etapa:
            return  # evita gravação redundante
        self._gravar(chat_id, dados, etapa)

    def obter_etapa(self, chat_id: int) -> str | None:
        return self._carregar(chat_id)[1]

    def limpar(self, chat_id: int) -> bool:
        return self._apagar(chat_id)


class SQLConversationRegistry(_BaseRegistry):
    """Registro persistido em PostgreSQL (tabela ``conversas``)."""

    def __init__(self, fluxo: str, modelo: type, db_factory=None) -> None:
        super().__init__(fluxo, modelo)
        self._db_factory = db_factory or get_database

    def _carregar(self, chat_id: int) -> tuple[dict | None, str | None]:
        try:
            with self._db_factory().unit_of_work(commit=False) as session:
                conversa = session.get(Conversa, chat_id)
                if conversa is None or conversa.fluxo != self.fluxo:
                    return None, None
                return dict(conversa.dados or {}), conversa.etapa
        except Exception:
            logger.exception("falha_ao_carregar_conversa", extra={"chat_id": chat_id})
            return None, None

    def _gravar(self, chat_id: int, dados: dict, etapa: str | None) -> None:
        try:
            with self._db_factory().unit_of_work() as session:
                conversa = session.get(Conversa, chat_id)
                if conversa is None:
                    conversa = Conversa(
                        chat_id=chat_id, fluxo=self.fluxo, etapa=etapa, dados=dados
                    )
                    session.add(conversa)
                else:
                    conversa.fluxo = self.fluxo
                    conversa.etapa = etapa
                    conversa.dados = dados
                    conversa.atualizadoEm = datetime.now(UTC)
        except Exception:
            logger.exception("falha_ao_gravar_conversa", extra={"chat_id": chat_id})

    def _apagar(self, chat_id: int) -> bool:
        try:
            with self._db_factory().unit_of_work() as session:
                conversa = session.get(Conversa, chat_id)
                if conversa is None:
                    return False
                session.delete(conversa)
                return True
        except Exception:
            logger.exception("falha_ao_apagar_conversa", extra={"chat_id": chat_id})
            return False


class MemoryConversationRegistry(_BaseRegistry):
    """Registro em memória (testes de unidade, sem banco)."""

    def __init__(self, fluxo: str, modelo: type) -> None:
        super().__init__(fluxo, modelo)
        self._dados: dict[int, tuple[dict, str | None]] = {}

    def _carregar(self, chat_id: int) -> tuple[dict | None, str | None]:
        item = self._dados.get(chat_id)
        if item is None:
            return None, None
        return item

    def _gravar(self, chat_id: int, dados: dict, etapa: str | None) -> None:
        self._dados[chat_id] = (dados, etapa)

    def _apagar(self, chat_id: int) -> bool:
        return self._dados.pop(chat_id, None) is not None


_REGISTRIES: dict[str, _BaseRegistry] = {}


def get_registry(fluxo: str, modelo: type, *, persistente: bool = True) -> _BaseRegistry:
    """Retorna o registro do fluxo (memoizado). Em testes, use ``persistente=False``."""
    chave = f"{fluxo}:{'sql' if persistente else 'mem'}"
    registro = _REGISTRIES.get(chave)
    if registro is None:
        classe = SQLConversationRegistry if persistente else MemoryConversationRegistry
        registro = classe(fluxo, modelo)
        _REGISTRIES[chave] = registro
    return registro


def limpar_registros() -> None:
    """Descarta registros memoizados (reinício/testes)."""
    _REGISTRIES.clear()


def registros_ativos() -> list[_BaseRegistry]:
    """Registros de fluxo já instanciados (para retomada após restart)."""
    return list(_REGISTRIES.values())
