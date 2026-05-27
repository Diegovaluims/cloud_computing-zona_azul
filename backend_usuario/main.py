from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import veiculos_router, reservas_router

# Inicialização da Aplicação
app = FastAPI(title="API Zona Azul - Usuário")

# Configuração do CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro das Rotas
app.include_router(veiculos_router.router)
app.include_router(reservas_router.router)

@app.get("/", tags=["Healthcheck"])
def root():
    """
    Endpoint de healthcheck para verificar se a API está online.
    Retorna o status da aplicação e uma mensagem de boas-vindas.
    """
    return {
        "status": "Online",
        "mensagem": "API do Zona Azul (Usuário) rodando com sucesso! Acesse /docs para testar."
    }