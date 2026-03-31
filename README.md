# Clasificador Inteligente de PQR para Empresas

Este proyecto propone el desarrollo de un prototipo de sistema inteligente para automatizar la clasificación de solicitudes de **Peticiones, Quejas y Reclamos (PQR)** en una empresa de servicios.

---

## Configuración del Backend

Sigue estos pasos para preparar el entorno y ejecutar el servidor de desarrollo.

### 1. Acceder al directorio

Desde la terminal, navega a la carpeta del backend:

```bash
cd src/backend
```

## 2. Crear entorno virtual

```bash
python -m venv .venv
```

## 3. Activar entorno virtual

### Windows (PowerShell)

```bash
.venv\Scripts\Activate.ps1
```

### Windows (CMD)

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

## 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 5. Configurar variables de entorno

Crear un archivo .env en la raíz de src/backend con las variables necesarias del proyecto.

## 6. Ejecutar backend en desarrollo

```bash
uvicorn app.api.main:app --reload
```

### URL de desarrollo

http://127.0.0.1:8000

### Documentación automática de la API

Swagger UI: http://127.0.0.1:8000/docs

ReDoc: http://127.0.0.1:8000/redoc