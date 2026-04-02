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

---

## Base de Datos Actual (JSON)

Actualmente el proyecto corre con base de datos local en archivos JSON (modo desarrollo), ubicada en:

`src/db/`

Se genera/actualiza con:

```bash
cd src/backend
python -m app.logic.seed_json_db
```

Tablas seed actuales:

- `ROL.json`
- `Usuario.json`
- `Area.json`
- `PQR.json`
- `CATEGORIAS.json`
- `PRIORIDADES.json`
- `CLASIFICACIONES.json`
- `ARCHIVOS.json`
- `HISTORIAL.json`

La estructura se alineó con el diagrama de `src/extras/image.png` para entorno local.

---

## Arranque Local Rápido (Windows)

Desde la raíz del repo:

```bat
src\start.bat
```

Este script:

1. Ejecuta seed de base de datos JSON.
2. Levanta backend en `http://localhost:8000`.
3. Levanta frontend en `http://localhost:5173`.

---

## Ejecutar con Docker (Frontend + Backend + PostgreSQL + Adminer)

En la raíz del repositorio:

```bash
docker compose up --build
```

Servicios:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Adminer: `http://localhost:8080`

Credenciales base de PostgreSQL (docker-compose):

- Server: `postgres`
- Database: `pqr_db`
- Username: `pqr_user`
- Password: `pqr_password`

El esquema y seed de PostgreSQL se inicializan automáticamente desde:

- `src/db/postgres/init/01_schema_and_seed.sql`

La carpeta `src/db` se monta como volumen en el backend para compartir datos entre usuarios del repositorio.

---

## Endpoints Base de BD (No Estáticos)

Se agregaron endpoints de diagnóstico para validar conexión real a PostgreSQL en Docker:

- `GET /db/health`: estado de conexión + configuración activa
- `GET /db/config`: configuración pública de conexión usada por la API
- `GET /db/tables`: lista de tablas y conteo de filas
- `GET /db/tables/{table_name}?limit=20&offset=0`: filas reales por tabla

Ejemplo rápido:

```bash
curl http://localhost:8000/db/health
curl http://localhost:8000/db/tables
curl "http://localhost:8000/db/tables/pqrs?limit=5"
```