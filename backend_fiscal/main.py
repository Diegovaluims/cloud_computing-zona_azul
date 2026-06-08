"""
Backend Fiscal - Microsserviço de Validação

Microsserviço enxuto de leitura. Recebe uma placa via URL e retorna
se o veículo está REGULAR (reserva ativa) ou IRREGULAR (sem reserva).

Porta padrão: 8001 | Documentação: http://localhost:8001/docs
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from db.database_connect import obter_conexao

app = FastAPI(title="API Zona Azul - Rascunho Infraestrutura Fiscal")

# CORS liberado para qualquer origem (*) — temporário, a ser restrito quando o Frontend for acoplado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# Rota: fiscalizar veículo
# =====================================================================

@app.get("/fiscalizacao/{placa}")
def fiscalizar_veiculo(placa: str, conexao = Depends(obter_conexao)):
    """
    Verifica se um veículo possui reserva ativa no sistema.
    Parâmetro de URL: placa (VARCHAR(50)).
    Retorna: {"status": "REGULAR"} se houver reserva, ou {"status": "IRREGULAR"} caso contrário.
    """
    try:
        # Validação básica do formato da placa
        placa = placa.strip().upper()
        if not placa:
            raise HTTPException(status_code=400, detail="Placa não pode ser vazia.")

        cursor = conexao.cursor()

        # busca existência de reserva — sem retornar dados desnecessários
        query = """
            SELECT 1
            FROM reservas r
            JOIN veiculos v ON r.id_veiculo = v.id_veiculo
            WHERE v.placa = %s
            LIMIT 1;
        """
        cursor.execute(query, (placa,))
        reserva = cursor.fetchone()
        cursor.close()

        if reserva:
            return {
                "status": "REGULAR",
                "detalhes": f"Veículo com placa {placa} possui reserva registrada."
            }

        return {
            "status": "IRREGULAR",
            "detalhes": "Nenhuma reserva encontrada para esta placa."
        }

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail="Erro interno ao processar consulta.")