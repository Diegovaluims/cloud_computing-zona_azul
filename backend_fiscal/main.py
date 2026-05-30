from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import database_connect

app = FastAPI(title="API Zona Azul - Rascunho Infraestrutura Fiscal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# Rota para buscar reserva por placa
# =====================================================================

@app.get("/fiscalizacao/{placa}")
def fiscalizar_veiculo(placa: str, conexao = Depends(database_connect.obter_conexao)):
    try:
        cursor = conexao.cursor()
        
        # Query simplificada: Busca apenas se o veículo tem uma reserva registrada
        # Como você adicionou 'setores', podemos até trazer o nome do setor se quiser!
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
        raise HTTPException(status_code=400, detail=f"Erro ao processar consulta: {e}")