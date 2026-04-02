import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.responses import JSONResponse

from app.core.auth import get_current_user
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.organization import AreaOut
from app.models.pqr import PQRCreate, PQROut, PQRUpdate
from app.models.user import UserOut

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Gestión de PQR"])


def _ensure_related_entities(payload: PQRCreate | PQRUpdate):
    if payload.area_id is not None:
        area = controller.get_by_id(AreaOut, payload.area_id)
        if not area:
            raise HTTPException(status_code=404, detail="Área no encontrada.")

    if payload.usuario_id is not None:
        user = controller.get_by_id(UserOut, payload.usuario_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")


@router.post("/pqrs", response_model=PQROut, status_code=status.HTTP_201_CREATED)
async def create_pqr(
    payload: PQRCreate,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "agente", "usuario"]),
):
    try:
        _ensure_related_entities(payload)

        now = datetime.utcnow()
        data = payload.model_dump()
        data["created_at"] = data.get("created_at") or now
        data["updated_at"] = data.get("updated_at") or now
        to_create = PQRCreate(**data)

        created = controller.add(to_create)
        if not created:
            raise HTTPException(status_code=500, detail="No se pudo crear la PQR.")

        return JSONResponse(content={"success": True, "message": "PQR creada", "data": created.to_dict()})
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[POST /pqrs] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}")


@router.put("/pqrs/{pqr_id}", response_model=PQROut)
async def update_pqr(
    pqr_id: int,
    payload: PQRUpdate,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "agente"]),
):
    try:
        existing = controller.get_by_id(PQROut, pqr_id)
        if not existing:
            raise HTTPException(status_code=404, detail="PQR no encontrada.")

        _ensure_related_entities(payload)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing, field, value)

        existing.updated_at = datetime.utcnow()

        updated = controller.update(existing)
        if not updated:
            raise HTTPException(status_code=500, detail="No se pudo actualizar la PQR.")

        return JSONResponse(content={"success": True, "message": "PQR actualizada", "data": updated.to_dict()})
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[PUT /pqrs/%s] Error: %s", pqr_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}")


@router.delete("/pqrs/{pqr_id}")
async def delete_pqr(
    pqr_id: int,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor"]),
):
    try:
        existing = controller.get_by_id(PQROut, pqr_id)
        if not existing:
            raise HTTPException(status_code=404, detail="PQR no encontrada.")

        deleted = controller.delete(existing)
        if not deleted:
            raise HTTPException(status_code=500, detail="No se pudo eliminar la PQR.")

        return JSONResponse(content={"success": True, "message": "PQR eliminada"})
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[DELETE /pqrs/%s] Error: %s", pqr_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}")
