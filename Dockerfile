FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instala dependencias Python
COPY src/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código
COPY src/backend/app ./app
COPY src/db ./db
COPY src/data/models ./data/models 
COPY config.yaml ./config.yaml

# Puerto de la API
EXPOSE 8000

# Comando de arranque
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]