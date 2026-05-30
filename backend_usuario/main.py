"""
Backend do Usuário - Microsserviço de Gerenciamento

Responsável pelo cadastro de usuários, veículos,
vinculação usuário-veículo (garagem) e emissão de reservas de estacionamento.

Porta padrão: 8000 | Documentação: http://localhost:8000/docs
"""
from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import database_connect

# =====================================================================
# INICIALIZAÇÃO
# =====================================================================
app = FastAPI(title="API Zona Azul - Rascunho Infraestrutura Usuario")

# CORS liberado para qualquer origem (*) — temporário, a ser restrito quando o Frontend for acoplado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# Rota: criar usuário
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
    conexao = Depends(database_connect.obter_conexao)
):
    """
    Cria um novo usuário no sistema.
    Parâmetros: nome (str), email (str).
    Retorna: mensagem de sucesso e o id_usuario gerado pelo banco.
    """
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
# Rota: listar usuários
# =====================================================================
@app.get("/usuarios")
def listar_usuarios(conexao = Depends(database_connect.obter_conexao)):
    """
    Retorna a lista completa de usuários cadastrados no sistema.
    """
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
# Rota: remover usuário
# =====================================================================
@app.delete("/usuarios/{id_usuario}")
def remover_usuario(id_usuario: int, conexao = Depends(database_connect.obter_conexao)):
    """
    Remove um usuário e todos os seus vínculos do sistema.
    A deleção respeita a ordem das constraints de Foreign Key:
    reservas → vínculos de garagem (usuario_veiculo) → usuário.
    """
    cursor = conexao.cursor()
    try:
        # ordem de deleção respeita as FKs: reservas → garagem → usuário
        cursor.execute("DELETE FROM reservas WHERE id_usuario = %s;", (id_usuario,))
        cursor.execute("DELETE FROM usuario_veiculo WHERE id_usuario = %s;", (id_usuario,))
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
# Rota: adicionar veículo à garagem
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
    conexao = Depends(database_connect.obter_conexao)
):
    """
    Cadastra um veículo e o vincula à garagem do usuário.
    Parâmetros: placa (VARCHAR(50)), modelo (str), ano (int).
    ON CONFLICT (placa) DO NOTHING — evita duplicatas se a placa já existir.
    """
    cursor = conexao.cursor()
    try:
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
        conexao.rollback()
        raise HTTPException(status_code=400, detail=f"Campo ausente no JSON: {e}")
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao vincular veículo: {e}")
    finally:
        cursor.close()

# =====================================================================
# Rota: listar veículos
# =====================================================================
@app.get("/veiculos")
def listar_veiculos(conexao = Depends(database_connect.obter_conexao)):
    """
    Retorna todos os veículos cadastrados no sistema.
    """
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
# Rota: listar veículos do usuário
# =====================================================================
@app.get("/usuarios/{id_usuario}/veiculos")
def listar_veiculos_do_usuario(id_usuario: int, conexao = Depends(database_connect.obter_conexao)):
    """
    Retorna os veículos da garagem de um usuário específico.
    """
    cursor = conexao.cursor()
    try:
        cursor.execute("""
            SELECT v.id_veiculo, v.placa, v.modelo, v.ano 
            FROM veiculos v
            JOIN usuario_veiculo uv ON v.placa = uv.placa
            WHERE uv.id_usuario = %s;
        """, (id_usuario,))
        
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
        raise HTTPException(status_code=400, detail=f"Erro ao buscar veículos do usuário: {e}")
        
    finally:
        cursor.close()

# =====================================================================
# Rota: remover veículo
# =====================================================================
@app.delete("/veiculos/{id_veiculo}")
def remover_veiculo(id_veiculo: int, conexao = Depends(database_connect.obter_conexao)):
    """
    Remove um veículo e todo o seu histórico do sistema.
    A deleção respeita a ordem das constraints de Foreign Key:
    reservas → vínculos de garagem (usuario_veiculo) → veículo.
    """
    cursor = conexao.cursor()
    try:
        # busca a placa — necessária para limpar usuario_veiculo (FK por placa, não por id)
        cursor.execute("SELECT placa FROM veiculos WHERE id_veiculo = %s;", (id_veiculo,))
        resultado = cursor.fetchone()
        
        if not resultado:
            raise HTTPException(status_code=404, detail="Veículo não encontrado.")
        placa = resultado[0]

        # ordem de deleção respeita as FKs: reservas → garagem → veículo
        cursor.execute("DELETE FROM reservas WHERE id_veiculo = %s;", (id_veiculo,))
        cursor.execute("DELETE FROM usuario_veiculo WHERE placa = %s;", (placa,))
        cursor.execute("DELETE FROM veiculos WHERE id_veiculo = %s;", (id_veiculo,))
        
        conexao.commit()
        return {"mensagem": f"Veículo de placa {placa} e todo o seu histórico foram removidos com sucesso!"}
        
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()

# =====================================================================
# Rota: emitir reserva
# =====================================================================
@app.post("/reservas", status_code=201)
def comprar_reserva(
    reserva: dict = Body(
        ..., 
        example={
            "id_usuario": 1,
            "placa": "ABC-1234",
        }
    ), 
    conexao = Depends(database_connect.obter_conexao)
):
    """
    Emite uma reserva de estacionamento para um veículo da garagem do usuário.
    Valida se o veículo pertence à garagem do usuário antes de inserir.
    Parâmetros: id_usuario (int), placa (VARCHAR(50)).
    Retorna: mensagem de sucesso e o id_reserva gerado.
    """
    cursor = conexao.cursor()
    try:
        # valida se a placa pertence à garagem do usuário antes de inserir
        cursor.execute("""
            SELECT v.id_veiculo FROM veiculos v
            JOIN usuario_veiculo uv ON v.placa = uv.placa
            WHERE uv.id_usuario = %s AND v.placa = %s;
        """, (reserva["id_usuario"], reserva["placa"]))
        
        resultado = cursor.fetchone()
        if not resultado:
            raise HTTPException(status_code=404, detail="Veículo não encontrado na garagem.")
        id_veiculo = resultado[0]
        cursor.execute("""
            INSERT INTO reservas (id_usuario, id_veiculo)
            VALUES (%s, %s) RETURNING id_reserva;
        """, (reserva["id_usuario"], id_veiculo))
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
# Rota: listar reservas
# =====================================================================
@app.get("/reservas")
def listar_reservas(conexao = Depends(database_connect.obter_conexao)):
    """
    Retorna todas as reservas registradas no sistema.
    """
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT id_reserva, id_usuario, id_veiculo FROM reservas")
        reservas_bd = cursor.fetchall()
        
        return [
            {
                "id_reserva": r[0], 
                "id_usuario": r[1], 
                "id_veiculo": r[2]
            } for r in reservas_bd
        ]
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()

# =====================================================================
# Rota: remover reserva
# =====================================================================
@app.delete("/reservas/{id_reserva}")
def remover_reserva(id_reserva: int, conexao = Depends(database_connect.obter_conexao)):
    """
    Remove uma reserva pelo seu ID.
    Retorna 404 se a reserva não for encontrada.
    """
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