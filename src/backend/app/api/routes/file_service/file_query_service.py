import logging

from fastapi import APIRouter, HTTPException, Security, status

from app.core.auth import get_current_user
from app.core.responses import ok_response
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.file import FileOut

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Archivos"])


# ══════════════════════════════════════════════════════════════════════════════
#  GET /archivos
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/archivos", status_code=status.HTTP_200_OK)
async def list_files(
    current_user: dict = Security(get_current_user, scopes=["agente", "supervisor", "admin"]),
):
    """Retorna todos los archivos registrados."""
    try:
        logger.info("[GET /archivos] Listando archivos")
        files = controller.get_all(FileOut)
        return ok_response(
            data=[f.to_dict() for f in files],
            message="Archivos consultados",
            status_code=status.HTTP_200_OK,
        )
    except Exception as exc:
        logger.error("[GET /archivos] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ══════════════════════════════════════════════════════════════════════════════
#  GET /archivos/{id}
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/archivos/{file_id}", status_code=status.HTTP_200_OK)
async def get_file(
    file_id: int,
    current_user: dict = Security(get_current_user, scopes=["agente", "supervisor", "admin"]),
):
    """Retorna un archivo específico por ID."""
    try:
        logger.info("[GET /archivos/%s]", file_id)
        file = controller.get_by_id(FileOut, file_id)
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Archivo no encontrado.",
            )
        return ok_response(
            data=file.to_dict(),
            message="Archivo consultado",
            status_code=status.HTTP_200_OK,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[GET /archivos/%s] Error: %s", file_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ══════════════════════════════════════════════════════════════════════════════
#  GET /archivos/pqr/{pqr_id}
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/archivos/pqr/{pqr_id}", status_code=status.HTTP_200_OK)
async def get_files_by_pqr(
    pqr_id: int,
    current_user: dict = Security(get_current_user, scopes=["agente", "supervisor", "admin"]),
):
    """Retorna todos los archivos asociados a una PQR específica."""
    try:
        logger.info("[GET /archivos/pqr/%s] Buscando archivos", pqr_id)
        file = controller.get_by_column(FileOut, "pqr_id", pqr_id)
        if not file:
            return ok_response(data=[], message="Archivos por PQR consultados", status_code=status.HTTP_200_OK)
        return ok_response(
            data=[file.to_dict()],
            message="Archivos por PQR consultados",
            status_code=status.HTTP_200_OK,
        )
    except Exception as exc:
        logger.error("[GET /archivos/pqr/%s] Error: %s", pqr_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
