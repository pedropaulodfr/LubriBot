from sqlalchemy import text
from repository.models import _Session, Notificacao, Usuario

session = _Session()

def ProcessarNotificacoes():
    # Lógica para processar notificações
    print("Processando notificações...")
    session = _Session()
    try:
        session.execute(text('CALL public."sp_CriarNotificacaoProximaManutencao"()'))
        session.commit()
    except Exception as e:
        session.rollback()
        print("Erro ao processar notificações:", e)
    finally:
        session.close()

def EnviaNotificacoes(bot):
    # Lógica para enviar notificações aos usuários
    print("Enviando notificações aos usuários...")
    session = _Session()
    try:
        notificacoes = session.query(Notificacao).filter(Notificacao.status == "Pendente").all()
        for notificacao in notificacoes:
            usuarioNotificacao = session.query(Usuario).filter(Usuario.id == notificacao.usuario_id).first()
            notificacao.status = "Enviada"
            session.commit()
            bot.send_message(usuarioNotificacao.telegram_id, notificacao.conteudo)

    except Exception as e:
        print("Erro ao enviar notificações:", e)
    finally:
        session.close()