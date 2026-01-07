from repository.models import Produto, _Session
from sqlalchemy import func, cast, String, or_

def get_all_produtos():
    session = _Session()
    try:
        produtos = session.query(
            func.concat(Produto.descricao, " (", func.lpad(cast(Produto.id, String), 6, "0"), ")").label("descricao_completa"),
        ).filter(Produto.status == "Ativo").all()
        return produtos
    finally:
        session.close()


def get_all_produtos_manutencao(usuario_id):
    session = _Session()
    try:
        produtos = session.query(
            func.concat(Produto.descricao, " (", func.lpad(cast(Produto.id, String), 6, "0"), ")").label("descricao_completa"),
        ).filter(Produto.status == "Ativo").filter(or_(Produto.usuario_id.is_(None), Produto.usuario_id == usuario_id)).all()
        return produtos
    finally:
        session.close()


def get_produto_by_descricao_completa(descricao_completa):
    session = _Session()
    try:
        produto = session.query(Produto).filter(
            func.concat(Produto.descricao, " (", func.lpad(cast(Produto.id, String), 6, "0"), ")") == descricao_completa,
            Produto.status == "Ativo"
        ).first()
        return produto
    finally:
        session.close()


def get_produtos_by_usuario(usuario_id):
    session = _Session()
    try:
        produtos = session.query(Produto).filter(Produto.usuario_id == usuario_id, Produto.status == "Ativo").all()
        return produtos
    finally:
        session.close()


def get_produtos_by_telegram_id(telegram_id):
    session = _Session()
    try:
        produtos = session.query(Produto).join(Produto.usuario).filter(Produto.usuario.has(telegram_id=telegram_id), Produto.status == "Ativo").all()
        return produtos
    finally:
        session.close()