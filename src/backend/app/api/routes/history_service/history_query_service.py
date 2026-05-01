import logging

from fastapi import APIRouter, HTTPException, Security, status

from app.core.auth import get_current_user
from app.core.responses import ok_response
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.history import HistoryOut

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Historial"])


# ══════════════════════════════════════════════════════════════════════════════
#  GET /historial
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/historial", status_code=status.HTTP_200_OK)
async def list_history(
    current_user: dict = Security(get_current_user, scopes=["agente", "supervisor", "operador", "admin"]),
):
    """Retorna todo el historial registrado."""
    try:
        logger.info("[GET /historial] Listando historial")
        history = controller.get_all(HistoryOut)
        return ok_response(
            data=[h.to_dict() for h in history],
            message="Historial consultado",
            status_code=status.HTTP_200_OK,
        )
    except Exception as exc:
        logger.error("[GET /historial] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ══════════════════════════════════════════════════════════════════════════════
#  GET /historial/{id}
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/historial/{history_id}", status_code=status.HTTP_200_OK)
async def get_history(
    history_id: int,
    current_user: dict = Security(get_current_user, scopes=["agente", "supervisor", "operador", "admin"]),
):
    """Retorna un evento específico del historial por ID."""
    try:
        logger.info("[GET /historial/%s]", history_id)
        event = controller.get_by_id(HistoryOut, history_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento no encontrado.",
            )
        return ok_response(
            data=event.to_dict(),
            message="Evento de historial consultado",
            status_code=status.HTTP_200_OK,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[GET /historial/%s] Error: %s", history_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ══════════════════════════════════════════════════════════════════════════════
#  GET /historial/pqr/{pqr_id}
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/historial/pqr/{pqr_id}", status_code=status.HTTP_200_OK)
async def get_history_by_pqr(
    pqr_id: int,
    current_user: dict = Security(get_current_user, scopes=["agente", "supervisor", "operador", "admin"]),
):
    """Retorna todo el historial asociado a una PQR específica."""
    try:
        logger.info("[GET /historial/pqr/%s] Buscando eventos", pqr_id)
        event = controller.get_by_column(HistoryOut, "pqr_id", pqr_id)
        if not event:
            return ok_response(data=[], message="Historial por PQR consultado", status_code=status.HTTP_200_OK)
        return ok_response(
            data=[event.to_dict()],
            message="Historial por PQR consultado",
            status_code=status.HTTP_200_OK,
        )
    except Exception as exc:
        logger.error("[GET /historial/pqr/%s] Error: %s", pqr_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
