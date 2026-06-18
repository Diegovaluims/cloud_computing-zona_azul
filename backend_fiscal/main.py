"""
Backend Fiscal - Microsserviço de Validação

Microsserviço enxuto de leitura. Recebe uma placa via URL e retorna
se o veículo está REGULAR (reserva ativa) ou IRREGULAR (sem reserva).

Porta padrão: 8001 | Documentação: http://localhost:8001/docs
"""
import os
from fastapi import FastAPI, Depends, HTTPException, Header, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db.database_connect import obter_conexao
from db.auth import hash_senha, verificar_senha, criar_token, exigir_role
import psycopg2
import psycopg2.errors

app = FastAPI(title="API Zona Azul - Rascunho Infraestrutura Fiscal")

# CORS liberado para origens específicas
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MultaRequest(BaseModel):
    placa: str
    motivo: str
    valor: float = 50.00

# =====================================================================
# Rota: fiscalizar veículo
# =====================================================================

@app.get("/fiscalizacao/{placa}")
def fiscalizar_veiculo(placa: str, conexao = Depends(obter_conexao), auth = Depends(exigir_role("fiscal"))):
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

        # busca existência de reserva ativa (tempo válido)
        query = """
            SELECT expira_em
            FROM reservas r
            JOIN veiculos v ON r.id_veiculo = v.id_veiculo
            WHERE v.placa = %s AND r.status = 'ATIVA' AND r.expira_em > NOW()
            ORDER BY r.expira_em DESC
            LIMIT 1;
        """
        cursor.execute(query, (placa,))
        reserva_ativa = cursor.fetchone()
        
        # se não há ativa, verificar se há vencida
        if not reserva_ativa:
            query_vencida = """
                SELECT expira_em
                FROM reservas r
                JOIN veiculos v ON r.id_veiculo = v.id_veiculo
                WHERE v.placa = %s
                ORDER BY r.expira_em DESC
                LIMIT 1;
            """
            cursor.execute(query_vencida, (placa,))
            reserva_vencida = cursor.fetchone()
        
        cursor.close()

        if reserva_ativa:
            return {
                "status": "REGULAR",
                "detalhes": f"Veículo com placa {placa} possui reserva válida até {reserva_ativa[0]}."
            }
            
        if reserva_vencida:
            return {
                "status": "IRREGULAR",
                "detalhes": f"Reserva expirada em {reserva_vencida[0]}.",
                "motivo_multa": "RESERVA_EXPIRADA"
            }

        return {
            "status": "IRREGULAR",
            "detalhes": "Nenhuma reserva encontrada para esta placa.",
            "motivo_multa": "SEM_RESERVA"
        }

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail="Erro interno ao processar consulta.")

# =====================================================================
# Rota: emitir multa
# =====================================================================
@app.post("/multas", status_code=201)
def emitir_multa(dados: MultaRequest, conexao = Depends(obter_conexao), auth = Depends(exigir_role("fiscal"))):
    id_fiscal = int(auth["sub"])
    cursor = conexao.cursor()
    try:
        # Verificar se placa existe
        cursor.execute("SELECT id_veiculo FROM veiculos WHERE placa = %s;", (dados.placa,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Placa não encontrada no sistema.")

        cursor.execute("""
            INSERT INTO multas (id_fiscal, placa, motivo, valor)
            VALUES (%s, %s, %s, %s) RETURNING id_multa;
        """, (id_fiscal, dados.placa, dados.motivo, dados.valor))
        id_multa = cursor.fetchone()[0]
        
        conexao.commit()
        return {"mensagem": "Multa emitida com sucesso!", "id_multa": id_multa}
    except Exception as e:
        conexao.rollback()
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()