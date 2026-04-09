import logging

from fastapi import APIRouter, HTTPException, Security, status

from app.core.auth import get_current_user
from app.core.responses import ok_response
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.role import RoleOut

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Roles"])


# ══════════════════════════════════════════════════════════════════════════════
#  GET /roles
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/roles", status_code=status.HTTP_200_OK)
async def list_roles(
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "agente"]),
):
    """Retorna todos los roles disponibles."""
    try:
        logger.info("[GET /roles] Listando roles")
        roles = controller.get_all(RoleOut)
        return ok_response(
            data=[r.to_dict() for r in roles],
            message="Roles consultados",
            status_code=status.HTTP_200_OK,
        )
    except Exception as exc:
        logger.error("[GET /roles] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ══════════════════════════════════════════════════════════════════════════════
#  GET /roles/{id}
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/roles/{role_id}", status_code=status.HTTP_200_OK)
async def get_role(
    role_id: int,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "agente"]),
):
    """Retorna un rol específico por ID."""
    try:
        logger.info("[GET /roles/%s]", role_id)
        role = controller.get_by_id(RoleOut, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rol no encontrado.",
            )
        return ok_response(
            data=role.to_dict(),
            message="Rol consultado",
            status_code=status.HTTP_200_OK,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[GET /roles/%s] Error: %s", role_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
