import logging

from fastapi import APIRouter, HTTPException, Security, status

from app.core.auth import get_current_user
from app.core.responses import ok_response
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
        get_current_user, scopes=["admin", "supervisor", "operador", "agente", "usuario"]
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

        return ok_response(data=data, message="Áreas consultadas")

    except Exception as exc:
        logger.error("[GET /areas] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ══════════════════════════════════════════════════════════════════════════════
#  4.3 GET /areas/{id}
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/areas/{area_id}")
async def get_area_by_id(
    area_id: int,
    current_user: dict = Security(
        get_current_user, scopes=["admin", "supervisor", "operador", "agente", "usuario"]
    ),
):
    """
    Retorna la información de un área específica por su ID.

    Requiere token válido.
    """
    try:
        logger.info("[GET /areas/%s] Consultando área.", area_id)

        area: AreaOut | None = controller.get_by_id(AreaOut, area_id)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Área no encontrada.",
            )

        return ok_response(
            data={
                "id": area.id,
                "nombre": area.nombre,
                "descripcion": area.descripcion,
            },
            message="Área consultada",
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[GET /areas/%s] Error: %s", area_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/areas/name")
async def get_priority_by_name(
    area_name: str,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "operador", "agente", "usuario"]),
):
    try:
        obj: AreaOut | None = controller.get_by_column(AreaOut, column="nombre", value=area_name)
        if not obj: raise HTTPException(status_code=404, detail="No encontrada")
        return ok_response(data=obj.to_dict(), message="Categoría consultada")
    except HTTPException: raise
    except Exception: raise HTTPException(status_code=500, detail="Error interno")