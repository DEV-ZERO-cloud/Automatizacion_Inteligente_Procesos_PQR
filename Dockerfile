FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dependencias del sistema requeridas por paquetes Python y chequeos de salud
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instala dependencias Python
COPY src/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código y la configuracion del backend
COPY src/backend/app ./app
COPY src/db ./db
COPY src/data/models /data/models
COPY config.yaml ./config.yaml

# Puerto de la API
EXPOSE 8000

# Arranque en modo desarrollo dentro del contenedor
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]