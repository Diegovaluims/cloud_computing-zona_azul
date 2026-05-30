# Distro Linux com Python
FROM python:3.12.3-slim

WORKDIR /app

# Pacotes e versões
COPY backend_usuario/requirements.txt .

COPY db/database_connect.py .

# Instala tudo sem cache
RUN pip install --no-cache-dir -r requirements.txt

# Copia tudo para dentro do Docker
COPY backend_usuario/ .

# Uvicorn para subir a API
CMD  ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
