import os
import psycopg2
from dotenv import load_dotenv

# Carregamento de Variáveis de Ambiente
load_dotenv(dotenv_path='./.env')

def inserir_mocks():
    """
    Função responsável por inserir dados iniciais fictícios (mocks) no banco de dados,
    como setores e um usuário padrão para testes.
    """
    # Configurações de Conexão
    db_config = {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'database': os.getenv('DB_NAME')
    }

    # Conexão com o Banco de Dados
    try:
        conexao = psycopg2.connect(**db_config)
        cursor = conexao.cursor()

        # Inserção de Setores
        cursor.execute("INSERT INTO setores (nome_setor) VALUES ('Centro'), ('Bairro Alto'), ('Shopping') ON CONFLICT DO NOTHING;")
        
        # Inserção de Usuário com Saldo Fixo
        cursor.execute("""
            INSERT INTO usuarios (cpf, nome, email, telefone, saldo) 
            VALUES ('12345678901', 'João da Silva', 'joao@email.com', '11999999999', 50.00) 
            ON CONFLICT (cpf) DO NOTHING;
        """)
        
        # Efetivação da Transação
        conexao.commit()
        print("Dados mockados inseridos com sucesso!")

    except Exception as e:
        print(f"Erro ao inserir mocks: {e}")
    finally:
        # Fechamento de Conexões
        if 'conexao' in locals() and conexao:
            cursor.close()
            conexao.close()

if __name__ == "__main__":
    inserir_mocks()
