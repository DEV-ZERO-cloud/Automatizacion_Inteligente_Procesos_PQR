# Automatizacion Inteligente de Procesos PQR

<p align="center">
	<img alt="Status" src="https://img.shields.io/badge/Status-Ready%20for%20Dev-16a34a?style=for-the-badge" />
	<img alt="Docker" src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
	<img alt="Backend" src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
	<img alt="Frontend" src="https://img.shields.io/badge/Frontend-React%20%2B%20Vite-0ea5e9?style=for-the-badge&logo=react&logoColor=white" />
</p>

<p align="center">
	<img alt="Database" src="https://img.shields.io/badge/Database-PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white" />
	<img alt="Adminer" src="https://img.shields.io/badge/Adminer-Enabled-0f766e?style=flat-square" />
	<img alt="API Docs" src="https://img.shields.io/badge/API%20Docs-Swagger%20%2F%20ReDoc-f59e0b?style=flat-square" />
	<img alt="Seed Data" src="https://img.shields.io/badge/Seed-Preloaded-7c3aed?style=flat-square" />
</p>

<p align="center">
	<a href="#inicio-rapido">Inicio rapido</a> •
	<a href="#servicios">Servicios</a> •
	<a href="#usuarios-base">Usuarios base</a> •
	<a href="#adminer-keys">Adminer</a>
</p>

Plataforma para gestionar y clasificar PQR con apoyo de IA, frontend web y API FastAPI.

## ✨ Estado actual

- Stack listo para levantar con Docker (frontend + backend + postgres + adminer).
- Arranque simplificado: construyes imagen y enciendes contenedores.
- Datos base incluidos para pruebas funcionales desde el primer inicio.

<a id="inicio-rapido"></a>

## 🚀 Inicio rapido con Docker

Prerequisito unico:

- Docker Desktop activo.

Desde la raiz del repositorio:

```bash
docker compose up -d --build
```

Si ya tienes la imagen construida, solo enciende:

```bash
docker compose up -d
```

<a id="servicios"></a>

## 🌐 Servicios disponibles

| Servicio | URL | Puerto |
|---|---|---|
| Frontend | http://localhost:5173 | 5173 |
| Backend API | http://localhost:8000 | 8000 |
| Swagger | http://localhost:8000/docs | 8000 |
| ReDoc | http://localhost:8000/redoc | 8000 |
| Adminer | http://localhost:8080 | 8080 |
| PostgreSQL | localhost | 5432 |

<a id="usuarios-base"></a>

## 🔐 Usuarios base para login en la app

Usa estos datos en el login de la API/app (usuario = correo, password = contrasena):

| Rol | Correo | Contrasena | Estado |
|---|---|---|---|
| Admin | admin@pqr.com | admin123 | Activo |
| Supervisor | laura@pqr.com | super456 | Activo |
| Agente | carlos@pqr.com | agente789 | Activo |
| Usuario | maria@pqr.com | user000 | Activo |
| Usuario | pedro@pqr.com | inact111 | Inactivo |

<a id="adminer-keys"></a>

## 🗄️ Claves de Adminer / PostgreSQL

En Adminer usa exactamente estos campos:

- System: PostgreSQL
- Server: postgres
- Username: pqr_user
- Password: pqr_password
- Database: pqr_db

Nota: Adminer no trae una cuenta propia, se autentica con las credenciales de PostgreSQL.

## ⚙️ Comandos utiles

Levantar contenedores:

```bash
docker compose up -d --build
```

Ver logs en vivo:

```bash
docker compose logs -f
```

Detener stack:

```bash
docker compose down
```

Reiniciar solo backend:

```bash
docker compose restart backend
```

## 🧠 Notas tecnicas breves

- El backend inicia ejecutando seed JSON automaticamente.
- El servicio postgres se inicializa con SQL desde src/db/postgres/init/01_schema_and_seed.sql.
- Endpoints de diagnostico BD disponibles: /db/health, /db/config, /db/tables.

## 📁 Estructura principal

- src/backend: API FastAPI + logica de negocio + IA.
- src/frontend: app React + Vite.
- src/db: datos JSON y scripts SQL de inicializacion.
- 
