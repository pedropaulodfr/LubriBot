from repository.models import Veiculo, _Session

def get_veiculos_by_usuario(usuario_id):
    session = _Session()
    try:
        veiculos = session.query(Veiculo).filter(Veiculo.usuario_id == usuario_id, Veiculo.status == "Ativo").all()
        return veiculos
    finally:
        session.close()


def get_veiculos_by_telegram_id(telegram_id):
    session = _Session()
    try:
        veiculos = session.query(Veiculo).join(Veiculo.usuario).filter(Veiculo.usuario.has(telegram_id=telegram_id), Veiculo.status == "Ativo").all()
        return veiculos
    finally:
        session.close()


def get_veiculo_by_placa(placa):
    session = _Session()
    try:
        veiculo = session.query(Veiculo).filter(Veiculo.placa == placa.replace("-", ""), Veiculo.status == "Ativo").first()
        return veiculo
    finally:
        session.close()


def add_veiculo(usuario_id, marca, modelo, ano, placa):
    session = _Session()
    try:
        novo_veiculo = Veiculo(
            usuario_id=usuario_id,
            marca=marca,
            modelo=modelo,
            ano=ano,
            placa=placa
        )
        session.add(novo_veiculo)
        session.commit()
        return novo_veiculo
    finally:
        session.close()