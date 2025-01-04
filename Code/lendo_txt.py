import pandas as pd
import pyodbc
from dotenv import load_dotenv
import os

load_dotenv()



# Carregar dados do Excel
excel_file = os.getenv('EXCEL')
df = pd.read_excel(excel_file)

# Conectar ao SQL Server
db_server = os.getenv('SERVER')
db_name = os.getenv('DATABASE_BASELINE')
conn = pyodbc.connect(f'DRIVER=SQL Server;SERVER={db_server};DATABASE={db_name};Trusted_Connection=yes')
cursor = conn.cursor()

# Inserir dados na tabela   # Certifique-se de que as colunas no Excel correspondem ao que está sendo inserido na tabela

query = f"TRUNCATE TABLE p_codigo_postal"

cursor.execute(query)


for index, row in df.iterrows():
    try:
        cursor.execute("""
            INSERT INTO p_codigo_postal (id_codigo_distrito, CP3, CP4, Concelho, codigo_postal_clean, codigo_postal_baseline)
            VALUES (?, ?, ?, ?, ?, ?)
        """, row['id_codigo_distrito'], row['CP3'], row['CP4'], row['Concelho'], row['codigo_postal_clean'], row['codigo_postal_baseline'])

        print(f' Os dados estão sendo inseridos na base de dados aguarde........ linha: {index}')
    except Exception as e:
        print(f'Erro ao inserir dados na base de dados {e}')

# Comitar as alterações no banco de dados
conn.commit()

print('Todos os dados foram inseridos')

# Fechar o cursor e a conexão
cursor.close()
conn.close()
