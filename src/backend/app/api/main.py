import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

# ── Microservicio: Autenticación y Usuarios ────────────────────────────────────
from app.api.routes.user_auth_service import (
    user_CUD_service,
    user_query_service,
)

# ── Microservicio: Organización ───────────────────────────────────────────────
from app.api.routes.organization_service import (
    organization_CUD_service,
    organization_query_service,
)

# ── Microservicio: Gestión de Clasificación ───────────────────────────────────
from app.api.routes.classifications_service import (
    classifications_CUD_service,
    classifications_query_service,
)

# ── Microservicio: Reportes y Dashboard ───────────────────────────────────────
from app.api.routes.reports_service import reports_service

# ── Inicialización de la app ───────────────────────────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "API de Automatización Inteligente de Procesos PQR. "
        "Gestión de peticiones, quejas y reclamos con clasificación IA."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Eventos de ciclo de vida ───────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    print("Conexión establecida con la base de datos SQL Server.")


@app.on_event("shutdown")
async def shutdown_event():
    try:
        from backend.app.logic.universal_controller_instance import universal_controller
        if universal_controller.conn:
            universal_controller.conn.close()
            print("Conexión a la base de datos cerrada correctamente.")
    except Exception as exc:
        print(f"Error al cerrar la conexión: {exc}")


# ── Registro de routers ────────────────────────────────────────────────────────

# Microservicio 3 – Autenticación y Usuarios
app.include_router(user_CUD_service.router)    # POST /auth/login, POST /users/create, PUT /users/update, DELETE /users/delete/{id}
app.include_router(user_query_service.router)  # GET /users, GET /users/{id}

# Microservicio 4 – Organización
app.include_router(organization_CUD_service.router)
app.include_router(organization_query_service.router)

# Microservicios 6, 7 y 8 – Gestión de Clasificación
app.include_router(classifications_CUD_service.router)
app.include_router(classifications_query_service.router)

# Microservicio 12 – Reportes y Dashboard
app.include_router(reports_service.router)     # GET /reports/dashboard, /by-category, /by-priority, /by-area


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Verifica que la API esté en funcionamiento."""
    return {"status": "ok", "service": settings.PROJECT_NAME}
