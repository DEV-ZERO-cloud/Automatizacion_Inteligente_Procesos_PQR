import logging

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.responses import JSONResponse

from app.core.auth import get_current_user
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.organization import AreaOut

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Organizacional"])


# ══════════════════════════════════════════════════════════════════════════════
#  4.2 GET /areas
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/areas")
async def get_all_areas(
    current_user: dict = Security(
        get_current_user, scopes=["admin", "supervisor", "agente", "usuario"]
    ),
):
    """
    Retorna la lista completa de áreas registradas.

    Requiere token válido.
    """
    try:
        logger.info("[GET /areas] Consultando todas las áreas.")
        areas = controller.get_all(AreaOut)

        data = [
            {
                "id": a.id,
                "nombre": a.nombre,
                "descripcion": a.descripcion,
            }
            for a in areas
        ]

        return JSONResponse(content={"success": True, "data": data})

    except Exception as exc:
        logger.error("[GET /areas] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
#  4.3 GET /areas/{id}
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/areas/{area_id}")
async def get_area_by_id(
    area_id: int,
    current_user: dict = Security(
        get_current_user, scopes=["admin", "supervisor", "agente", "usuario"]
    ),
):
    """
    Retorna la información de un área específica por su ID.

    Requiere token válido.
    """
    try:
        logger.info("[GET /areas/%s] Consultando área.", area_id)

        area: AreaOut = controller.get_by_id(AreaOut, area_id)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Área no encontrada.",
            )

        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "id": area.id,
                    "nombre": area.nombre,
                    "descripcion": area.descripcion,
                },
            }
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[GET /areas/%s] Error: %s", area_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}")
