from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

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
from app.api.routes.pqr_service import (
    pqr_CUD_service,
    pqr_query_service,
)
from app.api.routes.database_service import database_query_service

# ── Microservicio: Agente Inteligente ───────────────────────────────────────
from app.api.routes.ai_service import ai_service

# ── Microservicios: Roles, Archivos, Historial ────────────────────────────
from app.api.routes.role_service import role_CUD_service, role_query_service
from app.api.routes.file_service import file_CUD_service, file_query_service
from app.api.routes.history_service import history_CUD_service, history_query_service

# ── Inicialización de la app ───────────────────────────────────────────────────   
bearer_scheme = HTTPBearer()
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "API de Automatización Inteligente de Procesos PQR. "
        "Gestión de peticiones, quejas y reclamos con clasificación IA."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"persistAuthorization": True}
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
    pass


@app.on_event("shutdown")
async def shutdown_event():
    try:
        from app.logic.universal_controller_instance import universal_controller

        conn = getattr(universal_controller, "conn", None)
        if conn:
            conn.close()
    except Exception:
        pass


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

# Microservicio PQR
app.include_router(pqr_query_service.router)
app.include_router(pqr_CUD_service.router)

# Endpoints base de diagnóstico de base de datos Docker
app.include_router(database_query_service.router)

# Endpoints base de agente inteligente
app.include_router(ai_service.router)

# Microservicios de Roles, Archivos e Historial
app.include_router(role_CUD_service.router)
app.include_router(role_query_service.router)
app.include_router(file_CUD_service.router)
app.include_router(file_query_service.router)
app.include_router(history_CUD_service.router)
app.include_router(history_query_service.router)

# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Verifica que la API esté en funcionamiento."""
    return {
        "success": True,
        "message": "Servicio disponible",
        "data": {"status": "ok", "service": settings.PROJECT_NAME},
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": str(exc.detail),
            "data": None,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Error de validación en la solicitud",
            "data": {"errors": exc.errors()},
            "error_code": "VALIDATION_ERROR",
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Error interno del servidor",
            "data": None,
            "error_code": "INTERNAL_SERVER_ERROR",
        },
    )
