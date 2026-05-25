import os
import psycopg2
from psycopg2 import Error
from dotenv import load_dotenv

load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env

def criar_tabelas():
    # Agora buscamos as configurações de forma segura
    db_config = {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'database': os.getenv('DB_NAME')
    }

    try:
        # 1. Conecta ao banco de dados
        conexao = psycopg2.connect(**db_config)
        print(conexao)
        cursor = conexao.cursor()
        print("Conexão com PostgreSQL bem-sucedida!")

        # 2. Lê o arquivo SQL
        with open('schema.sql', 'r') as arquivo_sql:
            comandos_sql = arquivo_sql.read()

        # 3. Executa os comandos
        cursor.execute(comandos_sql)
        
        # 4. Confirma a transação (Commit)
        conexao.commit()
        print("Tabelas criadas com sucesso no banco de dados!")

    except Error as e:
        print(f"Erro ao conectar ou executar no PostgreSQL: {e}")
    finally:
        if conexao:
            cursor.close()
            conexao.close()
            print("Conexão encerrada.")

if __name__ == "__main__":
    criar_tabelas()