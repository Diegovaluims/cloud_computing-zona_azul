# Python 3.12 slim: imagem leve sem pacotes desnecessários
FROM python:3.12.3-slim

WORKDIR /app

# Copia apenas o requirements antes do código-fonte para aproveitar o cache de camadas do Docker
# (se o requirements não mudar, o pip install não é reexecutado no rebuild)
COPY backend_usuario/requirements.txt .

# Módulo compartilhado de conexão com o banco — copiado como pacote Python
COPY db/ ./db/

# --no-cache-dir: evita cache para manter a imagem menor
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte do microsserviço
COPY backend_usuario/ .

# Inicia o servidor Uvicorn
# --host 0.0.0.0: necessário para expor a porta para fora do contêiner (não apenas localhost)
CMD  ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
