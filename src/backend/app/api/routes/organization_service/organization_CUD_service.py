import logging

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.responses import JSONResponse

from app.core.auth import get_current_user
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.organization import AreaCreate, AreaOut, AreaUpdate

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Organizacional"])

# ══════════════════════════════════════════════════════════════════════════════
#  4.1 POST /areas/create
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/areas/create", status_code=status.HTTP_201_CREATED)
async def create_area(
    payload: AreaCreate,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor"]),
):
    """
    Crea un área nueva en el sistema.

    Requiere token con scope **admin** o **supervisor**.
    """
    try:
        logger.info("[POST /areas/create] Creando área con nombre: %s", payload.nombre)

        # Verificar duplicado
        existing_area = controller.get_by_column(AreaOut, "nombre", payload.nombre)
        if existing_area:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un área con ese nombre.",
            )

        controller.add(payload)
        logger.info("[POST /areas/create] Área creada con ID=%s", payload.id)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "message": "Área creada",
                "data": {"id": payload.id},
            },
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[POST /areas/create] Error interno: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
#  4.4 PUT /areas/update
# ══════════════════════════════════════════════════════════════════════════════
@router.put("/areas/update")
async def update_area(
    payload: AreaUpdate,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor"]),
):
    """
    Actualiza los datos de un área existente.

    Requiere token con scope **admin** o **supervisor**.
    """
    try:
        logger.info("[PUT /areas/update] Actualizando área ID=%s", payload.id)

        existing: AreaOut = controller.get_by_id(AreaOut, payload.id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Área no encontrada.",
            )

        # Actualizar campos
        updated = AreaOut(
            id=payload.id,
            nombre=payload.nombre,
            descripcion=payload.descripcion,
        )
        controller.update(updated)

        logger.info("[PUT /areas/update] Área ID=%s actualizada.", payload.id)

        return JSONResponse(
            content={"success": True, "message": "Área actualizada"}
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[PUT /areas/update] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
#  4.5 DELETE /areas/delete/{id}
# ══════════════════════════════════════════════════════════════════════════════
@router.delete("/areas/delete/{area_id}")
async def delete_area(
    area_id: int,
    current_user: dict = Security(get_current_user, scopes=["admin"]),
):
    """
    Elimina un área del sistema.

    Requiere token con scope **admin**.
    """
    try:
        logger.info("[DELETE /areas/delete/%s] Eliminando área.", area_id)

        existing: AreaOut = controller.get_by_id(AreaOut, area_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Área no encontrada.",
            )

        controller.delete(existing)
        logger.info("[DELETE /areas/delete/%s] Área eliminada.", area_id)

        return JSONResponse(
            content={"success": True, "message": "Área eliminada"}
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[DELETE /areas/delete/%s] Error: %s", area_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}")
