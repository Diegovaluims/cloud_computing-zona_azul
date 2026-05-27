from pydantic import BaseModel
from datetime import datetime

# Schema de Entrada (Criação)
class ReservaCreate(BaseModel):
    """
    Representa os dados necessários enviados pelo cliente para criar uma reserva.
    """
    id_usuario: int
    placa: str
    id_setor: int
    duracao_minutos: int

# Schema de Saída (Resposta)
class ReservaResponse(BaseModel):
    """
    Representa os dados retornados ao cliente após a confirmação da reserva.
    """
    mensagem: str
    id_reserva: int
    valor_pago: float
    hora_inicio: datetime
    hora_fim: datetime
