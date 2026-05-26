import os
import psycopg2
from dotenv import load_dotenv

# Credenciais
load_dotenv(dotenv_path='./.env')

# Função de Conexão com Injeção de Dependência
def obter_conexao():
    conexao = None
    try:
        conexao = psycopg2.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME')
        )
        # Entrega a conexão temporariamente, responsável pela injeção de dependência.
        yield conexao
        
    except psycopg2.Error as e:
        print(f"Erro grave ao conectar ao banco: {e}")
        
    finally:
        # Encerra a conexão estabelecida
        if conexao is not None:
            conexao.close()