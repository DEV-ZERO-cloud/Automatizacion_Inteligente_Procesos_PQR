# ProjectProbe - Sistema de PQR's

Sistema de gestión de Peticiones, Quejas y Reclamos con 3 roles de usuario.

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │  PostgreSQL │  │   Backend   │  │    Frontend     │  │
│  │   (Puerto   │  │   (FastAPI) │  │    (Next.js)    │  │
│  │    5432)    │  │  (Puerto    │  │   (Puerto 3000) │  │
│  │             │  │   8000)     │  │                 │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 👥 Roles

| Rol | Descripción |
|-----|-------------|
| **Usuario** | Crea PQR's, ve sus solicitudes y recibe notificaciones |
| **Supervisor** | Gestiona PQR's asignadas, actualiza estados, agrega comentarios |
| **Operador** | Ve TODAS las PQR's, asigna supervisores, ve estadísticas |

## 🚀 Cómo Ejecutar

### 1. Base de Datos (PostgreSQL)

```bash
# Opción A: Docker Compose
docker-compose up -d

# Opción B: Docker directo
docker run -d \
  --name pqr_postgres \
  -e POSTGRES_USER=pqr_user \
  -e POSTGRES_PASSWORD=pqr_password \
  -e POSTGRES_DB=pqr_db \
  -p 5432:5432 \
  -v pqr_data:/var/lib/postgresql/data \
  postgres:16
```

### 2. Backend (FastAPI)

```bash
cd backend

# Crear entorno virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Ejecutar servidor
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend (Next.js)

```bash
cd frontend

# Instalar dependencias
npm install

# Ejecutar servidor desarrollo
npm run dev
```

### 4. Acceder a la Aplicación

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Docs Swagger**: http://localhost:8000/docs

## 📧 Configuración de Email

Para activar las notificaciones por email, edita el archivo `backend/.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password
```

> **Nota**: Para Gmail, necesitas crear una "App Password" en la configuración de seguridad de tu cuenta.

## 📁 Estructura del Proyecto

```
ProjectProbe/
├── backend/
│   ├── app/
│   │   ├── core/          # Config, database, security
│   │   ├── models/         # Modelos SQLAlchemy
│   │   ├── routers/        # Endpoints API
│   │   ├── schemas/        # Schemas Pydantic
│   │   ├── services/       # Email, archivos
│   │   └── main.py         # App FastAPI
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/
│   │   ├── login/
│   │   ├── register/
│   │   └── dashboard/
│   ├── components/
│   ├── lib/
│   └── package.json
│
├── docker-compose.yml
└── README.md
```

## 🔑 Credenciales Demo

Después de ejecutar el sistema, crea un operador inicial:

1. Accede a http://localhost:8000/docs
2. Ve a `/api/v1/auth/register`
3. Crea un usuario normal
4. Manual: Actualiza la base de datos para cambiar su rol a `operador`

## 🎨 Paleta de Colores

| Color | Hex | Uso |
|-------|-----|-----|
| Primary | #E60023 | Botones, acentos |
| Success | #00A67E | Estados positivos |
| Warning | #FFC107 | Estados en proceso |
| Background | #FAFAFA | Fondo general |

## 📝 API Endpoints Principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Registro usuario |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/auth/me` | Usuario actual |
| POST | `/api/v1/pqr` | Crear PQR |
| GET | `/api/v1/pqr/mis-pqrs` | Mis PQR's |
| GET | `/api/v1/pqr/asignadas` | PQR's asignadas (Supervisor) |
| GET | `/api/v1/pqr/todas` | Todas las PQR's (Operador) |
| PUT | `/api/v1/pqr/{id}/estado` | Actualizar estado |
| PUT | `/api/v1/pqr/{id}/asignar` | Asignar supervisor |

## 🛠️ Tecnologías

- **Frontend**: Next.js 14, React, Tailwind CSS, TypeScript
- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Base de Datos**: PostgreSQL 16
- **Email**: aiosmtplib (async)
