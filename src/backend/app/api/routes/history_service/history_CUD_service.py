import logging

from fastapi import APIRouter, HTTPException, Security, status

from app.core.auth import get_current_user
from app.core.responses import ok_response
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.history import HistoryCreate, HistoryOut, HistoryUpdate

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Historial"])


# ══════════════════════════════════════════════════════════════════════════════
#  POST /historial/create
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/historial/create", status_code=status.HTTP_201_CREATED)
async def create_history(
    payload: HistoryCreate,
    current_user: dict = Security(get_current_user, scopes=["agente", "supervisor", "operador", "admin"]),
):
    """Registra un evento en el historial de una PQR."""
    try:
        logger.info("[POST /historial/create] Registrando acción para PQR ID=%s", payload.pqr_id)

        controller.add(payload)
        logger.info("[POST /historial/create] Evento ID=%s registrado.", payload.id)

        return ok_response(
            data={"id": payload.id},
            message="Historial registrado",
            status_code=status.HTTP_201_CREATED,
        )

    except Exception as exc:
        logger.error("[POST /historial/create] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ══════════════════════════════════════════════════════════════════════════════
#  PUT /historial/update
# ══════════════════════════════════════════════════════════════════════════════
@router.put("/historial/update")
async def update_history(
    payload: HistoryUpdate,
    current_user: dict = Security(get_current_user, scopes=["admin"]),
):
    """Actualiza un registro de historial."""
    try:
        logger.info("[PUT /historial/update] Actualizando evento ID=%s", payload.id)

        existing = controller.get_by_id(HistoryOut, payload.id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento no encontrado.",
            )

        # Actualizar solo campos proporcionados
        updated = HistoryOut(
            id=payload.id,
            pqr_id=existing.pqr_id,
            usuario_id=existing.usuario_id,
            accion=payload.accion or existing.accion,
            detalle=payload.detalle or existing.detalle,
            created_at=existing.created_at,
        )
        controller.update(updated)

        logger.info("[PUT /historial/update] Evento ID=%s actualizado.", payload.id)
        return ok_response(data=None, message="Historial actualizado")

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[PUT /historial/update] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ══════════════════════════════════════════════════════════════════════════════
#  DELETE /historial/delete/{id}
# ══════════════════════════════════════════════════════════════════════════════
@router.delete("/historial/delete/{history_id}")
async def delete_history(
    history_id: int,
    current_user: dict = Security(get_current_user, scopes=["admin"]),
):
    """Elimina un registro del historial."""
    try:
        logger.info("[DELETE /historial/delete/%s] Eliminando evento.", history_id)

        existing = controller.get_by_id(HistoryOut, history_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento no encontrado.",
            )

        controller.delete(existing)
        logger.info("[DELETE /historial/delete/%s] Evento eliminado.", history_id)
        return ok_response(data=None, message="Historial eliminado")

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[DELETE /historial/delete/%s] Error: %s", history_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
