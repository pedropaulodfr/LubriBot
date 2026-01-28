from repository.models import Manutencao, Veiculo, Usuario,  ManutencaoServico, _Session

def get_manutencoes_by_usuario(usuario_id):
    session = _Session()
    try:
        manutencoes = session.query(Manutencao).join(ManutencaoServico).join(Veiculo).join(Usuario).filter(Usuario.id == usuario_id).order_by(Manutencao.data).all()
        return manutencoes
    finally:
        session.close()


def get_manutencoes_by_veiculos(veiculo_id):
    session = _Session()
    try:
        manutencoes = session.query(Manutencao).join(ManutencaoServico).join(Veiculo).join(Usuario).filter(Manutencao.veiculo_id == veiculo_id).order_by(Manutencao.data).all()
        return manutencoes
    finally:
        session.close()
