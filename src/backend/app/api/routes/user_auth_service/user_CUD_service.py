import logging

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

from app.core.auth import encode_token, get_current_user
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.user import UserCreate, UserOut, UserUpdate

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Autenticación y Usuarios"])

# ── Mapa de roles ──────────────────────────────────────────────────────────────
ROLE_SCOPE_MAP: dict = {
    1: "admin",
    2: "supervisor",
    3: "agente",
    4: "usuario",
}


# ══════════════════════════════════════════════════════════════════════════════
#  3.1 POST /auth/login
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        logger.info("[POST /auth/login] Intento de inicio de sesión: %s", form_data.username)

        user: UserOut = controller.get_by_column(UserOut, "correo", form_data.username)

        if not user:
            logger.warning("[POST /auth/login] Usuario no encontrado: %s", form_data.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )

        if user.activo != 1:
            logger.warning("[POST /auth/login] Usuario inactivo: %s", form_data.username)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo. Contacte al administrador.",
            )

        if user.contrasena != form_data.password:
            logger.warning("[POST /auth/login] Contraseña incorrecta para: %s", form_data.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )

        scope = ROLE_SCOPE_MAP.get(user.rol_id, "usuario")
        payload = {"sub": str(user.id), "scope": scope}
        token = encode_token(payload)

        logger.info("[POST /auth/login] Login exitoso para user_id=%s scope=%s", user.id, scope)

        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
            "role": scope
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[POST /auth/login] Error interno: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# ══════════════════════════════════════════════════════════════════════════════
#  3.2 POST /users/create
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/users/create", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor"]),
):
    """
    Crea un nuevo usuario en el sistema.

    Requiere token con scope **admin** o **supervisor**.
    """
    try:
        logger.info("[POST /users/create] Creando usuario con correo: %s", payload.correo)

        # Verificar duplicado por correo
        existing = controller.get_by_column(UserOut, "correo", payload.correo)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un usuario con ese correo.",
            )

        # Verificar duplicado por identificación
        existing_id = controller.get_by_column(UserOut, "identificacion", payload.identificacion)
        if existing_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un usuario con esa identificación.",
            )

        controller.add(payload)
        logger.info("[POST /users/create] Usuario creado con ID=%s", payload.id)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "message": "Usuario creado",
                "data": {"id": payload.id},
            },
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[POST /users/create] Error interno: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
#  3.5 PUT /users/update
# ══════════════════════════════════════════════════════════════════════════════
@router.put("/users/update")
async def update_user(
    payload: UserUpdate,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "agente", "usuario"]),
):
    """
    Actualiza los datos de un usuario existente.

    Requiere token válido.
    """
    try:
        logger.info("[PUT /users/update] Actualizando usuario ID=%s", payload.id)

        existing: UserOut = controller.get_by_id(UserOut, payload.id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado.",
            )

        # Actualizar campos
        updated = UserOut(
            ID=payload.id,
            identificacion=existing.identificacion,
            nombre=payload.nombre,
            correo=payload.correo,
            telefono=payload.telefono,
            rol_id=payload.rol_id,
            area_id=payload.area_id,
            activo=existing.activo,
            contrasena=existing.contrasena,
        )
        controller.update(updated)

        logger.info("[PUT /users/update] Usuario ID=%s actualizado.", payload.id)

        return JSONResponse(
            content={"success": True, "message": "Usuario actualizado"}
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[PUT /users/update] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
#  3.6 DELETE /users/delete/{id}
# ══════════════════════════════════════════════════════════════════════════════
@router.delete("/users/delete/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Security(get_current_user, scopes=["admin"]),
):
    """
    Elimina un usuario del sistema.

    Requiere token con scope **admin**.
    """
    try:
        logger.info("[DELETE /users/delete/%s] Eliminando usuario.", user_id)

        existing: UserOut = controller.get_by_id(UserOut, user_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado.",
            )

        controller.delete(existing)
        logger.info("[DELETE /users/delete/%s] Usuario eliminado.", user_id)

        return JSONResponse(
            content={"success": True, "message": "Usuario eliminado"}
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[DELETE /users/delete/%s] Error: %s", user_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}")
