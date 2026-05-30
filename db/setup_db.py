"""
Script Utilitário de Setup do Banco de Dados

Usado para inicializar as tabelas manualmente via linha de comando,
fora do ambiente Docker. Lê o schema.sql e executa no banco configurado
pelas variáveis de ambiente do arquivo .env.

Uso: python db/setup_db.py
"""
import os
import psycopg2
from psycopg2 import Error
from dotenv import load_dotenv

# carrega variáveis de ambiente do .env
load_dotenv(dotenv_path='./.env')

def criar_tabelas():
    """
    Função responsável por conectar ao banco de dados e criar as tabelas
    iniciais utilizando o script 'schema.sql'.
    """
    db_config = {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'database': os.getenv('DB_NAME')
    }

    try:
        conexao = psycopg2.connect(**db_config)
        cursor = conexao.cursor()

        # leitura e execução do schema SQL
        with open('./db/schema.sql', 'r') as arquivo_sql:
            comandos_sql = arquivo_sql.read()

        cursor.execute(comandos_sql)
        conexao.commit()
        print("Tabelas criadas com sucesso no banco de dados!")

    except Error as e:
        print(f"Erro ao conectar ou executar no PostgreSQL: {e}")
    finally:
        if 'conexao' in locals() and conexao:
            cursor.close()
            conexao.close()
            print("Conexão encerrada.")

# Ponto de entrada do script — só executa se chamado diretamente, não se importado como módulo
if __name__ == "__main__":
    criar_tabelas()