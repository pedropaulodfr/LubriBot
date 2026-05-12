import logging
from sqlalchemy.orm import Session
from migration.models import Base

logger = logging.getLogger(__name__)

def validate_migration(source_session: Session, target_session: Session, models_list):
    """
    Valida a migração comparando a contagem de registros por tabela.
    """
    report = []
    logger.info("Iniciando validação da migração...")
    
    for model in models_list:
        table_name = model.__tablename__
        source_count = source_session.query(model).count()
        target_count = target_session.query(model).count()
        
        status = "OK" if source_count == target_count else "DIVERGENTE"
        
        if status == "DIVERGENTE" and target_count > source_count:
            # Pode acontecer se houver dados pré-existentes no Supabase
            status = "OK (Destino possui mais dados)"
            
        report.append({
            "tabela": table_name,
            "origem": source_count,
            "destino": target_count,
            "status": status
        })
        logger.info(f"Tabela {table_name}: Origem={source_count}, Destino={target_count} -> {status}")
        
    return report
