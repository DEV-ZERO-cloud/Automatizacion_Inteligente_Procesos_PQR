import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Security, status

from app.core.auth import get_current_user
from app.core.responses import ok_response
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.classification import CategoryOut, ClassificationOut, PriorityOut
from app.models.pqr import PQROut
from app.models.user import UserOut

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Gestión de PQR"])


def _serialize_pqr(pqr: PQROut) -> dict:
    classification: ClassificationOut | None = controller.get_by_column(ClassificationOut, "pqr_id", pqr.ID)

    category_name = None
    priority_name = None
    if classification:
        category = controller.get_by_id(CategoryOut, classification.categoria_id)
        priority = controller.get_by_id(PriorityOut, classification.prioridad_id)
        category_name = category.nombre if category else None
        priority_name = priority.nombre if priority else None

    user_name = None
    if pqr.usuario_id:
        user = controller.get_by_id(UserOut, int(pqr.usuario_id))
        user_name = user.nombre if user else None

    created_at: Any = pqr.created_at
    updated_at: Any = pqr.updated_at
    created_at = created_at.isoformat() if callable(getattr(created_at, "isoformat", None)) else created_at
    updated_at = updated_at.isoformat() if callable(getattr(updated_at, "isoformat", None)) else updated_at

    return {
        "id": pqr.ID,
        "titulo": pqr.titulo,
        "descripcion": pqr.descripcion,
        "tipo": pqr.tipo,
        "categoria": category_name,
        "prioridad": priority_name,
        "estado": pqr.estado,
        "area_id": pqr.area_id,
        "usuario_id": pqr.usuario_id,
        "operador_id": pqr.operador_id,
        "supervisor_id": pqr.supervisor_id,
        "clasificacion_id": pqr.clasificacion_id,
        "created_at": created_at,
        "updated_at": updated_at,
        "usuario_nombre": user_name,
    }


@router.get("/pqrs")
async def get_all_pqrs(
    estado: str | None = Query(default=None),
    categoria: str | None = Query(default=None),
    prioridad: str | None = Query(default=None),
    area_id: int | None = Query(default=None),
    usuario_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    current_user: dict = Security(
        get_current_user, scopes=["admin", "supervisor", "operador", "gerente", "agente", "usuario"]
    ),
):
    try:
        results = controller.get_all(PQROut)

        data = [_serialize_pqr(r) for r in sorted(results, key=lambda x: x.ID or 0, reverse=True)]

        if estado:
            data = [r for r in data if (r.get("estado") or "").lower() == estado.lower()]
        if categoria:
            data = [r for r in data if (r.get("categoria") or "").lower() == categoria.lower()]
        if prioridad:
            data = [r for r in data if (r.get("prioridad") or "").lower() == prioridad.lower()]
        if area_id is not None:
            data = [r for r in data if r.get("area_id") == area_id]
        if usuario_id is not None:
            data = [r for r in data if r.get("usuario_id") == usuario_id]
        if search:
            s = search.lower()
            data = [
                r
                for r in data
                if s in (r.get("titulo") or "").lower() or s in (r.get("descripcion") or "").lower()
            ]

        return ok_response(data=data, message="PQRs consultadas")
    except Exception as exc:
        logger.error("[GET /pqrs] Error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/pqrs/{pqr_id}")
async def get_pqr_by_id(
    pqr_id: int,
    current_user: dict = Security(
        get_current_user, scopes=["admin", "supervisor", "operador", "gerente", "agente", "usuario"]
    ),
):
    try:
        pqr = controller.get_by_id(PQROut, pqr_id)
        if not pqr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PQR no encontrada.")

        return ok_response(data=_serialize_pqr(pqr), message="PQR consultada")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[GET /pqrs/%s] Error: %s", pqr_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
