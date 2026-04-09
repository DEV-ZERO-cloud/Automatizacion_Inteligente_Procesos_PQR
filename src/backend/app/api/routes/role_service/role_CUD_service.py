import logging

from fastapi import APIRouter, HTTPException, Security, status

from app.core.auth import get_current_user
from app.core.responses import ok_response
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.role import RoleCreate, RoleOut, RoleUpdate

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Roles"])


# ══════════════════════════════════════════════════════════════════════════════
#  POST /roles/create
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/roles/create", status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    current_user: dict = Security(get_current_user, scopes=["admin"]),
):
    """Crea un rol nuevo. Solo admin."""
    try:
        logger.info("[POST /roles/create] Creando rol: %s", payload.nombre)

        # Verificar duplicado
        existing = controller.get_by_column(RoleOut, "nombre", payload.nombre)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un rol con ese nombre.",
            )

        controller.add(payload)
        logger.info("[POST /roles/create] Rol ID=%s creado.", payload.id)

        return ok_response(
            data={"id": payload.id},
            message="Rol creado",
            status_code=status.HTTP_201_CREATED,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[POST /roles/create] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ══════════════════════════════════════════════════════════════════════════════
#  PUT /roles/update
# ══════════════════════════════════════════════════════════════════════════════
@router.put("/roles/update")
async def update_role(
    payload: RoleUpdate,
    current_user: dict = Security(get_current_user, scopes=["admin"]),
):
    """Actualiza un rol existente. Solo admin."""
    try:
        logger.info("[PUT /roles/update] Actualizando rol ID=%s", payload.id)

        existing = controller.get_by_id(RoleOut, payload.id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rol no encontrado.",
            )

        updated = RoleOut(id=payload.id, nombre=payload.nombre)
        controller.update(updated)

        logger.info("[PUT /roles/update] Rol ID=%s actualizado.", payload.id)
        return ok_response(data=None, message="Rol actualizado")

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[PUT /roles/update] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ══════════════════════════════════════════════════════════════════════════════
#  DELETE /roles/delete/{id}
# ══════════════════════════════════════════════════════════════════════════════
@router.delete("/roles/delete/{role_id}")
async def delete_role(
    role_id: int,
    current_user: dict = Security(get_current_user, scopes=["admin"]),
):
    """Elimina un rol. Solo admin."""
    try:
        logger.info("[DELETE /roles/delete/%s] Eliminando rol.", role_id)

        existing = controller.get_by_id(RoleOut, role_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rol no encontrado.",
            )

        controller.delete(existing)
        logger.info("[DELETE /roles/delete/%s] Rol eliminado.", role_id)
        return ok_response(data=None, message="Rol eliminado")

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[DELETE /roles/delete/%s] Error: %s", role_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
