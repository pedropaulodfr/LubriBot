from repository.models import Servico, _Session
from sqlalchemy import or_

def get_all_servicos(usuario_id=None):
    session = _Session()
    try:
        if usuario_id is None:
            servicos = session.query(Servico).filter(Servico.status == "Ativo").all()
        else:
            servicos = (
                session.query(Servico)
                .filter(Servico.status == "Ativo")
                .filter(or_(Servico.usuario_id.is_(None), Servico.usuario_id == usuario_id))
                .all()
            )
        return servicos
    finally:
        session.close()

def get_servico_by_descricao(descricao):
    session = _Session()
    try:
        servico = session.query(Servico).filter(Servico.descricao == descricao).first()
        return servico
    finally:
        session.close()

def get_servico_by_id(id):
    session = _Session()
    try:
        servico = session.query(Servico).filter(Servico.id == id).first()
        return servico
    finally:
        session.close()