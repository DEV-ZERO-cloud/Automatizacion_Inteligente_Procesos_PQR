import logging

from fastapi import APIRouter, HTTPException, Security, status

from app.core.auth import get_current_user
from app.core.responses import ok_response
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.file import FileCreate, FileOut, FileUpdate

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Archivos"])


# ══════════════════════════════════════════════════════════════════════════════
#  POST /archivos/create
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/archivos/create", status_code=status.HTTP_201_CREATED)
async def create_file(
    payload: FileCreate,
    current_user: dict = Security(get_current_user, scopes=["agente", "admin"]),
):
    """Crea un registro de archivo adjunto a una PQR."""
    try:
        logger.info("[POST /archivos/create] Creando archivo para PQR ID=%s", payload.pqr_id)

        controller.add(payload)
        logger.info("[POST /archivos/create] Archivo ID=%s creado.", payload.id)

        return ok_response(
            data={"id": payload.id},
            message="Archivo registrado",
            status_code=status.HTTP_201_CREATED,
        )

    except Exception as exc:
        logger.error("[POST /archivos/create] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ══════════════════════════════════════════════════════════════════════════════
#  PUT /archivos/update
# ══════════════════════════════════════════════════════════════════════════════
@router.put("/archivos/update")
async def update_file(
    payload: FileUpdate,
    current_user: dict = Security(get_current_user, scopes=["admin"]),
):
    """Actualiza metadatos de un archivo."""
    try:
        logger.info("[PUT /archivos/update] Actualizando archivo ID=%s", payload.id)

        existing = controller.get_by_id(FileOut, payload.id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Archivo no encontrado.",
            )

        # Actualizar solo campos proporcionados
        updated = FileOut(
            id=payload.id,
            pqr_id=existing.pqr_id,
            nombre=payload.nombre or existing.nombre,
            ruta=payload.ruta or existing.ruta,
            tipo=payload.tipo or existing.tipo,
            created_at=existing.created_at,
        )
        controller.update(updated)

        logger.info("[PUT /archivos/update] Archivo ID=%s actualizado.", payload.id)
        return ok_response(data=None, message="Archivo actualizado")

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[PUT /archivos/update] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ══════════════════════════════════════════════════════════════════════════════
#  DELETE /archivos/delete/{id}
# ══════════════════════════════════════════════════════════════════════════════
@router.delete("/archivos/delete/{file_id}")
async def delete_file(
    file_id: int,
    current_user: dict = Security(get_current_user, scopes=["admin"]),
):
    """Elimina un archivo del registro."""
    try:
        logger.info("[DELETE /archivos/delete/%s] Eliminando archivo.", file_id)

        existing = controller.get_by_id(FileOut, file_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Archivo no encontrado.",
            )

        controller.delete(existing)
        logger.info("[DELETE /archivos/delete/%s] Archivo eliminado.", file_id)
        return ok_response(data=None, message="Archivo eliminado")

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[DELETE /archivos/delete/%s] Error: %s", file_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
