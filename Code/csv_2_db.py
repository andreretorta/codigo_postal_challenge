import os
import pandas as pd
import requests
from pathlib import Path
from sqlalchemy import create_engine
from dotenv import load_dotenv
import glob


class ProcessadorCodigoPostal:
    def __init__(self, csv_name, env_file):
        self.csv_name = csv_name
        self.env_file = env_file
        self.df = None
        self.base_url = None
        self.success_list = []
        self.error_404_list = []
        self.other_error_list = []
        self.db_engine = None
        self.csv_path = os.getenv('PATH')

        self._setup()

    def _setup(self):
        """Inicializa variáveis de ambiente, configurações e localiza o CSV."""
        # Carregar variáveis de ambiente
        load_dotenv(self.env_file)

        # Configurar pandas
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)

        # Carregar a URL base da API
        self.base_url = os.getenv('BASE_URL')
        if not self.base_url:
            raise ValueError("A URL base não foi encontrada no arquivo .env.")

        # Configurar a conexão com o banco de dados
        db_server = os.getenv('SERVER')
        db_name = os.getenv('DATABASE_BASELINE')
        connection_string = f"mssql+pyodbc://{db_server}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
        self.db_engine = create_engine(connection_string)

        # Localizar o arquivo CSV
        self.file = self.get_csv_file()

    def get_csv_file(self):
        """Localiza o arquivo CSV e retorna o caminho do primeiro arquivo encontrado."""
        files = glob.glob(os.path.join(self.csv_path, self.csv_name))
        if not files:
            raise FileNotFoundError(f"Nenhum arquivo encontrado para o padrão: {os.path.join(self.csv_path, self.csv_name)}")
        return files[0]  # Seleciona o primeiro arquivo se houver múltiplos

    def load_and_prepare_data(self):
        """Carrega e prepara os dados do arquivo CSV."""
        self.df = pd.read_csv(self.file)  # Utiliza o primeiro arquivo encontrado
        self.df = self.df.rename(columns={'CP7': 'CP'})
        self.df['CP'] = self.df['CP'].str.replace('-', '', regex=True)

    def fetch_postal_data(self, cp):
        """Busca os dados da API para um código postal."""
        url = f"{self.base_url}/{cp}?json=1"
        response = requests.get(url)
        return response

    def process_responses(self):
        """Processa as respostas da API para todos os códigos postais."""
        for cp in self.df['CP']:
            response = self.fetch_postal_data(cp)

            if response.status_code == 200:
                data = response.json()
                df_cp = pd.json_normalize(data)
                df_cp = df_cp[['CP', 'Concelho','Distrito']]
                self.success_list.append(df_cp)

            elif response.status_code == 404:
                print(f"Erro: {response.status_code} para o código postal {cp}")
                self.error_404_list.append(pd.DataFrame([{'CP': cp}]))

            else:
                print(f"Erro: {response.status_code} para o código postal {cp}")
                self.other_error_list.append(pd.DataFrame([{'CP': cp}]))

    def save_results(self):
        df_collected = pd.concat(self.success_list, ignore_index=True) if self.success_list else pd.DataFrame()
        df_errors_404 = pd.concat(self.error_404_list, ignore_index=True) if self.error_404_list else pd.DataFrame()
        

        # Ajustar colunas para compatibilidade com as tabelas
        if not df_errors_404.empty:
            df_errors_404 = df_errors_404.rename(columns={'CP': 'codigo_postal_clean'})
            df_errors_404['codigo_postal_baseline'] = None 
            
        if not df_collected.empty:
            df_collected = df_collected.rename(columns={'CP': 'codigo_postal_baseline','Concelho':'concelho','Distrito':'distrito'})
            df_collected['codigo_postal_clean'] = None 
            #df_collected['codigo_postal_baseline'] = None
            df_collected = df_collected[['codigo_postal_clean','codigo_postal_baseline','concelho', 'distrito']]
            
        # Salvar os resultados no banco de dados
        self.insert_into_db(df_collected, "codigo_postal_base")
        self.insert_into_db(df_errors_404, "codigo_postal_erro_404")

    def insert_into_db(self, df, table_name):
        """Insere um DataFrame na tabela SQL especificada."""
        if not df.empty:
            try:
                df.to_sql(table_name, self.db_engine, if_exists='replace', index=False)
                print(f"Dados inseridos com sucesso na tabela {table_name}")
            except Exception as e:
                print(f"Erro ao inserir dados na tabela {table_name}: {e}")


    def run(self):
        """Executa o processo completo."""
        self.load_and_prepare_data()
        self.process_responses()
        self.save_results()


# Uso
if __name__ == "__main__":
    processor = ProcessadorCodigoPostal(
        csv_name="cp7_data.csv",
        env_file=".env"
    )
    processor.run()
