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
        "operador": "Supervisión de PQR sin acceso a reportes",
        "gerente": "Acceso exclusivo a reportes y métricas",
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

    logger.info("---- AUTH DEBUG ----")

    # Header Authorization
    auth_header = request.headers.get("authorization")
    logger.info("Authorization header: %s", auth_header)

    # Token inicial (lo que inyecta OAuth2)
    logger.info("Token from Depends: %s", token)

    # Cookie
    token_cookie = request.cookies.get("access_token")
    logger.info("Token from cookie: %s", token_cookie)

    # Si hay cookie, sobrescribe
    if token_cookie:
        if token_cookie.startswith("Bearer "):
            token = token_cookie.replace("Bearer ", "")
        else:
            token = token_cookie

    logger.info("Token final usado: %s", token)

    # Validación básica
    if not token or token == "undefined":
        logger.error("Token vacío o undefined")
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

        logger.info("Payload decodificado: %s", payload)

        user_id: Optional[str] = payload.get("sub")
        scope: Optional[str] = payload.get("scope")

        logger.info("User ID: %s | Scope: %s", user_id, scope)

        if user_id is None or scope is None:
            logger.error("Payload incompleto")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )

        # Validación de scopes
        if security_scopes.scopes:
            logger.info("Scopes requeridos: %s", security_scopes.scopes)

            if scope not in security_scopes.scopes:
                logger.error("Scope no autorizado")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos suficientes",
                )

        logger.info("AUTH OK")
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