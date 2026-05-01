import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Security, UploadFile, status

from app.core.auth import get_current_user
from app.core.responses import ok_response
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.file import FileCreate, FileOut, FileUpdate
from app.models.pqr import PQROut

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Archivos"])

STORAGE_ROOT = Path(__file__).resolve().parents[4]
UPLOADS_DIR = STORAGE_ROOT / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
#  POST /archivos/create
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/archivos/create", status_code=status.HTTP_201_CREATED)
async def create_file(
    payload: FileCreate,
    current_user: dict = Security(get_current_user, scopes=["usuario", "agente", "admin"]),
):
    """Crea un registro de archivo adjunto a una PQR."""
    try:
        logger.info("[POST /archivos/create] Creando archivo para PQR ID=%s", payload.pqr_id)

        pqr = controller.get_by_id(PQROut, payload.pqr_id)
        if not pqr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PQR no encontrada.")

        created = controller.add(payload)
        logger.info("[POST /archivos/create] Archivo ID=%s creado.", created.id)

        return ok_response(
            data=created.to_dict(),
            message="Archivo registrado",
            status_code=status.HTTP_201_CREATED,
        )

    except Exception as exc:
        logger.error("[POST /archivos/create] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/archivos/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    pqr_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Security(get_current_user, scopes=["usuario", "agente", "admin"]),
):
    """Sube un archivo al disco y registra sus metadatos asociados a una PQR."""
    try:
        pqr = controller.get_by_id(PQROut, pqr_id)
        if not pqr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PQR no encontrada.")

        original_name = (file.filename or "").strip()
        if not original_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nombre de archivo inválido.")

        suffix = Path(original_name).suffix.lower()
        generated_name = f"{uuid4().hex}{suffix}"
        disk_path = UPLOADS_DIR / generated_name

        content = await file.read()
        disk_path.write_bytes(content)

        relative_path = Path("uploads") / generated_name
        created = controller.add(
            FileCreate(
                pqr_id=pqr_id,
                nombre=original_name,
                ruta=relative_path.as_posix(),
                tipo=file.content_type or "application/octet-stream",
            )
        )

        logger.info("[POST /archivos/upload] Archivo ID=%s guardado para PQR=%s", created.id, pqr_id)
        return ok_response(
            data=created.to_dict(),
            message="Archivo subido",
            status_code=status.HTTP_201_CREATED,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[POST /archivos/upload] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    finally:
        await file.close()


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

        if existing.ruta:
            disk_path = Path(existing.ruta)
            if not disk_path.is_absolute():
                disk_path = STORAGE_ROOT / disk_path
            if disk_path.exists() and disk_path.is_file():
                disk_path.unlink()

        controller.delete(existing)
        logger.info("[DELETE /archivos/delete/%s] Archivo eliminado.", file_id)
        return ok_response(data=None, message="Archivo eliminado")

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[DELETE /archivos/delete/%s] Error: %s", file_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
