from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List
from database import obter_conexao
from schemas.veiculos_schema import VeiculoNovo, VeiculoResponse
from repositories.veiculos_repository import VeiculoRepository

router = APIRouter(prefix="/usuarios", tags=["Veículos"])

# Simulação de Autenticação JWT
# Isso previne o ataque "BOLA" (Broken Object Level Authorization).
# Sem isso, qualquer pessoa com um ID alteraria os dados de outro usuário 
# apenas mudando o número na URL. Na vida real, extrai-se o ID de um JWT Token.
def verificar_identidade(id_usuario: int, x_user_id: int = Header(..., description="ID do usuário autenticado (Simulação de Token JWT)")):
    """
    Middleware/Dependência para garantir que o usuário logado (x_user_id) 
    seja o mesmo que o requisitado (id_usuario) na URL.
    """
    if id_usuario != x_user_id:
        raise HTTPException(status_code=403, detail="Acesso negado. Você só pode gerenciar a sua própria garagem.")

@router.post("/{id_usuario}/veiculos")

def adicionar_veiculo_na_garagem(
    id_usuario: int, 
    veiculo: VeiculoNovo, 
    conexao = Depends(obter_conexao),
    _=Depends(verificar_identidade) # Injeta a verificação de segurança antes de rodar a rota
):
    """
    Adiciona um novo veículo associado à garagem de um usuário específico.
    """
    # Inicialização de Cursor e Repositório
    cursor = conexao.cursor()
    repo = VeiculoRepository(cursor)
    try:
        # Inserção de Dados
        repo.inserir_veiculo_e_vincular(id_usuario, veiculo.placa, veiculo.modelo, veiculo.ano)
        conexao.commit()
        return {"mensagem": f"Veículo {veiculo.placa} adicionado com sucesso!"}
    except Exception as e:
        # Tratamento de Exceções
        conexao.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao vincular veículo: {e}")
    finally:
        # Encerramento do Cursor
        cursor.close()

@router.get("/{id_usuario}/veiculos", response_model=List[VeiculoResponse])
def listar_veiculos_do_usuario(
    id_usuario: int, 
    conexao = Depends(obter_conexao),
    _=Depends(verificar_identidade)
):
    """
    Retorna uma lista de veículos cadastrados e vinculados ao usuário informado.
    """
    # Inicialização de Cursor e Repositório
    cursor = conexao.cursor()
    repo = VeiculoRepository(cursor)
    try:
        # Consulta no Banco de Dados
        veiculos_bd = repo.listar_por_usuario(id_usuario)
        
        # Mapeamento para Modelo Pydantic
        resultado = []
        for v in veiculos_bd:
            resultado.append(VeiculoResponse(placa=v[0], modelo=v[1], ano=v[2]))
            
        return resultado
    finally:
        # Encerramento do Cursor
        cursor.close()
