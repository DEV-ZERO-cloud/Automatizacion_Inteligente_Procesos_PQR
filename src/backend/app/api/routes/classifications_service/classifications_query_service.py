import logging

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.responses import JSONResponse

from app.core.auth import get_current_user
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.classification import ClassificationOut, CategoryOut, PriorityOut

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Gestión de Clasificación"])


# ══════════════════════════════════════════════════════════════════════════════
#  6.2 GET /classifications
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/classifications")
async def get_all_classifications(
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "agente"]),
):
    try:
        results = controller.get_all(ClassificationOut)
        data = [r.to_dict() for r in results]
        return JSONResponse(content={"success": True, "data": data})
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Error interno")


# ══════════════════════════════════════════════════════════════════════════════
#  6.3 GET /classifications/{id}
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/classifications/{class_id}")
async def get_classification_by_id(
    class_id: int,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "agente", "usuario"]),
):
    try:
        obj: ClassificationOut = controller.get_by_id(ClassificationOut, class_id)
        if not obj:
            raise HTTPException(status_code=404, detail="No encontrada.")
        return JSONResponse(content={"success": True, "data": obj.to_dict()})
    except HTTPException: raise
    except Exception as exc: raise HTTPException(status_code=500, detail="Error interno")


# ══════════════════════════════════════════════════════════════════════════════
#  GET /classifications/pqr/{pqr_id} (De la imagen)
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/classifications/pqr/{pqr_id}")
async def get_classification_by_pqr(
    pqr_id: int,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "agente", "usuario"]),
):
    try:
        obj: ClassificationOut = controller.get_by_column(ClassificationOut, "pqr_id", pqr_id)
        if not obj:
            raise HTTPException(status_code=404, detail="No se encontró clasificación para esta PQR.")
        return JSONResponse(content={"success": True, "data": obj.to_dict()})
    except HTTPException: raise
    except Exception as exc: raise HTTPException(status_code=500, detail="Error interno")


# ══════════════════════════════════════════════════════════════════════════════
#  7.2 GET /categories
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/categories")
async def get_all_categories(
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "agente", "usuario"]),
):
    try:
        results = controller.get_all(CategoryOut)
        data = [r.to_dict() for r in results]
        return JSONResponse(content={"success": True, "data": data})
    except Exception as exc: raise HTTPException(status_code=500, detail="Error interno")

# ══════════════════════════════════════════════════════════════════════════════
#  7.3 GET /categories/{id}
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/categories/{cat_id}")
async def get_category_by_id(
    cat_id: int,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "agente", "usuario"]),
):
    try:
        obj: CategoryOut = controller.get_by_id(CategoryOut, cat_id)
        if not obj: raise HTTPException(status_code=404, detail="No encontrada")
        return JSONResponse(content={"success": True, "data": obj.to_dict()})
    except HTTPException: raise
    except Exception: raise HTTPException(status_code=500, detail="Error interno")


# ══════════════════════════════════════════════════════════════════════════════
#  8.2 GET /priorities
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/priorities")
async def get_all_priorities(
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "agente", "usuario"]),
):
    try:
        results = controller.get_all(PriorityOut)
        data = [r.to_dict() for r in results]
        return JSONResponse(content={"success": True, "data": data})
    except Exception as exc: raise HTTPException(status_code=500, detail="Error interno")

# ══════════════════════════════════════════════════════════════════════════════
#  8.3 GET /priorities/{id}
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/priorities/{prio_id}")
async def get_priority_by_id(
    prio_id: int,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "agente", "usuario"]),
):
    try:
        obj: PriorityOut = controller.get_by_id(PriorityOut, prio_id)
        if not obj: raise HTTPException(status_code=404, detail="No encontrada")
        return JSONResponse(content={"success": True, "data": obj.to_dict()})
    except HTTPException: raise
    except Exception: raise HTTPException(status_code=500, detail="Error interno")
