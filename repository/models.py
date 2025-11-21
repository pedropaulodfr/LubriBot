from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey, Date
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from config import STRING_CONNECTION

engine = create_engine(STRING_CONNECTION)
Base = declarative_base()
_Session = sessionmaker(engine)

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

    usuario = relationship("Usuario", backref="veiculos", lazy='subquery')

class Manutencao(Base):
    __tablename__ = 'manutencoes'
    
    id = Column(Integer, primary_key=True)
    data = Column(Date)
    veiculo_id = Column(Integer, ForeignKey('veiculos.id'))
    km = Column(Integer)
    observacao = Column(String(100))
    status = Column(String(10)),
    custo = Column(Float)

    veiculo = relationship("Veiculo", backref="manutencoes", lazy='subquery')

class ManutencaoServico(Base):
    __tablename__ = 'manutencaoservicos'
    
    id = Column(Integer, primary_key=True)
    manutencao_id = Column(Integer, ForeignKey('manutencoes.id'))
    servico_id = Column(Integer, ForeignKey('servicos.id'))

    manutencao = relationship("Manutencao", backref="manutencaoservicos", lazy='subquery')
    servico = relationship("Servico", backref="manutencaoservicos", lazy='subquery')

class Servico(Base):
    __tablename__ = 'servicos'
    
    id = Column(Integer, primary_key=True)
    descricao = Column(String(50))
    status = Column(String(8))

class Produto(Base):
    __tablename__ = 'produtos'
    
    id = Column(Integer, primary_key=True)
    descricao = Column(String(50))
    status = Column(String(8))

class ServicoProduto(Base):
    __tablename__ = 'servicoprodutos'
    
    id = Column(Integer, primary_key=True)
    servico_id = Column(Integer, ForeignKey('servicos.id'))
    produto_id = Column(Integer, ForeignKey('produtos.id'))

    servico = relationship("Servico", backref="servicoprodutos", lazy='subquery')
    produto = relationship("Produto", backref="servicoprodutos", lazy='subquery')


Base.metadata.create_all(engine)    