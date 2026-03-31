import logging
from typing import Dict, List, Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── OAuth2 scheme ──────────────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    scopes={
        "admin": "Acceso total al sistema",
        "supervisor": "Supervisión de PQR y reportes",
        "agente": "Gestión y respuesta de PQR",
        "usuario": "Consulta y creación de PQR",
    },
)


# ── Token helpers ──────────────────────────────────────────────────────────────
def encode_token(payload: dict) -> str:
    """
    Codifica un JWT con el payload recibido.
    """
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(
    security_scopes: SecurityScopes,
    request: Request,
    token: str = Depends(oauth2_scheme),
) -> Dict[str, str]:
    """
    Extrae y valida el usuario autenticado desde un JWT.
    También verifica si el token tiene los scopes requeridos por la ruta.
    """
    token_cookie = request.cookies.get("access_token")
    if token_cookie:
        token = token_cookie.replace("Bearer ", "")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        user_id: str = payload.get("sub")
        scope: str = payload.get("scope")

        if user_id is None or scope is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o faltan campos requeridos",
            )

        # ── VALIDACIÓN REAL DE SCOPES ─────────────────────────────────────────
        if security_scopes.scopes:
            if scope not in security_scopes.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos suficientes para acceder a este recurso",
                )

        return {"sub": user_id, "scope": scope}

    except JWTError as e:
        logger.error("Error decoding token: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )


def verify_role(allowed_roles: List[str]) -> Callable:
    """
    Dependency para verificar si el usuario actual tiene uno de los roles permitidos.
    """

    def _verify(
        current_user: dict = Depends(get_current_user),
    ):
        user_scope = current_user.get("scope")

        if user_scope not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this route",
            )

        return current_user

    return _verify