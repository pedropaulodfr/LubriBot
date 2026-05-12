import logging
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from migration.models import Base

logger = logging.getLogger(__name__)

def load_table_data(session: Session, model, data_list, batch_size=500):
    """
    Insere dados na tabela do Supabase preservando IDs e tratando conflitos.
    """
    if not data_list:
        logger.info(f"Nenhum dado para carregar em {model.__tablename__}.")
        return 0

    inserted_count = 0
    try:
        logger.info(f"Carregando {len(data_list)} registros em {model.__tablename__} (Supabase)...")
        
        # Converte objetos SQLAlchemy para dicionários
        data_dicts = []
        for obj in data_list:
            d = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
            data_dicts.append(d)

        # Inserção em lotes
        for i in range(0, len(data_dicts), batch_size):
            batch = data_dicts[i:i + batch_size]
            
            stmt = insert(model).values(batch)
            # Preserva IDs e ignora se já existir (idempotência)
            stmt = stmt.on_conflict_do_nothing(index_elements=['id'])
            
            session.execute(stmt)
            inserted_count += len(batch)
            logger.info(f"Lote enviado: {inserted_count}/{len(data_dicts)} em {model.__tablename__}")

        session.commit()
        logger.info(f"Sucesso: Carga concluída para {model.__tablename__}.")
        return inserted_count
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao carregar dados em {model.__tablename__}: {e}")
        raise
