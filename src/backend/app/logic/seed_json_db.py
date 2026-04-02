"""
seed_json_db.py
---------------
Carga datos de prueba en la base de datos JSON local.

Uso:
    cd src/backend
    python -m app.logic.seed_json_db

Genera los archivos:
    db/ROL.json
    db/Usuario.json
    db/Area.json
    db/PQR.json
    db/CATEGORIAS.json
    db/PRIORIDADES.json
    db/CLASIFICACIONES.json
    db/ARCHIVOS.json
    db/HISTORIAL.json
"""

from pathlib import Path
from app.logic.universal_controller_json import UniversalControllerJSON

DB_PATH = Path(__file__).parent.parent.parent.parent / "db"
ctrl = UniversalControllerJSON(db_path=DB_PATH)

# ── Áreas ─────────────────────────────────────────────────────────────────────
AREAS = [
    {"ID": 1, "nombre": "Tecnología", "descripcion": "Infraestructura y soporte técnico"},
    {"ID": 2, "nombre": "Cartera", "descripcion": "Gestión de cobros y facturación"},
    {"ID": 3, "nombre": "Servicio al Cliente", "descripcion": "Atención y resolución de solicitudes"},
    {"ID": 4, "nombre": "Recursos Humanos", "descripcion": "Gestión de personal"},
    {"ID": 5, "nombre": "Operaciones", "descripcion": "Operación del servicio"},
]

# ── Roles ─────────────────────────────────────────────────────────────────────
ROLES = [
    {"id": 1, "nombre": "admin"},
    {"id": 2, "nombre": "supervisor"},
    {"id": 3, "nombre": "agente"},
    {"id": 4, "nombre": "usuario"},
]

# ── Usuarios ───────────────────────────────────────────────────────────────────
# rol_id: 1=admin, 2=supervisor, 3=agente, 4=usuario
USUARIOS = [
    {
        "ID": 1,
        "identificacion": 100001,
        "nombre": "Admin Sistema",
        "correo": "admin@pqr.com",
        "telefono": "3001000001",
        "contrasena": "admin123",
        "rol_id": 1,
        "area_id": 1,
        "activo": 1,
    },
    {
        "ID": 2,
        "identificacion": 100002,
        "nombre": "Laura Supervisora",
        "correo": "laura@pqr.com",
        "telefono": "3001000002",
        "contrasena": "super456",
        "rol_id": 2,
        "area_id": 3,
        "activo": 1,
    },
    {
        "ID": 3,
        "identificacion": 100003,
        "nombre": "Carlos Agente",
        "correo": "carlos@pqr.com",
        "telefono": "3001000003",
        "contrasena": "agente789",
        "rol_id": 3,
        "area_id": 3,
        "activo": 1,
    },
    {
        "ID": 4,
        "identificacion": 100004,
        "nombre": "María Usuario",
        "correo": "maria@pqr.com",
        "telefono": "3001000004",
        "contrasena": "user000",
        "rol_id": 4,
        "area_id": 2,
        "activo": 1,
    },
    {
        "ID": 5,
        "identificacion": 100005,
        "nombre": "Pedro Inactivo",
        "correo": "pedro@pqr.com",
        "telefono": "3001000005",
        "contrasena": "inact111",
        "rol_id": 4,
        "area_id": 4,
        "activo": 0,
    },
]

# ── PQR ───────────────────────────────────────────────────────────────────────
PQRS = [
    {"ID": 1,  "titulo": "Factura incorrecta",       "descripcion": "Cobro no corresponde al consumo", "tipo": "reclamo",  "categoria": "Reclamo",  "prioridad": "alta",  "estado": "pendiente", "area_id": 2, "usuario_id": 4},
    {"ID": 2,  "titulo": "No funciona el portal",    "descripcion": "No permite autenticación",         "tipo": "queja",    "categoria": "Queja",    "prioridad": "alta",  "estado": "pendiente", "area_id": 1, "usuario_id": 4},
    {"ID": 3,  "titulo": "Solicitud de certificado", "descripcion": "Certificado de paz y salvo",       "tipo": "peticion", "categoria": "Petición", "prioridad": "media", "estado": "resuelta",  "area_id": 4, "usuario_id": 3},
    {"ID": 4,  "titulo": "Demora en respuesta",      "descripcion": "Sin respuesta en 10 días",         "tipo": "queja",    "categoria": "Queja",    "prioridad": "media", "estado": "resuelta",  "area_id": 3, "usuario_id": 4},
    {"ID": 5,  "titulo": "Error en descuento",       "descripcion": "Descuento no aplicado",            "tipo": "reclamo",  "categoria": "Reclamo",  "prioridad": "alta",  "estado": "pendiente", "area_id": 2, "usuario_id": 4},
    {"ID": 6,  "titulo": "Cambio de dirección",      "descripcion": "Actualizar dirección de envío",    "tipo": "peticion", "categoria": "Petición", "prioridad": "baja",  "estado": "resuelta",  "area_id": 3, "usuario_id": 3},
    {"ID": 7,  "titulo": "Cobro duplicado",          "descripcion": "Cobro repetido en dos facturas",   "tipo": "reclamo",  "categoria": "Reclamo",  "prioridad": "alta",  "estado": "pendiente", "area_id": 2, "usuario_id": 4},
    {"ID": 8,  "titulo": "Mala atención agente",     "descripcion": "Atención irrespetuosa",            "tipo": "queja",    "categoria": "Queja",    "prioridad": "media", "estado": "resuelta",  "area_id": 3, "usuario_id": 4},
    {"ID": 9,  "titulo": "Información de producto",  "descripcion": "Consulta sobre cobertura",         "tipo": "peticion", "categoria": "Petición", "prioridad": "baja",  "estado": "resuelta",  "area_id": 5, "usuario_id": 3},
    {"ID": 10, "titulo": "Sistema caído",            "descripcion": "Plataforma indisponible",          "tipo": "queja",    "categoria": "Queja",    "prioridad": "alta",  "estado": "pendiente", "area_id": 1, "usuario_id": 4},
]

# ── Catálogos de clasificación ───────────────────────────────────────────────
CATEGORIAS = [
    {"id": 1, "nombre": "Facturación"},
    {"id": 2, "nombre": "Soporte Técnico"},
    {"id": 3, "nombre": "Servicio al Cliente"},
    {"id": 4, "nombre": "Infraestructura"},
    {"id": 5, "nombre": "Legal"},
]

PRIORIDADES = [
    {"id": 1, "nombre": "Baja"},
    {"id": 2, "nombre": "Media"},
    {"id": 3, "nombre": "Alta"},
    {"id": 4, "nombre": "Urgente"},
]

CLASIFICACIONES = [
    {
        "id": 1,
        "pqr_id": 1,
        "modelo_version": "v2.4.0",
        "categoria_id": 1,
        "prioridad_id": 3,
        "confianza": 0.94,
        "origen": "IA",
        "fue_corregida": False,
        "validado_por": None,
        "created_at": "2026-04-01T10:15:00",
    },
    {
        "id": 2,
        "pqr_id": 2,
        "modelo_version": "v2.4.0",
        "categoria_id": 2,
        "prioridad_id": 4,
        "confianza": 0.98,
        "origen": "IA",
        "fue_corregida": False,
        "validado_por": None,
        "created_at": "2026-04-01T10:21:00",
    },
    {
        "id": 3,
        "pqr_id": 3,
        "modelo_version": "v2.4.0",
        "categoria_id": 3,
        "prioridad_id": 2,
        "confianza": 0.82,
        "origen": "MANUAL",
        "fue_corregida": True,
        "validado_por": 2,
        "created_at": "2026-04-01T11:05:00",
    },
]

ARCHIVOS = [
    {"id": 1, "pqr_id": 1, "filename": "factura_abril.pdf", "filepath": "uploads/factura_abril.pdf", "mimetype": "application/pdf", "created_at": "2026-04-01T10:16:00"},
    {"id": 2, "pqr_id": 2, "filename": "captura_error.png", "filepath": "uploads/captura_error.png", "mimetype": "image/png", "created_at": "2026-04-01T10:22:00"},
]

HISTORIAL = [
    {"id": 1, "pqr_id": 1, "usuario_id": 2, "accion": "validacion", "comentario": "Clasificación confirmada", "created_at": "2026-04-01T10:45:00"},
    {"id": 2, "pqr_id": 3, "usuario_id": 2, "accion": "correccion", "comentario": "Ajuste de prioridad", "created_at": "2026-04-01T11:10:00"},
]


def main():
    print(f"\nCargando datos de prueba en: {DB_PATH}\n")

    ctrl.seed("ROL",     ROLES,    overwrite=True)
    print(f"  ✓ ROL     → {len(ROLES)} registros")

    ctrl.seed("Area",    AREAS,    overwrite=True)
    print(f"  ✓ Area    → {len(AREAS)} registros")

    ctrl.seed("Usuario", USUARIOS, overwrite=True)
    print(f"  ✓ Usuario → {len(USUARIOS)} registros")

    ctrl.seed("PQR",     PQRS,     overwrite=True)
    print(f"  ✓ PQR     → {len(PQRS)} registros")

    ctrl.seed("CATEGORIAS",      CATEGORIAS,      overwrite=True)
    print(f"  ✓ CATEGORIAS      → {len(CATEGORIAS)} registros")

    ctrl.seed("PRIORIDADES",     PRIORIDADES,     overwrite=True)
    print(f"  ✓ PRIORIDADES     → {len(PRIORIDADES)} registros")

    ctrl.seed("CLASIFICACIONES", CLASIFICACIONES, overwrite=True)
    print(f"  ✓ CLASIFICACIONES → {len(CLASIFICACIONES)} registros")

    ctrl.seed("ARCHIVOS", ARCHIVOS, overwrite=True)
    print(f"  ✓ ARCHIVOS        → {len(ARCHIVOS)} registros")

    ctrl.seed("HISTORIAL", HISTORIAL, overwrite=True)
    print(f"  ✓ HISTORIAL       → {len(HISTORIAL)} registros")

    print("\nTablas disponibles:", ctrl.list_tables())
    print("\nSeed completado. Puedes iniciar el servidor con:")
    print("  DB_MODE=json uvicorn app.api.main:app --reload\n")


if __name__ == "__main__":
    main()
