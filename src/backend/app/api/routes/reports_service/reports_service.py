import logging

from fastapi import APIRouter, HTTPException, Security

from app.core.auth import get_current_user
from app.core.responses import ok_response
from app.logic.universal_controller_instance import universal_controller as controller

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(prefix="/reports", tags=["Reportes y Dashboard"])

# Scopes autorizados para todos los endpoints de reportes
REPORT_SCOPES = ["admin", "supervisor", "operador", "gerente"]


# ══════════════════════════════════════════════════════════════════════════════
#  12.1 GET /reports/dashboard
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/dashboard")
async def get_dashboard(
    current_user: dict = Security(get_current_user, scopes=REPORT_SCOPES),
):
    """
    Retorna el resumen general del dashboard: total de PQR, pendientes y resueltas.

    Requiere token con scope **admin** o **supervisor**.
    """
    try:
        logger.info("[GET /reports/dashboard] Generando resumen del dashboard.")
        summary = controller.get_dashboard_summary()

        return ok_response(
            data={
                "total_pqrs": summary["total_pqrs"],
                "pendientes": summary["pendientes"],
                "resueltas": summary["resueltas"],
            },
            message="Dashboard consultado",
        )

    except Exception as exc:
        logger.error("[GET /reports/dashboard] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="No se pudo generar el dashboard")


# ══════════════════════════════════════════════════════════════════════════════
#  12.2 GET /reports/by-category
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/by-category")
async def get_by_category(
    current_user: dict = Security(get_current_user, scopes=REPORT_SCOPES),
):
    """
    Retorna la cantidad de PQR agrupadas por categoría.

    Requiere token con scope **admin** o **supervisor**.
    """
    try:
        logger.info("[GET /reports/by-category] Generando reporte por categoría.")
        data = controller.get_pqrs_by_category()

        return ok_response(data=data, message="Reporte por categoría consultado")

    except Exception as exc:
        logger.error("[GET /reports/by-category] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="No se pudo generar el reporte")


# ══════════════════════════════════════════════════════════════════════════════
#  12.3 GET /reports/by-priority
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/by-priority")
async def get_by_priority(
    current_user: dict = Security(get_current_user, scopes=REPORT_SCOPES),
):
    """
    Retorna la cantidad de PQR agrupadas por prioridad.

    Requiere token con scope **admin** o **supervisor**.
    """
    try:
        logger.info("[GET /reports/by-priority] Generando reporte por prioridad.")
        data = controller.get_pqrs_by_priority()

        return ok_response(data=data, message="Reporte por prioridad consultado")

    except Exception as exc:
        logger.error("[GET /reports/by-priority] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="No se pudo generar el reporte")


# ══════════════════════════════════════════════════════════════════════════════
#  12.4 GET /reports/by-area
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/by-area")
async def get_by_area(
    current_user: dict = Security(get_current_user, scopes=REPORT_SCOPES),
):
    """
    Retorna la cantidad de PQR agrupadas por área organizacional.

    Requiere token con scope **admin** o **supervisor**.
    """
    try:
        logger.info("[GET /reports/by-area] Generando reporte por área.")
        data = controller.get_pqrs_by_area()

        return ok_response(data=data, message="Reporte por área consultado")

    except Exception as exc:
        logger.error("[GET /reports/by-area] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="No se pudo generar el reporte")
