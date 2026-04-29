import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Security, status

from app.core.auth import get_current_user
from app.core.responses import ok_response
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.pqr import PQROut
from app.models.user import UserOut

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Gestión de PQR"])


def _serialize_pqr(pqr: PQROut) -> dict:
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
        "categoria": pqr.categoria,
        "prioridad": pqr.prioridad,
        "estado": pqr.estado,
        "area_id": pqr.area_id,
        "usuario_id": pqr.usuario_id,
        "operador_id": pqr.operador_id,
        "supervisor_id": pqr.supervisor_id,
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

        if estado:
            results = [r for r in results if (r.estado or "").lower() == estado.lower()]
        if categoria:
            results = [r for r in results if (r.categoria or "").lower() == categoria.lower()]
        if prioridad:
            results = [r for r in results if (r.prioridad or "").lower() == prioridad.lower()]
        if area_id is not None:
            results = [r for r in results if r.area_id == area_id]
        if usuario_id is not None:
            results = [r for r in results if r.usuario_id == usuario_id]
        if search:
            s = search.lower()
            results = [
                r
                for r in results
                if s in (r.titulo or "").lower() or s in (r.descripcion or "").lower()
            ]

        data = [_serialize_pqr(r) for r in sorted(results, key=lambda x: x.ID or 0, reverse=True)]
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
