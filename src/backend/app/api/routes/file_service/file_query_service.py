import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.responses import FileResponse

from app.core.auth import get_current_user
from app.core.responses import ok_response
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.file import FileOut

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Archivos"])

STORAGE_ROOT = Path(__file__).resolve().parents[4]


# ══════════════════════════════════════════════════════════════════════════════
#  GET /archivos
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/archivos", status_code=status.HTTP_200_OK)
async def list_files(
    current_user: dict = Security(get_current_user, scopes=["usuario", "agente", "supervisor", "admin"]),
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
    current_user: dict = Security(get_current_user, scopes=["usuario", "agente", "supervisor", "admin"]),
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


@router.get("/archivos/{file_id}/content")
async def get_file_content(
    file_id: int,
    current_user: dict = Security(get_current_user, scopes=["usuario", "agente", "supervisor", "admin"]),
):
    """Retorna el contenido binario del archivo para visualización o descarga."""
    try:
        file = controller.get_by_id(FileOut, file_id)
        if not file:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado.")

        if not file.ruta:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ruta de archivo no disponible.")

        disk_path = Path(file.ruta)
        if not disk_path.is_absolute():
            disk_path = STORAGE_ROOT / disk_path

        if not disk_path.exists() or not disk_path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo físico no encontrado.")

        media_type = file.tipo or "application/octet-stream"
        disposition = "inline" if (media_type.startswith("image/") or media_type == "application/pdf") else "attachment"

        return FileResponse(
            path=disk_path,
            media_type=media_type,
            filename=file.nombre,
            headers={"Content-Disposition": f'{disposition}; filename="{file.nombre}"'},
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[GET /archivos/%s/content] Error: %s", file_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ══════════════════════════════════════════════════════════════════════════════
#  GET /archivos/pqr/{pqr_id}
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/archivos/pqr/{pqr_id}", status_code=status.HTTP_200_OK)
async def get_files_by_pqr(
    pqr_id: int,
    current_user: dict = Security(get_current_user, scopes=["usuario", "agente", "supervisor", "admin"]),
):
    """Retorna todos los archivos asociados a una PQR específica."""
    try:
        logger.info("[GET /archivos/pqr/%s] Buscando archivos", pqr_id)
        files = controller.get_many_by_column(FileOut, "pqr_id", pqr_id)
        return ok_response(
            data=[file.to_dict() for file in files],
            message="Archivos por PQR consultados",
            status_code=status.HTTP_200_OK,
        )
    except Exception as exc:
        logger.error("[GET /archivos/pqr/%s] Error: %s", pqr_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
