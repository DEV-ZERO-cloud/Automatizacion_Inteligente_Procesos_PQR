import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Security, status
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.responses import ok_response
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.organization import AreaOut
from app.models.pqr import PQRCreate, PQROut, PQRUpdate
from app.models.user import UserOut
from app.models.history import HistoryCreate

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Gestión de PQR"])


class PQRAsignarPayload(BaseModel):
    supervisor_id: int


class PQRClasificarPayload(BaseModel):
    categoria: str
    prioridad: str
    comentario: str | None = None


class PQRResolverPayload(BaseModel):
    respuesta: str


class PQRCerrarPayload(BaseModel):
    confirmacion: bool = True


def _ensure_related_entities(payload: PQRCreate | PQRUpdate):
    if payload.area_id is not None:
        area = controller.get_by_id(AreaOut, payload.area_id)
        if not area:
            raise HTTPException(status_code=404, detail="Área no encontrada.")

    if payload.usuario_id is not None:
        user = controller.get_by_id(UserOut, payload.usuario_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")


def _add_history(pqr_id: int, usuario_id: int | None, accion: str, detalle: str | None = None):
    """Genera automáticamente una entrada en el historial."""
    try:
        history_entry = HistoryCreate(
            pqr_id=pqr_id,
            usuario_id=usuario_id,
            accion=accion,
            detalle=detalle
        )
        controller.add(history_entry)
    except Exception as e:
        logger.warning(f"[Historial] No se pudo registrar la acción: {e}")


def _current_user_id(current_user: dict) -> int | None:
    sub = current_user.get("sub")
    if sub is None:
        return None
    try:
        return int(sub)
    except (TypeError, ValueError):
        return None


@router.post("/pqrs", response_model=PQROut, status_code=status.HTTP_201_CREATED)
async def create_pqr(
    payload: PQRCreate,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "operador", "agente", "usuario"]),
):
    try:
        _ensure_related_entities(payload)

        now = datetime.utcnow()
        data = payload.model_dump()
        data["created_at"] = data.get("created_at") or now
        data["updated_at"] = data.get("updated_at") or now
        data["estado"] = data.get("estado") or "pendiente"
        to_create = PQRCreate(**data)

        created = controller.add(to_create)
        if not created:
            raise HTTPException(status_code=500, detail="No se pudo crear la PQR.")

        user_id = _current_user_id(current_user)
        _add_history(created.ID, user_id, "PQR creada", f"Tipo: {created.tipo}, Título: {created.titulo}")

        return ok_response(data=created.to_dict(), message="PQR creada", status_code=201)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[POST /pqrs] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.put("/pqrs/{pqr_id}", response_model=PQROut)
async def update_pqr(
    pqr_id: int,
    payload: PQRUpdate,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "operador", "agente"]),
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

        return ok_response(data=updated.to_dict(), message="PQR actualizada")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[PUT /pqrs/%s] Error: %s", pqr_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.delete("/pqrs/{pqr_id}")
async def delete_pqr(
    pqr_id: int,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "operador"]),
):
    try:
        existing = controller.get_by_id(PQROut, pqr_id)
        if not existing:
            raise HTTPException(status_code=404, detail="PQR no encontrada.")

        deleted = controller.delete(existing)
        if not deleted:
            raise HTTPException(status_code=500, detail="No se pudo eliminar la PQR.")

        return ok_response(data=None, message="PQR eliminada")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[DELETE /pqrs/%s] Error: %s", pqr_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.put("/pqrs/{pqr_id}/asignar")
async def asignar_pqr(
    pqr_id: int,
    payload: PQRAsignarPayload,
    current_user: dict = Security(get_current_user, scopes=["admin"]),
):
    """Admin: Asigna una PQR a un supervisor."""
    try:
        existing = controller.get_by_id(PQROut, pqr_id)
        if not existing:
            raise HTTPException(status_code=404, detail="PQR no encontrada.")

        supervisor = controller.get_by_id(UserOut, payload.supervisor_id)
        if not supervisor:
            raise HTTPException(status_code=404, detail="Supervisor no encontrado.")

        if supervisor.rol_id != 2:
            raise HTTPException(status_code=400, detail="El usuario seleccionado no es un supervisor.")

        existing.supervisor_id = payload.supervisor_id
        existing.updated_at = datetime.utcnow()

        updated = controller.update(existing)
        if not updated:
            raise HTTPException(status_code=500, detail="No se pudo asignar la PQR.")

        user_id = _current_user_id(current_user)
        _add_history(pqr_id, user_id, "PQR asignada", f"Asignada al supervisor ID: {payload.supervisor_id}")

        return ok_response(data=updated.to_dict(), message="PQR asignada")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[PUT /pqrs/%s/asignar] Error: %s", pqr_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.put("/pqrs/{pqr_id}/clasificar")
async def clasificar_pqr(
    pqr_id: int,
    payload: PQRClasificarPayload,
    current_user: dict = Security(get_current_user, scopes=["supervisor", "operador"]),
):
    """Supervisor: Clasifica una PQR (categoría y prioridad)."""
    try:
        existing = controller.get_by_id(PQROut, pqr_id)
        if not existing:
            raise HTTPException(status_code=404, detail="PQR no encontrada.")

        existing.categoria = payload.categoria
        existing.prioridad = payload.prioridad
        existing.estado = "en_proceso"
        existing.updated_at = datetime.utcnow()

        updated = controller.update(existing)
        if not updated:
            raise HTTPException(status_code=500, detail="No se pudo clasificar la PQR.")

        user_id = _current_user_id(current_user)
        detalle = f"Categoría: {payload.categoria}, Prioridad: {payload.prioridad}"
        if payload.comentario:
            detalle += f". Comentario: {payload.comentario}"
        _add_history(pqr_id, user_id, "PQR clasificada", detalle)

        return ok_response(data=updated.to_dict(), message="PQR clasificada")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[PUT /pqrs/%s/clasificar] Error: %s", pqr_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.put("/pqrs/{pqr_id}/resolver")
async def resolver_pqr(
    pqr_id: int,
    payload: PQRResolverPayload,
    current_user: dict = Security(get_current_user, scopes=["supervisor", "operador"]),
):
    """Supervisor: Resuelve una PQR."""
    try:
        existing = controller.get_by_id(PQROut, pqr_id)
        if not existing:
            raise HTTPException(status_code=404, detail="PQR no encontrada.")

        existing.estado = "resuelta"
        existing.updated_at = datetime.utcnow()

        updated = controller.update(existing)
        if not updated:
            raise HTTPException(status_code=500, detail="No se pudo resolver la PQR.")

        user_id = _current_user_id(current_user)
        _add_history(pqr_id, user_id, "PQR resuelta", f"Respuesta: {payload.respuesta[:200]}...")

        return ok_response(data=updated.to_dict(), message="PQR resuelta")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[PUT /pqrs/%s/resolver] Error: %s", pqr_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.put("/pqrs/{pqr_id}/cerrar")
async def cerrar_pqr(
    pqr_id: int,
    payload: PQRCerrarPayload,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "operador", "usuario"]),
):
    """Usuario/Admin/Supervisor: Cierra una PQR."""
    try:
        existing = controller.get_by_id(PQROut, pqr_id)
        if not existing:
            raise HTTPException(status_code=404, detail="PQR no encontrada.")

        if existing.estado != "resuelta":
            raise HTTPException(status_code=400, detail="Solo se pueden cerrar PQRs resueltas.")

        existing.estado = "cerrada"
        existing.updated_at = datetime.utcnow()

        updated = controller.update(existing)
        if not updated:
            raise HTTPException(status_code=500, detail="No se pudo cerrar la PQR.")

        user_id = _current_user_id(current_user)
        _add_history(pqr_id, user_id, "PQR cerrada", "El usuario confirmó el cierre de la PQR")

        return ok_response(data=updated.to_dict(), message="PQR cerrada")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[PUT /pqrs/%s/cerrar] Error: %s", pqr_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
