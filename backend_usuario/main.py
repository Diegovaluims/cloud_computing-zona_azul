from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from backend_usuario.database import obter_conexao

# =====================================================================
# 1. INICIALIZAÇÃO DA APLICAÇÃO FASTAPI
# =====================================================================
app = FastAPI(title="API Zona Azul - Rascunho Infraestrutura")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# Rota para criar usuários #
# =====================================================================
@app.post("/usuarios", status_code=201)
def criar_usuario(
    usuario: dict = Body(
        ...,
        example={
            "nome": "João da Silva",
            "email": "joao@email.com"
        }
    ), 
    conexao = Depends(obter_conexao)
):
    cursor = conexao.cursor()
    try:
        cursor.execute("""
            INSERT INTO usuarios (nome, email) 
            VALUES (%s, %s) RETURNING id_usuario;
        """, (usuario["nome"], usuario["email"]))
        
        id_novo = cursor.fetchone()[0]
        conexao.commit()
        
        return {"mensagem": "Usuário criado com sucesso!", "id_usuario": id_novo}
    except KeyError as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=f"Campo ausente no JSON: {e}")
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar usuário: {e}")
    finally:
        cursor.close()

# =====================================================================
# Rota para listar usuários
# =====================================================================
@app.get("/usuarios")
def listar_usuarios(conexao = Depends(obter_conexao)):
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT id_usuario, nome, email FROM usuarios;")
        usuarios_bd = cursor.fetchall()
        
        return [{"id_usuario": u[0], "nome": u[1], "email": u[2]} for u in usuarios_bd]
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()

# =====================================================================
# Rota para remover usuários
# =====================================================================
@app.delete("/usuarios/{id_usuario}")
def remover_usuario(id_usuario: int, conexao = Depends(obter_conexao)):
    cursor = conexao.cursor()
    try:
        # 1. Apaga as reservas vinculadas a esse usuário para evitar erro de Foreign Key
        cursor.execute("DELETE FROM reservas WHERE id_usuario = %s;", (id_usuario,))
        
        # 2. Apaga o vínculo da garagem do usuário
        cursor.execute("DELETE FROM usuario_veiculo WHERE id_usuario = %s;", (id_usuario,))
        
        # 3. Finalmente, apaga o próprio usuário
        cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s RETURNING id_usuario;", (id_usuario,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
            
        conexao.commit()
        return {"mensagem": f"Usuário {id_usuario} e todos os seus vínculos foram removidos com sucesso!"}
        
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()

# =====================================================================
# Rota para adicionar veículos na garagem do usuário 
# =====================================================================
@app.post("/usuarios/{id_usuario}/veiculos")
def adicionar_veiculo_na_garagem(
    id_usuario: int, 
    veiculo: dict = Body(
        ...,
        example={
            "placa": "ABC-1234",
            "modelo": "Fusca",
            "ano": 1978
        }
    ), 
    conexao = Depends(obter_conexao)
):
    cursor = conexao.cursor()
    try:
        # Acessa os dados direto do JSON cru (ex: veiculo["placa"])
        cursor.execute(
            "INSERT INTO veiculos (placa, modelo, ano) VALUES (%s, %s, %s) ON CONFLICT (placa) DO NOTHING;", 
            (veiculo["placa"], veiculo["modelo"], veiculo["ano"])
        )
        cursor.execute(
            "INSERT INTO usuario_veiculo (id_usuario, placa) VALUES (%s, %s);", 
            (id_usuario, veiculo["placa"])
        )
        conexao.commit()
        return {"mensagem": f"Veículo {veiculo['placa']} adicionado com sucesso!"}
    except KeyError as e:
        # Se você esquecer de mandar algum campo no JSON, ele avisa aqui
        conexao.rollback()
        raise HTTPException(status_code=400, detail=f"Campo ausente no JSON: {e}")
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao vincular veículo: {e}")
    finally:
        cursor.close()

# =====================================================================
# Rota para listar veículos
# =====================================================================
@app.get("/veiculos")
def listar_veiculos(conexao = Depends(obter_conexao)):
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT id_veiculo, placa, modelo, ano FROM veiculos;")
        veiculos_bd = cursor.fetchall()
        
        return [
            {
                "id_veiculo": v[0], 
                "placa": v[1], 
                "modelo": v[2], 
                "ano": v[3]
            } for v in veiculos_bd
        ]
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()

# =====================================================================
# Rota para listar veículos do usuário
# =====================================================================
@app.get("/usuarios/{id_usuario}/veiculos")
def listar_veiculos_do_usuario(id_usuario: int, conexao = Depends(obter_conexao)):
    cursor = conexao.cursor()
    try:
        # Cruza as tabelas para pegar só os carros da garagem do usuário específico
        cursor.execute("""
            SELECT v.id_veiculo, v.placa, v.modelo, v.ano 
            FROM veiculos v
            JOIN usuario_veiculo uv ON v.placa = uv.placa
            WHERE uv.id_usuario = %s;
        """, (id_usuario,))
        
        veiculos_bd = cursor.fetchall()
        
        # Monta a lista de dicionários na mão
        return [
            {
                "id_veiculo": v[0],
                "placa": v[1], 
                "modelo": v[2], 
                "ano": v[3]
            } for v in veiculos_bd
        ]
        
    except Exception as e:
        # O airbag ativado caso algo dê errado
        conexao.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao buscar veículos do usuário: {e}")
        
    finally:
        # A faxina
        cursor.close()

# =====================================================================
# Rota para remover veículos
# =====================================================================
@app.delete("/veiculos/{id_veiculo}")
def remover_veiculo(id_veiculo: int, conexao = Depends(obter_conexao)):
    cursor = conexao.cursor()
    try:
        # 1. Pegamos a placa do veículo, pois precisamos dela para limpar a tabela 'usuario_veiculo'
        cursor.execute("SELECT placa FROM veiculos WHERE id_veiculo = %s;", (id_veiculo,))
        resultado = cursor.fetchone()
        
        if not resultado:
            raise HTTPException(status_code=404, detail="Veículo não encontrado.")
        placa = resultado[0]

        # 2. Apagamos todas as reservas atreladas a este veículo
        cursor.execute("DELETE FROM reservas WHERE id_veiculo = %s;", (id_veiculo,))
        
        # 3. Removemos o vínculo do veículo com qualquer usuário (usando a placa)
        cursor.execute("DELETE FROM usuario_veiculo WHERE placa = %s;", (placa,))
        
        # 4. Finalmente, apagamos o veículo da tabela principal
        cursor.execute("DELETE FROM veiculos WHERE id_veiculo = %s;", (id_veiculo,))
        
        conexao.commit()
        return {"mensagem": f"Veículo de placa {placa} e todo o seu histórico foram removidos com sucesso!"}
        
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()

# =====================================================================
# Rota para comprar reserva 
# =====================================================================
@app.post("/reservas", status_code=201)
def comprar_reserva(
    reserva: dict = Body(
        ..., 
        example={
            "id_usuario": 1,
            "placa": "ABC-1234",
            "id_setor": 5
        }
    ), 
    conexao = Depends(obter_conexao)
):
    cursor = conexao.cursor()
    try:
        # Pega o ID do carro e confirma se é da garagem
        cursor.execute("""
            SELECT v.id_veiculo FROM veiculos v
            JOIN usuario_veiculo uv ON v.placa = uv.placa
            WHERE uv.id_usuario = %s AND v.placa = %s;
        """, (reserva["id_usuario"], reserva["placa"]))
        
        resultado = cursor.fetchone()
        if not resultado:
            raise HTTPException(status_code=404, detail="Veículo não encontrado na garagem.")
        id_veiculo = resultado[0]

        # Registra a vaga direto, sem checar saldo
        cursor.execute("""
            INSERT INTO reservas (id_usuario, id_veiculo, id_setor)
            VALUES (%s, %s, %s) RETURNING id_reserva;
        """, (reserva["id_usuario"], id_veiculo, reserva["id_setor"]))
        id_reserva = cursor.fetchone()[0]

        conexao.commit()
        return {"mensagem": "Reserva efetuada com sucesso!", "id_reserva": id_reserva}
        
    except KeyError as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=f"Campo ausente no JSON: {e}")
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()

# =====================================================================
# Rota para listar reservas
# =====================================================================
@app.get("/reservas")
def listar_reservas(conexao = Depends(obter_conexao)):
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT id_reserva, id_usuario, id_veiculo, id_setor FROM reservas;")
        reservas_bd = cursor.fetchall()
        
        return [
            {
                "id_reserva": r[0], 
                "id_usuario": r[1], 
                "id_veiculo": r[2], 
                "id_setor": r[3]
            } for r in reservas_bd
        ]
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()

# =====================================================================
# Rota para remover reservas
# =====================================================================
@app.delete("/reservas/{id_reserva}")
def remover_reserva(id_reserva: int, conexao = Depends(obter_conexao)):
    cursor = conexao.cursor()
    try:
        cursor.execute("DELETE FROM reservas WHERE id_reserva = %s RETURNING id_reserva;", (id_reserva,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Reserva não encontrada.")
            
        conexao.commit()
        return {"mensagem": f"Reserva {id_reserva} removida com sucesso!"}
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()