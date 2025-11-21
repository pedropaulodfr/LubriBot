from repository.models import Servico, _Session

def get_all_servicos():
    session = _Session()
    try:
        servicos = session.query(Servico).filter(Servico.status == "Ativo").all()
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