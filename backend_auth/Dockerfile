# Python 3.12 slim: imagem leve sem pacotes desnecessários
FROM python:3.12.3-slim

WORKDIR /app

# Copia apenas o requirements antes do código-fonte para aproveitar o cache de camadas do Docker
COPY backend_auth/requirements.txt .

# Módulo compartilhado de conexão com o banco — copiado como pacote Python
COPY db/ ./db/

# --no-cache-dir: evita cache para manter a imagem menor
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte do microsserviço
COPY backend_auth/ .

# Inicia o servidor Uvicorn
# Porta interna: 8002
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
