"""
Backend do Usuário - Microsserviço de Gerenciamento

Responsável pelo cadastro de usuários, veículos,
vinculação usuário-veículo (garagem) e emissão de reservas de estacionamento.

Porta padrão: 8000 | Documentação: http://localhost:8000/docs
"""
from fastapi import FastAPI, Depends, HTTPException, Body, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db.database_connect import obter_conexao
from db.auth import hash_senha, verificar_senha, criar_token, exigir_role, obter_dados_token
import psycopg2
import psycopg2.errors
import os

# =====================================================================
# INICIALIZAÇÃO
# =====================================================================
app = FastAPI(title="API Zona Azul - Rascunho Infraestrutura Usuario")

# CORS liberado para origens específicas
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ReservaRequest(BaseModel):
    id_usuario: int
    placa: str
    duracao_horas: int = 1

class RecargaRequest(BaseModel):
    valor: float

class PerfilUpdateRequest(BaseModel):
    nome: str = None
    email: str = None

class SenhaUpdateRequest(BaseModel):
    senha_atual: str
    nova_senha: str


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
    conexao = Depends(obter_conexao),
    auth = Depends(exigir_role("usuario"))
):
    if str(id_usuario) != auth["sub"]:
        raise HTTPException(status_code=403, detail="Você só pode modificar a sua própria garagem.")
    """
    Cadastra um veículo e o vincula à garagem do usuário.
    Parâmetros: placa (VARCHAR(50)), modelo (str), ano (int).
    ON CONFLICT (placa) DO NOTHING — evita duplicatas se a placa já existir.
    """
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT 1 FROM usuarios WHERE id_usuario = %s;", (id_usuario,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")

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
    except psycopg2.errors.UniqueViolation:
        conexao.rollback()
        raise HTTPException(status_code=409, detail="Veículo já está na garagem deste usuário.")
    except KeyError as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=f"Campo ausente no JSON: {e}")
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao vincular veículo: {e}")
    finally:
        cursor.close()



# =====================================================================
# Rota: listar veículos do usuário
# =====================================================================
@app.get("/usuarios/{id_usuario}/veiculos")
def listar_veiculos_do_usuario(id_usuario: int, conexao = Depends(obter_conexao), auth = Depends(exigir_role("usuario"))):
    if str(id_usuario) != auth["sub"]:
        raise HTTPException(status_code=403, detail="Você só pode ver a sua própria garagem.")
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
        raise HTTPException(status_code=400, detail=f"Erro ao buscar veículos do usuário: {e}")
        
    finally:
        cursor.close()

# =====================================================================
# Rota: remover veículo
# =====================================================================
@app.delete("/veiculos/{id_veiculo}")
def remover_veiculo(id_veiculo: int, conexao = Depends(obter_conexao), auth = Depends(exigir_role("usuario"))):
    # OBS: Ideal seria validar se o veículo pertence ao usuário autenticado,
    # mas mantendo simples no MVP. Poderíamos fazer um JOIN com usuario_veiculo.
    """
    Remove um veículo e todo o seu histórico do sistema.
    A deleção respeita a ordem das constraints de Foreign Key:
    reservas → vínculos de garagem (usuario_veiculo) → veículo.
    """
    cursor = conexao.cursor()
    try:
        cursor.execute("DELETE FROM veiculos WHERE id_veiculo = %s RETURNING placa;", (id_veiculo,))
        resultado = cursor.fetchone()
        
        if not resultado:
            raise HTTPException(status_code=404, detail="Veículo não encontrado.")
        placa = resultado[0]
        
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
    reserva: ReservaRequest, 
    conexao = Depends(obter_conexao),
    auth = Depends(exigir_role("usuario"))
):
    if str(reserva.id_usuario) != auth["sub"]:
        raise HTTPException(status_code=403, detail="Você não pode comprar reservas para outros usuários.")
        
    if reserva.duracao_horas < 1:
        raise HTTPException(status_code=400, detail="A duração deve ser de pelo menos 1 hora.")

    cursor = conexao.cursor()
    try:
        # Obter o preço por hora
        cursor.execute("SELECT valor FROM configuracao WHERE chave = 'preco_hora';")
        preco_hora = cursor.fetchone()
        preco_hora = float(preco_hora[0]) if preco_hora else 5.00
        
        preco_total = preco_hora * reserva.duracao_horas

        # Verificar saldo
        cursor.execute("SELECT saldo FROM usuarios WHERE id_usuario = %s FOR UPDATE;", (reserva.id_usuario,))
        saldo_atual = cursor.fetchone()
        if not saldo_atual or float(saldo_atual[0]) < preco_total:
            raise HTTPException(status_code=402, detail="Saldo insuficiente.")

        # valida se a placa pertence à garagem do usuário antes de inserir
        cursor.execute("""
            SELECT v.id_veiculo FROM veiculos v
            JOIN usuario_veiculo uv ON v.placa = uv.placa
            WHERE uv.id_usuario = %s AND v.placa = %s
        """, (reserva.id_usuario, reserva.placa))
        
        resultado = cursor.fetchone()
        if not resultado:
            raise HTTPException(status_code=404, detail="Veículo não encontrado na garagem.")
        id_veiculo = resultado[0]
        
        # Debitar saldo
        cursor.execute("""
            UPDATE usuarios SET saldo = saldo - %s WHERE id_usuario = %s;
        """, (preco_total, reserva.id_usuario))

        # Inserir transacao
        cursor.execute("""
            INSERT INTO transacoes (id_usuario, tipo, valor, descricao)
            VALUES (%s, 'DEBITO_RESERVA', %s, 'Reserva de estacionamento');
        """, (reserva.id_usuario, -preco_total))

        # Inserir reserva
        cursor.execute("""
            INSERT INTO reservas (id_usuario, id_veiculo, duracao_horas, preco_total, expira_em)
            VALUES (%s, %s, %s, %s, NOW() + INTERVAL '%s hours') RETURNING id_reserva;
        """, (reserva.id_usuario, id_veiculo, reserva.duracao_horas, preco_total, reserva.duracao_horas))
        id_reserva = cursor.fetchone()[0]

        conexao.commit()
        return {"mensagem": "Reserva efetuada com sucesso!", "id_reserva": id_reserva, "preco_cobrado": preco_total}
        
    except Exception as e:
        conexao.rollback()
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

# =====================================================================
# Rota: listar reservas
# =====================================================================
@app.get("/reservas")
def listar_reservas(conexao = Depends(obter_conexao), auth = Depends(exigir_role("usuario"))):
    """
    Retorna todas as reservas registradas no sistema.
    """
    cursor = conexao.cursor()
    try:
        cursor.execute("""
            SELECT r.id_reserva, r.id_usuario, r.id_veiculo, v.placa 
            FROM reservas r
            JOIN veiculos v ON r.id_veiculo = v.id_veiculo
        """)
        reservas_bd = cursor.fetchall()
        
        return [
            {
                "id_reserva": r[0], 
                "id_usuario": r[1], 
                "id_veiculo": r[2],
                "placa": r[3]
            } for r in reservas_bd
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()

# =====================================================================
# Rota: remover reserva
# =====================================================================
@app.delete("/reservas/{id_reserva}")
def remover_reserva(id_reserva: int, conexao = Depends(obter_conexao), auth = Depends(exigir_role("usuario"))):
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

# =====================================================================
# Rota: carteira (saldo e extrato)
# =====================================================================
@app.get("/carteira")
def obter_carteira(conexao = Depends(obter_conexao), auth = Depends(exigir_role("usuario"))):
    id_usuario = int(auth["sub"])
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT saldo FROM usuarios WHERE id_usuario = %s;", (id_usuario,))
        resultado = cursor.fetchone()
        if not resultado:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        saldo = resultado[0]

        cursor.execute("""
            SELECT id_transacao, tipo, valor, descricao, criado_em 
            FROM transacoes 
            WHERE id_usuario = %s 
            ORDER BY criado_em DESC;
        """, (id_usuario,))
        transacoes_bd = cursor.fetchall()
        transacoes = [
            {
                "id_transacao": t[0],
                "tipo": t[1],
                "valor": float(t[2]),
                "descricao": t[3],
                "criado_em": t[4]
            } for t in transacoes_bd
        ]

        return {"saldo": float(saldo), "transacoes": transacoes}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

# =====================================================================
# Rota: recarga de carteira
# =====================================================================
@app.post("/carteira/recarga")
def recarregar_carteira(
    dados: RecargaRequest, 
    conexao = Depends(obter_conexao), 
    auth = Depends(exigir_role("usuario"))
):
    if dados.valor <= 0:
        raise HTTPException(status_code=400, detail="Valor de recarga deve ser positivo.")
        
    id_usuario = int(auth["sub"])
    cursor = conexao.cursor()
    try:
        # TODO: Integração real com gateway de pagamento entra aqui
        
        cursor.execute("""
            UPDATE usuarios SET saldo = saldo + %s WHERE id_usuario = %s RETURNING saldo;
        """, (dados.valor, id_usuario))
        novo_saldo = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO transacoes (id_usuario, tipo, valor, descricao)
            VALUES (%s, 'RECARGA', %s, 'Recarga via sistema');
        """, (id_usuario, dados.valor))
        
        conexao.commit()
        return {"mensagem": "Recarga efetuada com sucesso", "novo_saldo": float(novo_saldo)}
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

# =====================================================================
# Rotas: Perfil do Usuário
# =====================================================================
@app.get("/perfil")
def obter_perfil(conexao = Depends(obter_conexao), auth = Depends(exigir_role("usuario"))):
    id_usuario = int(auth["sub"])
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT nome, email FROM usuarios WHERE id_usuario = %s;", (id_usuario,))
        resultado = cursor.fetchone()
        if not resultado:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        return {"nome": resultado[0], "email": resultado[1]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.put("/perfil")
def atualizar_perfil(
    dados: PerfilUpdateRequest, 
    conexao = Depends(obter_conexao), 
    auth = Depends(exigir_role("usuario"))
):
    id_usuario = int(auth["sub"])
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT nome, email FROM usuarios WHERE id_usuario = %s;", (id_usuario,))
        usuario_atual = cursor.fetchone()
        if not usuario_atual:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
            
        novo_nome = dados.nome if dados.nome else usuario_atual[0]
        novo_email = dados.email if dados.email else usuario_atual[1]
        
        cursor.execute("UPDATE usuarios SET nome = %s, email = %s WHERE id_usuario = %s;", (novo_nome, novo_email, id_usuario))
        conexao.commit()
        return {"mensagem": "Perfil atualizado com sucesso."}
    except psycopg2.errors.UniqueViolation:
        conexao.rollback()
        raise HTTPException(status_code=409, detail="E-mail já está em uso por outro usuário.")
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.put("/perfil/senha")
def atualizar_senha(
    dados: SenhaUpdateRequest, 
    conexao = Depends(obter_conexao), 
    auth = Depends(exigir_role("usuario"))
):
    id_usuario = int(auth["sub"])
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT senha_hash FROM usuarios WHERE id_usuario = %s;", (id_usuario,))
        resultado = cursor.fetchone()
        if not resultado:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
            
        senha_hash_atual = resultado[0]
        
        if not verificar_senha(dados.senha_atual, senha_hash_atual):
            raise HTTPException(status_code=401, detail="Senha atual incorreta.")
            
        if len(dados.nova_senha) < 8:
            raise HTTPException(status_code=400, detail="A nova senha deve ter pelo menos 8 caracteres.")
            
        novo_hash = hash_senha(dados.nova_senha)
        
        cursor.execute("UPDATE usuarios SET senha_hash = %s WHERE id_usuario = %s;", (novo_hash, id_usuario))
        conexao.commit()
        return {"mensagem": "Senha atualizada com sucesso."}
    except Exception as e:
        conexao.rollback()
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

# =====================================================================
# Rotas: Multas do Usuário
# =====================================================================
@app.get("/multas")
def listar_multas_usuario(conexao = Depends(obter_conexao), auth = Depends(exigir_role("usuario"))):
    id_usuario = int(auth["sub"])
    cursor = conexao.cursor()
    try:
        cursor.execute("""
            SELECT m.id_multa, m.placa, m.motivo, m.valor, m.criado_em, m.status 
            FROM multas m
            JOIN usuario_veiculo uv ON m.placa = uv.placa
            WHERE uv.id_usuario = %s
            ORDER BY m.criado_em DESC;
        """, (id_usuario,))
        multas_bd = cursor.fetchall()
        return [
            {
                "id_multa": m[0],
                "placa": m[1],
                "motivo": m[2],
                "valor": float(m[3]),
                "criado_em": m[4],
                "status": m[5]
            } for m in multas_bd
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.post("/multas/{id_multa}/pagar")
def pagar_multa(id_multa: int, conexao = Depends(obter_conexao), auth = Depends(exigir_role("usuario"))):
    id_usuario = int(auth["sub"])
    cursor = conexao.cursor()
    try:
        # Verificar se a multa existe e pertence a um veiculo do usuario
        cursor.execute("""
            SELECT m.valor, m.status 
            FROM multas m
            JOIN usuario_veiculo uv ON m.placa = uv.placa
            WHERE m.id_multa = %s AND uv.id_usuario = %s FOR UPDATE;
        """, (id_multa, id_usuario))
        multa = cursor.fetchone()
        
        if not multa:
            raise HTTPException(status_code=404, detail="Multa não encontrada para os seus veículos.")
            
        valor_multa = float(multa[0])
        status = multa[1]
        
        if status == 'PAGA':
            raise HTTPException(status_code=400, detail="Esta multa já está paga.")

        # Verificar saldo
        cursor.execute("SELECT saldo FROM usuarios WHERE id_usuario = %s FOR UPDATE;", (id_usuario,))
        saldo_atual = float(cursor.fetchone()[0])
        
        if saldo_atual < valor_multa:
            raise HTTPException(status_code=402, detail="Saldo insuficiente para pagar a multa.")
            
        # Debitar saldo e registrar transação
        cursor.execute("UPDATE usuarios SET saldo = saldo - %s WHERE id_usuario = %s;", (valor_multa, id_usuario))
        cursor.execute("""
            INSERT INTO transacoes (id_usuario, tipo, valor, descricao)
            VALUES (%s, 'PAGAMENTO_MULTA', %s, 'Pagamento de multa: ' || %s);
        """, (id_usuario, -valor_multa, id_multa))
        
        # Atualizar status da multa
        cursor.execute("UPDATE multas SET status = 'PAGA' WHERE id_multa = %s;", (id_multa,))
        
        conexao.commit()
        return {"mensagem": "Multa paga com sucesso!"}
    except Exception as e:
        conexao.rollback()
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()