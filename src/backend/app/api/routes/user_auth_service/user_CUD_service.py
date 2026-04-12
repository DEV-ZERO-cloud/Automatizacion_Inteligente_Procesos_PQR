import logging

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from pydantic import BaseModel, EmailStr, Field

from app.core.auth import encode_token, get_current_user
from app.core.responses import ok_response
from app.core.security import hash_password, is_password_hashed, verify_password
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


class RegisterRequest(BaseModel):
    identificacion: int = Field(..., gt=0)
    nombre: str = Field(..., min_length=3, max_length=120)
    correo: EmailStr
    telefono: str | None = Field(default=None, max_length=30)
    password: str = Field(..., min_length=8, max_length=128)


# ══════════════════════════════════════════════════════════════════════════════
#  3.1 POST /auth/login
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        logger.info("[POST /auth/login] Intento de inicio de sesión: %s", form_data.username)

        user = controller.get_by_column(UserOut, "correo", form_data.username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )

        if not user.activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo",
            )

        stored_password = user.contrasena or ""

        if is_password_hashed(stored_password):
            password_ok = verify_password(form_data.password, stored_password)
        else:
            password_ok = stored_password == form_data.password
            if password_ok:
                user.contrasena = hash_password(form_data.password)
                controller.update(user)

        if not password_ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )

        scope = ROLE_SCOPE_MAP.get(user.rol_id, "usuario")
        payload = {"sub": str(user.id), "scope": scope}
        token = encode_token(payload)

        logger.info("[POST /auth/login] Login exitoso user_id=%s scope=%s", user.id, scope)

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


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register_user(payload: RegisterRequest):
    try:
        logger.info("[POST /auth/register] Registro de usuario: %s", payload.correo)

        existing = controller.get_by_column(UserOut, "correo", payload.correo)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un usuario con ese correo.",
            )

        existing_identification = controller.get_by_column(UserOut, "identificacion", payload.identificacion)
        if existing_identification:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un usuario con esa identificación.",
            )

        users = controller.get_all(UserOut)
        next_id = (max((u.id for u in users), default=0) + 1) if users else 1

        user_to_create = UserCreate(
            id=next_id,
            identificacion=payload.identificacion,
            nombre=payload.nombre,
            correo=str(payload.correo),
            telefono=payload.telefono or "",
            contrasena=hash_password(payload.password),
            rol_id=4,
            area_id=3,
            activo=1,
        )
        controller.add(user_to_create)

        token = encode_token({"sub": str(next_id), "scope": "usuario"})

        return ok_response(
            data={
                "access_token": token,
                "token_type": "bearer",
                "user_id": next_id,
                "role": "usuario",
            },
            message="Usuario registrado exitosamente",
            status_code=status.HTTP_201_CREATED,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[POST /auth/register] Error interno: %s", exc, exc_info=True)
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

        payload_data = payload.model_dump()
        payload_data["contrasena"] = hash_password(payload_data["contrasena"])
        secure_payload = UserCreate(**payload_data)

        controller.add(secure_payload)
        logger.info("[POST /users/create] Usuario creado con ID=%s", payload.id)

        return ok_response(
            data={"id": payload.id},
            message="Usuario creado",
            status_code=status.HTTP_201_CREATED,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[POST /users/create] Error interno: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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

        existing = controller.get_by_id(UserOut, payload.id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado.",
            )

        # Actualizar campos
        updated = UserOut(
            id=payload.id,
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

        return ok_response(data=None, message="Usuario actualizado")

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[PUT /users/update] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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

        existing = controller.get_by_id(UserOut, user_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado.",
            )

        controller.delete(existing)
        logger.info("[DELETE /users/delete/%s] Usuario eliminado.", user_id)

        return ok_response(data=None, message="Usuario eliminado")

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[DELETE /users/delete/%s] Error: %s", user_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
