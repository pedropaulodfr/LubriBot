import os
import sys
import logging

# Adiciona o diretório raiz ao path para permitir importações absolutas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from migration.models import (
    Usuario, UsuarioParametro, Veiculo, Servico, Produto,
    VeiculoDica, VeiculoDiagnosticos, Manutencao,
    ServicoProduto, ManutencaoServico, ManutencaoProduto, Notificacao
)
from migration.extract import extract_table_data
from migration.load import load_table_data
from migration.validate import validate_migration

# Ordem de migração baseada em Foreign Keys
MODELS_ORDER = [
    Usuario,
    UsuarioParametro,
    Veiculo,
    Servico,
    Produto,
    VeiculoDica,
    VeiculoDiagnosticos,
    Manutencao,
    ServicoProduto,
    ManutencaoServico,
    ManutencaoProduto,
    Notificacao
]

def run_migration():
    load_dotenv()
    
    source_url = os.getenv('SOURCE_DB_URL') or os.getenv('STRING_CONNECTION')
    target_url = os.getenv('SUPABASE_DB_URL')
    
    if not source_url or not target_url:
        logger.error("Erro: SOURCE_DB_URL ou SUPABASE_DB_URL não configurados no .env")
        print("\n[!] Por favor, configure as variáveis no seu arquivo .env:")
        print("SOURCE_DB_URL=postgresql://user:pass@host:port/dbname")
        print("SUPABASE_DB_URL=postgresql://postgres:password@db.jsjxkfczgihrfhgxxzft.supabase.co:5432/postgres")
        return

    # Engines e Sessões
    try:
        source_engine = create_engine(source_url)
        target_engine = create_engine(target_url)
        
        SourceSession = sessionmaker(bind=source_engine)
        TargetSession = sessionmaker(bind=target_engine)
        
        source_session = SourceSession()
        target_session = TargetSession()
        
        logger.info("Conexões estabelecidas com sucesso.")
        
        # Início da Migração
        results = {}
        for model in MODELS_ORDER:
            table_name = model.__tablename__
            logger.info(f"--- Iniciando migração da tabela: {table_name} ---")
            
            # Extrair
            data = extract_table_data(source_session, model)
            
            # Carregar
            count = load_table_data(target_session, model, data)
            results[table_name] = count
            
        # Validação
        report = validate_migration(source_session, target_session, MODELS_ORDER)
        
        # Relatório Final
        print("\n" + "="*50)
        print("RELATÓRIO FINAL DE MIGRAÇÃO")
        print("="*50)
        print(f"{'Tabela':<25} | {'Origem':<8} | {'Destino':<8} | {'Status'}")
        print("-" * 50)
        for item in report:
            print(f"{item['tabela']:<25} | {item['origem']:<8} | {item['destino']:<8} | {item['status']}")
        print("="*50)
        
        source_session.close()
        target_session.close()
        logger.info("Migração finalizada.")

    except Exception as e:
        logger.error(f"Erro fatal durante a migração: {e}")
        raise

if __name__ == "__main__":
    run_migration()
