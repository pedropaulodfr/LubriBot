import logging
from sqlalchemy.orm import Session
from migration.models import Base

logger = logging.getLogger(__name__)

def extract_table_data(session: Session, model):
    """
    Extrai todos os dados de uma tabela específica do banco legado.
    """
    try:
        logger.info(f"Extraindo dados da tabela {model.__tablename__}...")
        records = session.query(model).all()
        logger.info(f"Sucesso: {len(records)} registros extraídos de {model.__tablename__}.")
        return records
    except Exception as e:
        logger.error(f"Erro ao extrair dados de {model.__tablename__}: {e}")
        raise
