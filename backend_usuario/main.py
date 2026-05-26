from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from database import obter_conexao

app = FastAPI(title="API Zona Azul - Usuário")

class veiculoNovo(BaseModel):
    placa: str
    modelo: str
    ano: int

# Handler de inserção de veículo
@app.post("/usuarios/{id_usuario}/veiculos")
def adicionar_veiculo_na_garagem(id_usuario: int, veiculo: VeiculoNovo, conexao = Depends(obter_conexao)):
    cursor = conexao.cursor()
    
    try:
        # Inserção do carro no catálogo geral (ignora se a placa já existir)
        query_carro = """
            INSERT INTO veiculos (placa, modelo, ano) 
            VALUES (%s, %s, %s) ON CONFLICT (placa) DO NOTHING;
        """
        cursor.execute(query_carro, (veiculo.placa, veiculo.modelo, veiculo.ano))
        
        # Relaciona veículo e usuário na tabela ponte
        query_vinculo = """
            INSERT INTO usuario_veiculo (id_usuario, placa) 
            VALUES (%s, %s);
        """
        cursor.execute(query_vinculo, (id_usuario, veiculo.placa))
        
        # Commit no banco
        conexao.commit()
        return {"mensagem": f"Veículo {veiculo.placa} adicionado com sucesso!"}
        
    except Exception as e:
        conexao.rollback() # Desfaz tudo se der erro
        raise HTTPException(status_code=400, detail=f"Erro ao vincular veículo: {e}")
        
    finally:
        cursor.close()

# Handler de listagem dos veículos do usuário
@app.get("/usuarios/{id_usuario}/veiculos")
def listar_veiculos_do_usuario(id_usuario: int, conexao = Depends(obter_conexao)):
    cursor = conexao.cursor()
    
    # Consulta para buscar os veículos relacionados ao usuário
    query = """
        SELECT v.placa, v.modelo, v.ano 
        FROM veiculos v
        JOIN usuario_veiculo uv ON v.placa = uv.placa
        WHERE uv.id_usuario = %s;
    """
    cursor.execute(query, (id_usuario,))
    veiculos_bd = cursor.fetchall()
    cursor.close()
    
    # Formata o resultado para JSON
    resultado = []
    for veiculo in veiculos_bd:
        resultado.append({
            "placa": veiculo[0],
            "modelo": veiculo[1],
            "ano": veiculo[2]
        })
        
    return {"garagem": resultado}

# # lista os setores disponíveis no banco de dados
# @app.get("/setores")
# def listar_setores(conexao = Depends(obter_conexao)):
#     cursor = conexao.cursor()
    
#     # Faz a busca real no PostgreSQL
#     cursor.execute("SELECT id_setor, nome_setor FROM setores;")
#     setores_bd = cursor.fetchall()
    
#     cursor.close()
    
#     # Formata o resultado para JSON
#     resultado = []
#     for setor in setores_bd:
#         resultado.append({
#             "id": setor[0],
#             "nome": setor[1]
#         })
        
#     return {"setores": resultado}

# @app.get("/carros")
# def listar_carros(conexao = Depends(obter_conexao)):
#     cursor = conexao.cursor()
    
#     # Faz a busca real no PostgreSQL
#     cursor.execute("SELECT id_carro, placa, modelo, ano FROM carros;")
#     carros_bd = cursor.fetchall()
    
#     cursor.close()
    
#     # Formata o resultado para JSON
#     resultado = []
#     for carro in carros_bd:
#         resultado.append({
#             "id": carro[0],
#             "placa": carro[1],
#             "modelo": carro[2],
#             "ano": carro[3]
#         })
        
#     return {"carros": resultado}

# @app.get("/usuario_veiculos")
# def listar_usuario_veiculos(conexao = Depends(obter_conexao)):
#     cursor = conexao.cursor()
    
#     # Faz a busca real no PostgreSQL
#     cursor.execute("""
#         SELECT placa, id_usuario FROM usuario_veiculo GROUP BY id_usuario;
#     """)
#     usuario_veiculos_bd = cursor.fetchall()
    
#     cursor.close()
    
#     # Formata o resultado para JSON
#     resultado = []
#     for uv in usuario_veiculos_bd:
#         resultado.append({
#             "placa": uv[0],
#             "id_usuario": uv[1]
#         })
        
#     return {"usuario_veiculos": resultado}