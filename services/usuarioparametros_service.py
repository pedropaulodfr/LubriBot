from repository.models import UsuarioParametro, Usuario, _Session

def get_parametros_usuario_by_telegram_id(telegram_id):
    session = _Session()
    try:
        parametros = session.query(UsuarioParametro).join(Usuario).filter(Usuario.telegram_id == telegram_id).first()
        return parametros
    finally:
        session.close()