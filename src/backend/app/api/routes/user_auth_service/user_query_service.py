import logging

from fastapi import APIRouter, HTTPException, Security, status

from app.core.auth import get_current_user
from app.core.responses import ok_response
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
                "id": u.id,
                "nombre": u.nombre,
                "correo": u.correo,
                "rol_id": u.rol_id,
                "area_id": u.area_id,
            }
            for u in users
        ]

        return ok_response(data=data, message="Usuarios consultados")

    except Exception as exc:
        logger.error("[GET /users] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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

        user = controller.get_by_id(UserOut, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado.",
            )

        return ok_response(
            data={
                "id": user.id,
                "nombre": user.nombre,
                "correo": user.correo,
                "rol_id": user.rol_id,
                "area_id": user.area_id,
            },
            message="Usuario consultado",
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[GET /users/%s] Error: %s", user_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ══════════════════════════════════════════════════════════════════════════════
#  3.5 GET /supervisors
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/supervisors")
async def get_all_supervisors(
    current_user: dict = Security(
        get_current_user, scopes=["admin", "supervisor", "agente", "usuario"]
    ),
):
    """
    Retorna la lista de supervisores disponibles (usuarios con rol_id=2).

    Requiere token válido con cualquier scope autorizado.
    """
    try:
        logger.info("[GET /supervisors] Consultando supervisores disponibles.")
        all_users = controller.get_all(UserOut)
        logger.info(f"[GET /supervisors] Total usuarios: {len(all_users)}")

        supervisors = []
        for u in all_users:
            logger.info(f"[GET /supervisors] Usuario: {u.nombre}, rol_id: {u.rol_id} (tipo: {type(u.rol_id)})")
            if u.rol_id == 2:
                supervisors.append({
                    "id": u.id,
                    "nombre": u.nombre,
                    "correo": u.correo,
                    "rol_id": u.rol_id,
                })

        logger.info(f"[GET /supervisors] Supervisores encontrados: {len(supervisors)}")
        return ok_response(data=supervisors, message="Supervisores consultados")

    except Exception as exc:
        logger.error("[GET /supervisors] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
