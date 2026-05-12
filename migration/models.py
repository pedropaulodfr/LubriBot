from sqlalchemy import Column, Integer, Float, String, ForeignKey, Date, Text, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer)
    perfil = Column(String(12))
    primeiroNome = Column(String(50))
    ultimoNome = Column(String(50))
    usuarioNome = Column(String(50))
    CPF = Column(String(14))
    foto = Column(String(1000))
    email = Column(String(50))
    telefone = Column(String(11))
    status = Column(String(8))

class UsuarioParametro(Base):
    __tablename__ = 'usuarioparametros'
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    receberNotificacoes = Column(Boolean)
    diasNotificacao = Column(Integer)
    usuario = relationship("Usuario", backref="parametros")

class Veiculo(Base):
    __tablename__ = 'veiculos'
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    tipo = Column(String(20))
    placa = Column(String(7))
    renavam = Column(String(11))
    fabricante = Column(String(50))
    modelo = Column(String(50))
    anoModelo = Column(String(4))
    anoFabricacao = Column(String(4))
    cor = Column(String(20))
    status = Column(String(8))
    usuario = relationship("Usuario", backref="veiculos")

class VeiculoDica(Base):
    __tablename__ = 'veiculodica'
    id = Column(Integer, primary_key=True)
    veiculo_id = Column(Integer, ForeignKey('veiculos.id'))
    texto = Column(Text)
    datacriacao = Column(Date)
    veiculo = relationship("Veiculo", backref="veiculodica")

class VeiculoDiagnosticos(Base):
    __tablename__ = 'veiculodiagnosticos'
    id = Column(Integer, primary_key=True)
    veiculo_id = Column(Integer, ForeignKey('veiculos.id'))
    problema = Column(Text)
    diagnostico = Column(Text)
    datacriacao = Column(Date)
    resolvido = Column(Boolean)
    util = Column(Boolean)
    veiculo = relationship("Veiculo", backref="veiculodiagnosticos")

class Manutencao(Base):
    __tablename__ = 'manutencoes'
    id = Column(Integer, primary_key=True)
    data = Column(Date)
    veiculo_id = Column(Integer, ForeignKey('veiculos.id'))
    km = Column(Integer)
    observacao = Column(String(100))
    status = Column(String(10))
    custo = Column(Float)
    imagem = Column(Text)
    imagemNotaServico = Column(Text)
    veiculo = relationship("Veiculo", backref="manutencoes")

class Servico(Base):
    __tablename__ = 'servicos'
    id = Column(Integer, primary_key=True)
    descricao = Column(String(50))
    status = Column(String(8))
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    usuario = relationship("Usuario", backref="servicos")

class Produto(Base):
    __tablename__ = 'produtos'
    id = Column(Integer, primary_key=True)
    descricao = Column(String(50))
    status = Column(String(8))
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    usuario = relationship("Usuario", backref="produtos")

class ManutencaoServico(Base):
    __tablename__ = 'manutencaoservicos'
    id = Column(Integer, primary_key=True)
    manutencao_id = Column(Integer, ForeignKey('manutencoes.id'))
    servico_id = Column(Integer, ForeignKey('servicos.id'))
    manutencao = relationship("Manutencao", backref="manutencaoservicos")
    servico = relationship("Servico", backref="manutencaoservicos")

class ManutencaoProduto(Base):
    __tablename__ = 'manutencaoprodutos'
    id = Column(Integer, primary_key=True)
    manutencao_id = Column(Integer, ForeignKey('manutencoes.id'))
    produto_id = Column(Integer, ForeignKey('produtos.id'))
    manutencao = relationship("Manutencao", backref="manutencaoprodutos")
    produto = relationship("Produto", backref="manutencaoprodutos")

class ServicoProduto(Base):
    __tablename__ = 'servicoprodutos'
    id = Column(Integer, primary_key=True)
    servico_id = Column(Integer, ForeignKey('servicos.id'))
    produto_id = Column(Integer, ForeignKey('produtos.id'))
    servico = relationship("Servico", backref="servicoprodutos")
    produto = relationship("Produto", backref="servicoprodutos")

class Notificacao(Base):
    __tablename__ = 'notificacoes'
    id = Column(Integer, primary_key=True)
    dataNotificacao = Column(Date)
    tipoNotificacao = Column(String(20))
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    servico_id = Column(Integer, ForeignKey('servicos.id'))
    manutencao_id = Column(Integer, ForeignKey('manutencoes.id'))
    veiculo_id = Column(Integer, ForeignKey('veiculos.id'))
    titulo = Column(String(100))
    conteudo = Column(Text)
    status = Column(String(8))
    usuario = relationship("Usuario", backref="notificacoes")
    servico = relationship("Servico", backref="notificacoes")
    veiculo = relationship("Veiculo", backref="notificacoes")
    manutencao = relationship("Manutencao", backref="notificacoes")
