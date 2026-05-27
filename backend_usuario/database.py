import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
from fastapi import HTTPException

# Carregamento de Credenciais
load_dotenv(dotenv_path='./.env')

# Pool de Conexões
# Backlog de conexões prontas na memória
try:
    connection_pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=20,
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME')
    )
    if connection_pool:
        print("Connection pool criado com sucesso no backend_usuario")
except Exception as e:
    print(f"Erro grave ao inicializar pool de conexões: {e}")
    connection_pool = None

# Função de Conexão com Injeção de Dependência
def obter_conexao():
    """
    Fornece uma conexão com o banco de dados obtida a partir do Pool de Conexões.
    Utiliza um gerador (yield) para garantir que a conexão seja devolvida ao Pool
    após o uso, independentemente de sucesso ou falha na requisição.
    """
    if not connection_pool:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível no momento.")
        
    conexao = None
    try:
        # Pega uma conexão emprestada do Pool (MUITO mais rápido)
        conexao = connection_pool.getconn()
        yield conexao
        
    except psycopg2.Error as e:
        print(f"Erro durante uso da conexão: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no processamento com o banco.")
        
    finally:
        # Devolve a conexão ao Pool para ser reutilizada
        if conexao is not None:
            connection_pool.putconn(conexao)
