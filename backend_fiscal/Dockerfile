FROM python:3.12.3-slim

WORKDIR /app

COPY backend_fiscal/requirements.txt .

COPY db/database_connect.py .

RUN pip install --no-cache-dir -r requirements.txt

COPY backend_fiscal/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]