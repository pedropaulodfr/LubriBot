from repository.models import Usuario, _Session

def get_usuario_by_telegram_id(telegram_id):
    session = _Session()
    try:
        usuario = session.query(Usuario).filter(Usuario.telegram_id == telegram_id).first()
        return usuario
    finally:
        session.close()

def add_usuario(telegram_id, perfil, primeiroNome, ultimoNome, username, status):
    session = _Session()
    try:
        novo_usuario = Usuario(
            telegram_id=telegram_id,
            perfil=perfil,
            primeiroNome=primeiroNome,
            ultimoNome=ultimoNome,
            username=username,
            status=status)
        session.add(novo_usuario)
        session.commit()
        return novo_usuario
    finally:
        session.close()