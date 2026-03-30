    FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instala dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código
COPY src/ ./src/
COPY config.yaml .
COPY .env .env

# Puerto de la API
EXPOSE 8000

# Comando de arranque
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]