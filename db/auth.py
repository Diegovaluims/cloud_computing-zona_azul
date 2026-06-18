"""
Módulo compartilhado de autenticação.
Responsável por hash de senhas, criação e validação de JWTs,
e dependências FastAPI para proteção de rotas.
"""
import os
import secrets
import logging
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import Request, HTTPException

# Configuração do bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração do JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_jwt_secret():
    """Resolve o secret de forma segura (Env -> Arquivo -> Ephemeral)."""
    secret = os.getenv("JWT_SECRET_KEY")
    if secret:
        return secret
    
    arquivo_secret = "jwt_secret.txt"
    if os.path.exists(arquivo_secret):
        with open(arquivo_secret, "r") as f:
            return f.read().strip()
            
    logging.warning("GERANDO SECRET EPHEMERAL PARA JWT! Não recomendado para produção horizontal.")
    ephemeral = secrets.token_hex(32)
    with open(arquivo_secret, "w") as f:
        f.write(ephemeral)
    return ephemeral

SECRET_KEY = get_jwt_secret()

def hash_senha(senha: str) -> str:
    """Gera o hash bcrypt da senha."""
    return pwd_context.hash(senha)

def verificar_senha(senha: str, hash_senha: str) -> bool:
    """Verifica se a senha em texto plano bate com o hash."""
    return pwd_context.verify(senha, hash_senha)

def criar_token(data: dict, role: str) -> str:
    """Cria um JWT com expiração e role."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "role": role})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def obter_dados_token(request: Request) -> dict:
    """Extrai e decodifica o JWT do cookie."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Não autenticado. Faça login.")
    
    # O cookie pode vir com prefixo (embora com HttpOnly geralmente enviamos apenas o valor)
    if token.startswith("Bearer "):
        token = token[7:]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

def exigir_role(role_esperada: str):
    """Dependência FastAPI que garante que o usuário tem a role específica."""
    def verificador_role(request: Request):
        payload = obter_dados_token(request)
        role = payload.get("role")
        if role != role_esperada:
            raise HTTPException(status_code=403, detail="Acesso negado para o seu perfil.")
        return payload
    return verificador_role
