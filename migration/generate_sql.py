import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path para permitir importações absolutas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from migration.models import (
    Usuario, UsuarioParametro, Veiculo, Servico, Produto,
    VeiculoDica, VeiculoDiagnosticos, Manutencao,
    ServicoProduto, ManutencaoServico, ManutencaoProduto, Notificacao
)

MODELS_ORDER = [
    Usuario, UsuarioParametro, Veiculo, Servico, Produto,
    VeiculoDica, VeiculoDiagnosticos, Manutencao,
    ServicoProduto, ManutencaoServico, ManutencaoProduto, Notificacao
]

def generate_sql():
    load_dotenv()
    source_url = os.getenv('SOURCE_DB_URL') or os.getenv('STRING_CONNECTION')
    
    if not source_url:
        logger.error("SOURCE_DB_URL não configurado.")
        return

    source_engine = create_engine(source_url)
    SourceSession = sessionmaker(bind=source_engine)
    session = SourceSession()

    sql_output = "SET session_replication_role = 'replica';\n\n"

    for model in MODELS_ORDER:
        table_name = model.__tablename__
        records = session.query(model).all()
        if not records:
            continue
            
        logger.info(f"Gerando SQL para {table_name} ({len(records)} registros)...")
        
        columns = [c.name for c in model.__table__.columns]
        col_str = ", ".join([f'"{c}"' for c in columns])
        
        for record in records:
            values = []
            for col in columns:
                val = getattr(record, col)
                if val is None:
                    values.append("NULL")
                elif isinstance(val, (int, float)):
                    values.append(str(val))
                elif isinstance(val, bool):
                    values.append("TRUE" if val else "FALSE")
                else:
                    # Escape single quotes
                    escaped_val = str(val).replace("'", "''")
                    values.append(f"'{escaped_val}'")
            
            val_str = ", ".join(values)
            sql_output += f'INSERT INTO public."{table_name}" ({col_str}) VALUES ({val_str}) ON CONFLICT ("id") DO NOTHING;\n'
        
        sql_output += "\n"

    sql_output += "SET session_replication_role = 'origin';\n"
    
    with open("migration_data.sql", "w", encoding="utf-8") as f:
        f.write(sql_output)
    
    logger.info("Sucesso! SQL gerado em migration_data.sql")
    session.close()

if __name__ == "__main__":
    generate_sql()
