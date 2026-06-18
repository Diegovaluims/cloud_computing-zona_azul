"""
Backend de Autenticação - Microsserviço
Responsável por criar contas e emitir tokens JWT para Usuários e Fiscais.
Porta padrão: 8002
"""
import os
from fastapi import FastAPI, Depends, HTTPException, Header, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import psycopg2.errors
from db.database_connect import obter_conexao
from db.auth import hash_senha, verificar_senha, criar_token

app = FastAPI(title="API Zona Azul - Auth Service")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    email: str
    senha: str

class RegistroRequest(BaseModel):
    nome: str
    email: str
    senha: str

class LoginFiscalRequest(BaseModel):
    matricula: str
    senha: str

class RegistroFiscalRequest(BaseModel):
    nome: str
    matricula: str
    senha: str

# =====================================================================
# Rotas: Usuário
# =====================================================================

@app.post("/registro", status_code=201)
def criar_usuario(usuario: RegistroRequest, conexao = Depends(obter_conexao)):
    if len(usuario.senha) < 8:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 8 caracteres.")
        
    senha_hasheada = hash_senha(usuario.senha)
    cursor = conexao.cursor()
    try:
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha_hash) 
            VALUES (%s, %s, %s) RETURNING id_usuario;
        """, (usuario.nome, usuario.email, senha_hasheada))
        id_novo = cursor.fetchone()[0]
        conexao.commit()
        return {"mensagem": "Usuário criado com sucesso!", "id_usuario": id_novo}
    except psycopg2.errors.UniqueViolation:
        conexao.rollback()
        raise HTTPException(status_code=409, detail="E-mail já cadastrado no sistema.")
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar usuário: {e}")
    finally:
        cursor.close()

@app.post("/login")
def realizar_login(dados: LoginRequest, response: Response, conexao = Depends(obter_conexao)):
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT id_usuario, nome, senha_hash FROM usuarios WHERE email = %s;", (dados.email,))
        usuario = cursor.fetchone()
        
        if not usuario or not verificar_senha(dados.senha, usuario[2]):
            raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
            
        token = criar_token({"sub": str(usuario[0]), "nome": usuario[1]}, "usuario")
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False, # TODO: Configurar Secure=True via .env
            samesite="lax",
            max_age=30 * 60
        )
        return {"id_usuario": usuario[0], "nome": usuario[1]}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")
    finally:
        cursor.close()

@app.post("/logout")
def realizar_logout(response: Response):
    response.delete_cookie("access_token", httponly=True, secure=False, samesite="lax")
    return {"mensagem": "Logout realizado com sucesso."}

# =====================================================================
# Rotas: Fiscal
# =====================================================================

@app.post("/fiscal/registro", status_code=201)
def registrar_fiscal(fiscal: RegistroFiscalRequest, x_admin_key: str = Header(None), conexao = Depends(obter_conexao)):
    admin_key_esperada = os.getenv("ADMIN_KEY")
    if not admin_key_esperada or x_admin_key != admin_key_esperada:
        raise HTTPException(status_code=403, detail="Chave de admin inválida ou ausente.")

    if len(fiscal.senha) < 8:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 8 caracteres.")

    senha_hasheada = hash_senha(fiscal.senha)
    cursor = conexao.cursor()
    try:
        cursor.execute("""
            INSERT INTO fiscais (nome, matricula, senha_hash)
            VALUES (%s, %s, %s) RETURNING id_fiscal;
        """, (fiscal.nome, fiscal.matricula, senha_hasheada))
        id_novo = cursor.fetchone()[0]
        conexao.commit()
        return {"mensagem": "Fiscal registrado com sucesso!", "id_fiscal": id_novo}
    except psycopg2.errors.UniqueViolation:
        conexao.rollback()
        raise HTTPException(status_code=409, detail="Matrícula já cadastrada no sistema.")
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar fiscal: {e}")
    finally:
        cursor.close()

@app.post("/fiscal/login")
def login_fiscal(dados: LoginFiscalRequest, response: Response, conexao = Depends(obter_conexao)):
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT id_fiscal, nome, senha_hash FROM fiscais WHERE matricula = %s;", (dados.matricula,))
        fiscal = cursor.fetchone()
        
        if not fiscal or not verificar_senha(dados.senha, fiscal[2]):
            raise HTTPException(status_code=401, detail="Matrícula ou senha incorretos.")
            
        token = criar_token({"sub": str(fiscal[0]), "nome": fiscal[1]}, "fiscal")
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False, # TODO: Configurar Secure=True via .env
            samesite="lax",
            max_age=30 * 60
        )
        return {"id_fiscal": fiscal[0], "nome": fiscal[1]}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")
    finally:
        cursor.close()

@app.post("/fiscal/logout")
def logout_fiscal(response: Response):
    response.delete_cookie("access_token", httponly=True, secure=False, samesite="lax")
    return {"mensagem": "Logout realizado com sucesso."}
