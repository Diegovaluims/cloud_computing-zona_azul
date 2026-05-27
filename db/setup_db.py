import os
import psycopg2
from psycopg2 import Error
from dotenv import load_dotenv

# Carregamento de Variáveis de Ambiente
load_dotenv(dotenv_path='./.env')

def criar_tabelas():
    """
    Função responsável por conectar ao banco de dados e criar as tabelas
    iniciais utilizando o script 'schema.sql'.
    """
    # Configurações de Conexão
    db_config = {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'database': os.getenv('DB_NAME')
    }

    # Conexão e Execução de Comandos SQL
    try:
        conexao = psycopg2.connect(**db_config)
        cursor = conexao.cursor()

        # Leitura do Script SQL
        with open('./db/schema.sql', 'r') as arquivo_sql:
            comandos_sql = arquivo_sql.read()

        # Execução e Persistência
        cursor.execute(comandos_sql)
        
        # Confirma a transação (Commit)
        conexao.commit()
        print("Tabelas criadas com sucesso no banco de dados!")

    except Error as e:
        print(f"Erro ao conectar ou executar no PostgreSQL: {e}")
    finally:
        # Encerramento Seguro da Conexão
        if 'conexao' in locals() and conexao:
            cursor.close()
            conexao.close()
            print("Conexão encerrada.")

if __name__ == "__main__":
    criar_tabelas()