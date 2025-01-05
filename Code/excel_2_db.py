import pandas as pd
import pyodbc
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Carregar dados do Excel
excel_file = os.getenv('EXCEL')
if not excel_file or not os.path.exists(excel_file):
    raise FileNotFoundError(f"Arquivo Excel não encontrado: {excel_file}")

df = pd.read_excel(excel_file)

# Configurar conexão ao SQL Server
db_server = os.getenv('SERVER')
db_name = os.getenv('DATABASE_BASELINE')
if not db_server or not db_name:
    raise ValueError("As variáveis de ambiente SERVER e DATABASE_BASELINE devem ser configuradas.")

# Criar engine do SQLAlchemy para o banco de dados
connection_string = f"mssql+pyodbc://{db_server}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
engine = create_engine(connection_string)

# Inserir dados na tabela utilizando to_sql com replace
if not df.empty:
    try:
        df.to_sql("p_codigo_postal", engine, if_exists='replace', index=False)
        print("Dados inseridos com sucesso na tabela p_codigo_postal.")
    except Exception as e:
        print(f"Erro ao inserir dados na tabela p_codigo_postal: {e}")
else:
    print("O DataFrame está vazio. Nenhum dado foi inserido.")

print("Processo concluído com sucesso.")
