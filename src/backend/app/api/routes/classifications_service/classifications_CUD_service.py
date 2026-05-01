import logging

from fastapi import APIRouter, HTTPException, Security, status

from app.core.auth import get_current_user
from app.core.responses import ok_response
from app.logic.universal_controller_instance import universal_controller as controller
from app.models.classification import (
    ClassificationCreate, ClassificationOut, ClassificationUpdate,
    CategoryCreate, CategoryOut, CategoryUpdate,
    PriorityCreate, PriorityOut, PriorityUpdate
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router = APIRouter(tags=["Gestión de Clasificación"])

# ══════════════════════════════════════════════════════════════════════════════
#  6.1 POST /classifications/create
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/classifications/create", status_code=status.HTTP_201_CREATED)
async def create_classification(
    payload: ClassificationCreate,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "operador", "agente"]),
):
    try:
        logger.info("[POST /classifications/create] Creando clasificación para PQR=%s", payload.pqr_id)
        
        # Verificar si la PQR ya tiene clasificación
        existing = controller.get_by_column(ClassificationOut, "pqr_id", payload.pqr_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta PQR ya tiene una clasificación asignada.",
            )

        controller.add(payload)
        return ok_response(
            data={"id": payload.id},
            message="Clasificación creada",
            status_code=status.HTTP_201_CREATED,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[POST /classifications/create] Error: %s", exc)
        raise HTTPException(status_code=500, detail="Error interno")


# ══════════════════════════════════════════════════════════════════════════════
#  6.4 POST /classifications/validate
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/classifications/validate")
async def validate_classification(
    payload: ClassificationUpdate,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "operador", "agente"]),
):
    try:
        logger.info("[POST /classifications/validate] Validando clasificación ID=%s", payload.id)
        
        existing: ClassificationOut | None = controller.get_by_id(ClassificationOut, payload.id)
        if not existing:
            raise HTTPException(status_code=404, detail="Clasificación no encontrada.")
        
        updated = ClassificationOut(
            id=payload.id,
            pqr_id=payload.pqr_id,
            modelo_version=payload.modelo_version,
            categoria_id=payload.categoria_id,
            prioridad_id=payload.prioridad_id,
            confianza=payload.confianza,
            origen="MANUAL",
            fue_corregida=True,
            validado_por=current_user.get("sub"),
            created_at=payload.created_at,
        )
        controller.update(updated)
        
        return ok_response(data=None, message="Clasificación validada")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[POST /classifications/validate] Error: %s", exc)
        raise HTTPException(status_code=500, detail="Error interno")


# ══════════════════════════════════════════════════════════════════════════════
#  6.5 PUT /classifications/update
# ══════════════════════════════════════════════════════════════════════════════
@router.put("/classifications/update")
async def update_classification(
    payload: ClassificationUpdate,
    current_user: dict = Security(get_current_user, scopes=["admin", "supervisor", "operador"]),
):
    try:
        logger.info("[PUT /classifications/update] Actualizando clasificación ID=%s", payload.id)
        existing: ClassificationOut | None = controller.get_by_id(ClassificationOut, payload.id)
        if not existing:
            raise HTTPException(status_code=404, detail="Clasificación no encontrada.")
        
        updated = ClassificationOut(**payload.model_dump())
        controller.update(updated)
        return ok_response(data=None, message="Clasificación actualizada")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[PUT /classifications/update] Error: %s", exc)
        raise HTTPException(status_code=500, detail="Error interno")


# ══════════════════════════════════════════════════════════════════════════════
#  6.6 DELETE /classifications/delete/{id}
# ══════════════════════════════════════════════════════════════════════════════
@router.delete("/classifications/delete/{class_id}")
async def delete_classification(
    class_id: int,
    current_user: dict = Security(get_current_user, scopes=["admin"]),
):
    try:
        logger.info("[DELETE /classifications/delete/%s] Eliminando", class_id)
        existing: ClassificationOut | None = controller.get_by_id(ClassificationOut, class_id)
        if not existing:
            raise HTTPException(status_code=404, detail="No encontrada.")
        
        controller.delete(existing)
        return ok_response(data=None, message="Clasificación eliminada")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Error interno")

# ══════════════════════════════════════════════════════════════════════════════
#  7.1 POST /categories/create
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/categories/create", status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    current_user: dict = Security(get_current_user, scopes=["admin"]),
):
    try:
        controller.add(payload)
        return ok_response(
            data={"id": payload.id},
            message="Categoría creada",
            status_code=status.HTTP_201_CREATED,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Error interno")

# ══════════════════════════════════════════════════════════════════════════════
#  7.4 PUT /categories/update
# ══════════════════════════════════════════════════════════════════════════════
@router.put("/categories/update")
async def update_category(
    payload: CategoryUpdate,
    current_user: dict = Security(get_current_user, scopes=["admin"]),
):
    try:
        existing: CategoryOut | None = controller.get_by_id(CategoryOut, payload.id)
        if not existing: raise HTTPException(status_code=404, detail="No encontrada")
        controller.update(CategoryOut(**payload.model_dump()))
        return ok_response(data=None, message="Categoría actualizada")
    except HTTPException: raise
    except Exception: raise HTTPException(status_code=500, detail="Error interno")

# ══════════════════════════════════════════════════════════════════════════════
#  7.5 DELETE /categories/delete/{id}
# ══════════════════════════════════════════════════════════════════════════════
@router.delete("/categories/delete/{cat_id}")
async def delete_category(
    cat_id: int,
    current_user: dict = Security(get_current_user, scopes=["admin"]),
):
    try:
        existing: CategoryOut | None = controller.get_by_id(CategoryOut, cat_id)
        if not existing: raise HTTPException(status_code=404, detail="No encontrada")
        controller.delete(existing)
        return ok_response(data=None, message="Categoría eliminada")
    except HTTPException: raise
    except Exception: raise HTTPException(status_code=500, detail="Error interno")

# ══════════════════════════════════════════════════════════════════════════════
#  8.1 POST /priorities/create
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/priorities/create", status_code=status.HTTP_201_CREATED)
async def create_priority(
    payload: PriorityCreate,
    current_user: dict = Security(get_current_user, scopes=["admin"]),
):
    try:
        controller.add(payload)
        return ok_response(
            data={"id": payload.id},
            message="Prioridad creada",
            status_code=status.HTTP_201_CREATED,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Error interno")

# ══════════════════════════════════════════════════════════════════════════════
#  8.4 PUT /priorities/update
# ══════════════════════════════════════════════════════════════════════════════
@router.put("/priorities/update")
async def update_priority(
    payload: PriorityUpdate,
    current_user: dict = Security(get_current_user, scopes=["admin"]),
):
    try:
        existing: PriorityOut | None = controller.get_by_id(PriorityOut, payload.id)
        if not existing: raise HTTPException(status_code=404, detail="No encontrada")
        controller.update(PriorityOut(**payload.model_dump()))
        return ok_response(data=None, message="Prioridad actualizada")
    except HTTPException: raise
    except Exception: raise HTTPException(status_code=500, detail="Error interno")

# ══════════════════════════════════════════════════════════════════════════════
#  8.5 DELETE /priorities/delete/{id}
# ══════════════════════════════════════════════════════════════════════════════
@router.delete("/priorities/delete/{prio_id}")
async def delete_priority(
    prio_id: int,
    current_user: dict = Security(get_current_user, scopes=["admin"]),
):
    try:
        existing: PriorityOut | None = controller.get_by_id(PriorityOut, prio_id)
        if not existing: raise HTTPException(status_code=404, detail="No encontrada")
        controller.delete(existing)
        return ok_response(data=None, message="Prioridad eliminada")
    except HTTPException: raise
    except Exception: raise HTTPException(status_code=500, detail="Error interno")
