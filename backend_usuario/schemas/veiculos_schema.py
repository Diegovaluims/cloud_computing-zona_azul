from pydantic import BaseModel

# 1. Schema para Criação de Veículo
class VeiculoNovo(BaseModel):
    """
    Representa o payload recebido pelo endpoint de cadastro de veículos.
    """
    placa: str
    modelo: str
    ano: int

# 2. Schema para Resposta de Veículo
class VeiculoResponse(BaseModel):
    """
    Representa o formato de resposta ao listar os veículos do usuário.
    """
    placa: str
    modelo: str
    ano: int
