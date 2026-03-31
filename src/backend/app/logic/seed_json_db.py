"""
seed_json_db.py
---------------
Carga datos de prueba en la base de datos JSON local.

Uso:
    cd src/backend
    python -m app.logic.seed_json_db

Genera los archivos:
    db/Usuario.json
    db/Area.json
    db/PQR.json
"""

from pathlib import Path
from app.logic.universal_controller_json import UniversalControllerJSON

DB_PATH = Path(__file__).parent.parent.parent.parent / "db"
ctrl = UniversalControllerJSON(db_path=DB_PATH)

# ── Áreas ─────────────────────────────────────────────────────────────────────
AREAS = [
    {"ID": 1, "nombre": "Tecnología"},
    {"ID": 2, "nombre": "Cartera"},
    {"ID": 3, "nombre": "Servicio al Cliente"},
    {"ID": 4, "nombre": "Recursos Humanos"},
    {"ID": 5, "nombre": "Operaciones"},
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
    {"ID": 1,  "titulo": "Factura incorrecta",       "categoria": "Reclamo",  "prioridad": "alta",  "estado": "pendiente", "area_id": 2, "usuario_id": 4},
    {"ID": 2,  "titulo": "No funciona el portal",    "categoria": "Queja",    "prioridad": "alta",  "estado": "pendiente", "area_id": 1, "usuario_id": 4},
    {"ID": 3,  "titulo": "Solicitud de certificado", "categoria": "Petición", "prioridad": "media", "estado": "resuelta",  "area_id": 4, "usuario_id": 3},
    {"ID": 4,  "titulo": "Demora en respuesta",      "categoria": "Queja",    "prioridad": "media", "estado": "resuelta",  "area_id": 3, "usuario_id": 4},
    {"ID": 5,  "titulo": "Error en descuento",       "categoria": "Reclamo",  "prioridad": "alta",  "estado": "pendiente", "area_id": 2, "usuario_id": 4},
    {"ID": 6,  "titulo": "Cambio de dirección",      "categoria": "Petición", "prioridad": "baja",  "estado": "resuelta",  "area_id": 3, "usuario_id": 3},
    {"ID": 7,  "titulo": "Cobro duplicado",          "categoria": "Reclamo",  "prioridad": "alta",  "estado": "pendiente", "area_id": 2, "usuario_id": 4},
    {"ID": 8,  "titulo": "Mala atención agente",     "categoria": "Queja",    "prioridad": "media", "estado": "resuelta",  "area_id": 3, "usuario_id": 4},
    {"ID": 9,  "titulo": "Información de producto",  "categoria": "Petición", "prioridad": "baja",  "estado": "resuelta",  "area_id": 5, "usuario_id": 3},
    {"ID": 10, "titulo": "Sistema caído",            "categoria": "Queja",    "prioridad": "alta",  "estado": "pendiente", "area_id": 1, "usuario_id": 4},
]


def main():
    print(f"\nCargando datos de prueba en: {DB_PATH}\n")

    ctrl.seed("Area",    AREAS,    overwrite=True)
    print(f"  ✓ Area    → {len(AREAS)} registros")

    ctrl.seed("Usuario", USUARIOS, overwrite=True)
    print(f"  ✓ Usuario → {len(USUARIOS)} registros")

    ctrl.seed("PQR",     PQRS,     overwrite=True)
    print(f"  ✓ PQR     → {len(PQRS)} registros")

    print("\nTablas disponibles:", ctrl.list_tables())
    print("\nSeed completado. Puedes iniciar el servidor con:")
    print("  DB_MODE=json uvicorn app.api.main:app --reload\n")


if __name__ == "__main__":
    main()
