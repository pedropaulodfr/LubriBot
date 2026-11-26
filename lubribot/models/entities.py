"""Mapeamento SQLAlchemy — fonte única de verdade do schema.

Decisões:
- Nomes de tabela e coluna foram preservados **exatamente** como no banco em uso
  (inclusive camelCase), para não exigir migração destrutiva de dados.
- Relacionamentos usam ``lazy="selectin"`` em vez de ``"subquery"``: carrega em
  lote (evita N+1) e mantém os objetos legíveis depois do commit, que é como os
  handlers atuais consomem os modelos.
- ``Servico.intervaloDias`` passa a existir de forma explícita e opcional. Antes
  era referenciada em código e documentação, mas não existia no modelo (e a
  procedure que fazia o cálculo não está versionada). Ver ``docs/DECISIONS.md``.
- Nenhum ``create_all`` aqui: o schema é responsabilidade do Alembic.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarativa de todos os modelos."""


# ----------------------------------------------------------------------------
# Usuários
# ----------------------------------------------------------------------------
class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        Index("ix_usuarios_telegram_id", "telegram_id"),
        Index("ix_usuarios_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int | None] = mapped_column(Integer)
    perfil: Mapped[str | None] = mapped_column(String(12))
    primeiroNome: Mapped[str | None] = mapped_column(String(50))
    ultimoNome: Mapped[str | None] = mapped_column(String(50))
    usuarioNome: Mapped[str | None] = mapped_column(String(50))
    CPF: Mapped[str | None] = mapped_column(String(14))
    foto: Mapped[str | None] = mapped_column(String(1000))
    email: Mapped[str | None] = mapped_column(String(50))
    telefone: Mapped[str | None] = mapped_column(String(11))
    status: Mapped[str | None] = mapped_column(String(8))

    parametros: Mapped[list[UsuarioParametro]] = relationship(
        back_populates="usuario", lazy="selectin"
    )
    veiculos: Mapped[list[Veiculo]] = relationship(back_populates="usuario", lazy="selectin")


class UsuarioParametro(Base):
    __tablename__ = "usuarioparametros"
    __table_args__ = (
        Index("ix_usuarioparametros_usuario_id", "usuario_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    receberNotificacoes: Mapped[bool | None] = mapped_column(Boolean, default=True)
    diasNotificacao: Mapped[int | None] = mapped_column(Integer, default=7)

    usuario: Mapped[Usuario | None] = relationship(back_populates="parametros", lazy="selectin")


# ----------------------------------------------------------------------------
# Veículos
# ----------------------------------------------------------------------------
class Veiculo(Base):
    __tablename__ = "veiculos"
    __table_args__ = (
        Index("ix_veiculos_usuario_id", "usuario_id"),
        Index("ix_veiculos_placa", "placa"),
        Index("ix_veiculos_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    tipo: Mapped[str | None] = mapped_column(String(20))
    placa: Mapped[str | None] = mapped_column(String(7))
    renavam: Mapped[str | None] = mapped_column(String(11))
    fabricante: Mapped[str | None] = mapped_column(String(50))
    modelo: Mapped[str | None] = mapped_column(String(50))
    anoModelo: Mapped[str | None] = mapped_column(String(4))
    anoFabricacao: Mapped[str | None] = mapped_column(String(4))
    cor: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str | None] = mapped_column(String(8))

    usuario: Mapped[Usuario | None] = relationship(back_populates="veiculos", lazy="selectin")
    manutencoes: Mapped[list[Manutencao]] = relationship(
        back_populates="veiculo", lazy="selectin"
    )
    dicas: Mapped[list[VeiculoDica]] = relationship(
        back_populates="veiculo", lazy="selectin"
    )
    diagnosticos: Mapped[list[VeiculoDiagnosticos]] = relationship(
        back_populates="veiculo", lazy="selectin"
    )


class VeiculoDica(Base):
    __tablename__ = "veiculodica"
    __table_args__ = (Index("ix_veiculodica_veiculo_id", "veiculo_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    veiculo_id: Mapped[int | None] = mapped_column(ForeignKey("veiculos.id"))
    texto: Mapped[str | None] = mapped_column(Text)
    datacriacao: Mapped[date | None] = mapped_column(Date)

    veiculo: Mapped[Veiculo | None] = relationship(back_populates="dicas", lazy="selectin")


# Nome legado preservado para não quebrar imports existentes.
class VeiculoDiagnosticos(Base):
    __tablename__ = "veiculodiagnosticos"
    __table_args__ = (
        Index("ix_veiculodiagnosticos_veiculo_id", "veiculo_id"),
        Index("ix_veiculodiagnosticos_datacriacao", "datacriacao"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    veiculo_id: Mapped[int | None] = mapped_column(ForeignKey("veiculos.id"))
    problema: Mapped[str | None] = mapped_column(Text)
    diagnostico: Mapped[str | None] = mapped_column(Text)
    datacriacao: Mapped[date | None] = mapped_column(Date)
    resolvido: Mapped[bool | None] = mapped_column(Boolean)
    util: Mapped[bool | None] = mapped_column(Boolean)

    veiculo: Mapped[Veiculo | None] = relationship(
        back_populates="diagnosticos", lazy="selectin"
    )


VeiculoDiagnostico = VeiculoDiagnosticos


# ----------------------------------------------------------------------------
# Catálogo
# ----------------------------------------------------------------------------
class Servico(Base):
    __tablename__ = "servicos"
    __table_args__ = (
        Index("ix_servicos_usuario_id", "usuario_id"),
        Index("ix_servicos_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    descricao: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str | None] = mapped_column(String(8))
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    # Intervalo recomendado de troca/revisão, em dias. NULL = usa o padrão global.
    intervaloDias: Mapped[int | None] = mapped_column(Integer)

    usuario: Mapped[Usuario | None] = relationship(lazy="selectin")


class Produto(Base):
    __tablename__ = "produtos"
    __table_args__ = (
        Index("ix_produtos_usuario_id", "usuario_id"),
        Index("ix_produtos_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    descricao: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str | None] = mapped_column(String(8))
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))

    usuario: Mapped[Usuario | None] = relationship(lazy="selectin")


class ServicoProduto(Base):
    __tablename__ = "servicoprodutos"
    __table_args__ = (
        Index("ix_servicoprodutos_par", "servico_id", "produto_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    servico_id: Mapped[int | None] = mapped_column(ForeignKey("servicos.id"))
    produto_id: Mapped[int | None] = mapped_column(ForeignKey("produtos.id"))

    servico: Mapped[Servico | None] = relationship(lazy="selectin")
    produto: Mapped[Produto | None] = relationship(lazy="selectin")


# ----------------------------------------------------------------------------
# Manutenções
# ----------------------------------------------------------------------------
class Manutencao(Base):
    __tablename__ = "manutencoes"
    __table_args__ = (
        Index("ix_manutencoes_veiculo_id", "veiculo_id"),
        Index("ix_manutencoes_data", "data"),
        Index("ix_manutencoes_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    data: Mapped[date | None] = mapped_column(Date)
    veiculo_id: Mapped[int | None] = mapped_column(ForeignKey("veiculos.id"))
    km: Mapped[int | None] = mapped_column(Integer)
    observacao: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str | None] = mapped_column(String(10))
    custo: Mapped[float | None] = mapped_column(Float)
    imagem: Mapped[str | None] = mapped_column(Text)
    imagemNotaServico: Mapped[str | None] = mapped_column(Text)

    veiculo: Mapped[Veiculo | None] = relationship(back_populates="manutencoes", lazy="selectin")
    itens_servico: Mapped[list[ManutencaoServico]] = relationship(
        back_populates="manutencao", lazy="selectin"
    )
    itens_produto: Mapped[list[ManutencaoProduto]] = relationship(
        back_populates="manutencao", lazy="selectin"
    )


class ManutencaoServico(Base):
    __tablename__ = "manutencaoservicos"
    __table_args__ = (Index("ix_manutencaoservicos_manutencao_id", "manutencao_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manutencao_id: Mapped[int | None] = mapped_column(ForeignKey("manutencoes.id"))
    servico_id: Mapped[int | None] = mapped_column(ForeignKey("servicos.id"))

    manutencao: Mapped[Manutencao | None] = relationship(
        back_populates="itens_servico", lazy="selectin"
    )
    servico: Mapped[Servico | None] = relationship(lazy="selectin")


class ManutencaoProduto(Base):
    __tablename__ = "manutencaoprodutos"
    __table_args__ = (Index("ix_manutencaoprodutos_manutencao_id", "manutencao_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manutencao_id: Mapped[int | None] = mapped_column(ForeignKey("manutencoes.id"))
    produto_id: Mapped[int | None] = mapped_column(ForeignKey("produtos.id"))

    manutencao: Mapped[Manutencao | None] = relationship(
        back_populates="itens_produto", lazy="selectin"
    )
    produto: Mapped[Produto | None] = relationship(lazy="selectin")


# ----------------------------------------------------------------------------
# Notificações (outbox persistido)
# ----------------------------------------------------------------------------
class Notificacao(Base):
    """Notificação e, ao mesmo tempo, registro de outbox.

    Cada linha é um evento a entregar. ``chave`` é a chave de idempotência:
    duas execuções concorrentes não criam duplicata (índice único).
    """

    __tablename__ = "notificacoes"
    __table_args__ = (
        Index("ix_notificacoes_status", "status"),
        Index("ix_notificacoes_usuario_id", "usuario_id"),
        Index("ix_notificacoes_manutencao_id", "manutencao_id"),
        UniqueConstraint("chave", name="uq_notificacoes_chave"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataNotificacao: Mapped[date | None] = mapped_column(Date)
    tipoNotificacao: Mapped[str | None] = mapped_column(String(20))
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    servico_id: Mapped[int | None] = mapped_column(ForeignKey("servicos.id"))
    manutencao_id: Mapped[int | None] = mapped_column(ForeignKey("manutencoes.id"))
    veiculo_id: Mapped[int | None] = mapped_column(ForeignKey("veiculos.id"))
    titulo: Mapped[str | None] = mapped_column(String(100))
    conteudo: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(8))

    # --- colunas de controle do outbox ---
    chave: Mapped[str | None] = mapped_column(String(120))
    tentativas: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    criadaEm: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ultimaTentativaEm: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    proximaTentativaEm: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    enviadaEm: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ultimoErro: Mapped[str | None] = mapped_column(Text)

    usuario: Mapped[Usuario | None] = relationship(lazy="selectin")
    servico: Mapped[Servico | None] = relationship(lazy="selectin")
    veiculo: Mapped[Veiculo | None] = relationship(lazy="selectin")
    manutencao: Mapped[Manutencao | None] = relationship(lazy="selectin")


class Conversa(Base):
    """Estado de uma conversa em andamento (rascunho persistido).

    Sobrevive a restart: cada chat tem no máximo uma conversa ativa. ``dados`` é
    o rascunho serializado do fluxo e ``etapa`` é o nome do próximo passo, usado
    para retomar de onde parou.
    """

    __tablename__ = "conversas"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    fluxo: Mapped[str] = mapped_column(String(32), nullable=False)
    etapa: Mapped[str | None] = mapped_column(String(64))
    dados: Mapped[dict | None] = mapped_column(JSONB)
    atualizadoEm: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


__all__ = [
    "Base",
    "Conversa",
    "Manutencao",
    "ManutencaoProduto",
    "ManutencaoServico",
    "Notificacao",
    "Produto",
    "Servico",
    "ServicoProduto",
    "Usuario",
    "UsuarioParametro",
    "Veiculo",
    "VeiculoDiagnostico",
    "VeiculoDiagnosticos",
    "VeiculoDica",
]
