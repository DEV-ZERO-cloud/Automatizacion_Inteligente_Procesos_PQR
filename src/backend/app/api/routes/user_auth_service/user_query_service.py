import logging

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.responses import JSONResponse

from app.core.auth import get_current_user
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.user import UserOut

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Autenticación y Usuarios"])


# ══════════════════════════════════════════════════════════════════════════════
#  3.3 GET /users
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/users")
async def get_all_users(
    current_user: dict = Security(
        get_current_user, scopes=["admin", "supervisor", "agente", "usuario"]
    ),
):
    """
    Retorna la lista completa de usuarios registrados.

    Requiere token válido con cualquier scope autorizado.
    """
    try:
        logger.info("[GET /users] Consultando todos los usuarios.")
        users = controller.get_all(UserOut)

        data = [
            {
                "id": u.ID,
                "nombre": u.nombre,
                "correo": u.correo,
                "rol_id": u.rol_id,
                "area_id": u.area_id,
            }
            for u in users
        ]

        return JSONResponse(content={"success": True, "data": data})

    except Exception as exc:
        logger.error("[GET /users] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
#  3.4 GET /users/{id}
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/users/{user_id}")
async def get_user_by_id(
    user_id: int,
    current_user: dict = Security(
        get_current_user, scopes=["admin", "supervisor", "agente", "usuario"]
    ),
):
    """
    Retorna la información de un usuario específico por su ID.

    Requiere token válido con cualquier scope autorizado.
    """
    try:
        logger.info("[GET /users/%s] Consultando usuario.", user_id)

        user: UserOut = controller.get_by_id(UserOut, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado.",
            )

        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "id": user.ID,
                    "nombre": user.nombre,
                    "correo": user.correo,
                    "rol_id": user.rol_id,
                    "area_id": user.area_id,
                },
            }
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[GET /users/%s] Error: %s", user_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}")
