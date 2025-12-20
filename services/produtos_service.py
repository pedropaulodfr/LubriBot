from repository.models import Produto, _Session
from sqlalchemy import func, cast, String

def get_all_produtos():
    session = _Session()
    try:
        produtos = session.query(
            func.concat(Produto.descricao, " (", func.lpad(cast(Produto.id, String), 6, "0"), ")").label("descricao_completa"),
        ).filter(Produto.status == "Ativo").all()
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