"""
Pruebas Unitarias – Microservicio: Clasificaciones
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.models.classification import (
    ClassificationCreate, ClassificationOut, ClassificationUpdate,
    CategoryCreate, CategoryOut, CategoryUpdate,
    PriorityCreate, PriorityOut, PriorityUpdate
)

# Fixtures

@pytest.fixture
def admin_user():
    return {"sub": "1", "scope": "admin"}

@pytest.fixture
def supervisor_user():
    return {"sub": "2", "scope": "supervisor"}

@pytest.fixture
def operator_user():
    return {"sub": "3", "scope": "operador"}

@pytest.fixture
def agente_user():
    return {"sub": "4", "scope": "agente"}

@pytest.fixture
def category_mock():
    return CategoryOut(id=1, nombre="Petición")

@pytest.fixture
def priority_mock():
    return PriorityOut(id=1, nombre="Alta")

@pytest.fixture
def classification_mock():
    return ClassificationOut(
        id=1, pqr_id=10, modelo_version="v1", categoria_id=1, prioridad_id=1,
        confianza=0.9, origen="MANUAL", fue_corregida=False
    )

# ------------------------------------------------------------------------------
# CLASSIFICATIONS CUD
# ------------------------------------------------------------------------------
class TestClassificationsCUD:
    @pytest.mark.asyncio
    async def test_create_classification_ok(self, operator_user):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_column.return_value = None
            from app.api.routes.classifications_service.classifications_CUD_service import create_classification
            payload = ClassificationCreate(
                id=1, pqr_id=10, modelo_version="v1", categoria_id=1, prioridad_id=1,
                confianza=0.9, origen="AUTO", fue_corregida=False
            )
            result = await create_classification(payload, current_user=operator_user)
            content = json.loads(result.body.decode("utf-8"))
            assert content["success"] is True

    @pytest.mark.asyncio
    async def test_create_classification_duplicate(self, operator_user, classification_mock):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_column.return_value = classification_mock
            from app.api.routes.classifications_service.classifications_CUD_service import create_classification
            payload = ClassificationCreate(
                id=1, pqr_id=10, modelo_version="v1", categoria_id=1, prioridad_id=1,
                confianza=0.9, origen="AUTO", fue_corregida=False
            )
            with pytest.raises(HTTPException) as exc:
                await create_classification(payload, current_user=operator_user)
            assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_create_classification_500(self, operator_user):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_column.side_effect = Exception("DB")
            from app.api.routes.classifications_service.classifications_CUD_service import create_classification
            payload = ClassificationCreate(id=1, pqr_id=10, modelo_version="v1", categoria_id=1, prioridad_id=1, confianza=0.9, origen="AUTO", fue_corregida=False)
            with pytest.raises(HTTPException) as exc:
                await create_classification(payload, current_user=operator_user)
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_validate_classification_ok(self, admin_user, classification_mock):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = classification_mock
            from app.api.routes.classifications_service.classifications_CUD_service import validate_classification
            payload = ClassificationUpdate(id=1, pqr_id=10, modelo_version="v1", categoria_id=2, prioridad_id=2, confianza=1.0, origen="MANUAL", fue_corregida=True)
            result = await validate_classification(payload, current_user=admin_user)
            assert json.loads(result.body.decode("utf-8"))["success"] is True

    @pytest.mark.asyncio
    async def test_validate_classification_not_found(self, admin_user):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = None
            from app.api.routes.classifications_service.classifications_CUD_service import validate_classification
            payload = ClassificationUpdate(id=99, pqr_id=10, modelo_version="v1", categoria_id=2, prioridad_id=2, confianza=1.0, origen="MANUAL", fue_corregida=True)
            with pytest.raises(HTTPException) as exc:
                await validate_classification(payload, current_user=admin_user)
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_validate_classification_500(self, admin_user):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.side_effect = Exception("DB")
            from app.api.routes.classifications_service.classifications_CUD_service import validate_classification
            payload = ClassificationUpdate(id=1, pqr_id=10, modelo_version="v1", categoria_id=2, prioridad_id=2, confianza=1.0, origen="MANUAL", fue_corregida=True)
            with pytest.raises(HTTPException) as exc:
                await validate_classification(payload, current_user=admin_user)
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_update_classification_ok(self, supervisor_user, classification_mock):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = classification_mock
            from app.api.routes.classifications_service.classifications_CUD_service import update_classification
            payload = ClassificationUpdate(id=1, pqr_id=10, modelo_version="v1", categoria_id=1, prioridad_id=1, confianza=0.9, origen="MANUAL", fue_corregida=True)
            result = await update_classification(payload, current_user=supervisor_user)
            assert json.loads(result.body.decode("utf-8"))["success"] is True

    @pytest.mark.asyncio
    async def test_update_classification_not_found(self, supervisor_user):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = None
            from app.api.routes.classifications_service.classifications_CUD_service import update_classification
            payload = ClassificationUpdate(id=99, pqr_id=10, modelo_version="v1", categoria_id=1, prioridad_id=1, confianza=0.9, origen="MANUAL", fue_corregida=True)
            with pytest.raises(HTTPException) as exc:
                await update_classification(payload, current_user=supervisor_user)
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_classification_500(self, supervisor_user):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.side_effect = Exception("DB")
            from app.api.routes.classifications_service.classifications_CUD_service import update_classification
            payload = ClassificationUpdate(id=1, pqr_id=10, modelo_version="v1", categoria_id=1, prioridad_id=1, confianza=0.9, origen="MANUAL", fue_corregida=True)
            with pytest.raises(HTTPException) as exc:
                await update_classification(payload, current_user=supervisor_user)
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_delete_classification_ok(self, admin_user, classification_mock):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = classification_mock
            from app.api.routes.classifications_service.classifications_CUD_service import delete_classification
            result = await delete_classification(class_id=1, current_user=admin_user)
            assert json.loads(result.body.decode("utf-8"))["success"] is True

    @pytest.mark.asyncio
    async def test_delete_classification_not_found(self, admin_user):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = None
            from app.api.routes.classifications_service.classifications_CUD_service import delete_classification
            with pytest.raises(HTTPException) as exc:
                await delete_classification(class_id=99, current_user=admin_user)
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_classification_500(self, admin_user):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.side_effect = Exception("DB")
            from app.api.routes.classifications_service.classifications_CUD_service import delete_classification
            with pytest.raises(HTTPException) as exc:
                await delete_classification(class_id=1, current_user=admin_user)
            assert exc.value.status_code == 500

# ------------------------------------------------------------------------------
# CLASSIFICATIONS QUERY
# ------------------------------------------------------------------------------
class TestClassificationsQuery:
    @pytest.mark.asyncio
    async def test_get_all_classifications(self, admin_user, classification_mock):
        with patch("app.api.routes.classifications_service.classifications_query_service.controller") as mock_ctrl:
            mock_ctrl.get_all.return_value = [classification_mock]
            from app.api.routes.classifications_service.classifications_query_service import get_all_classifications
            result = await get_all_classifications(current_user=admin_user)
            assert json.loads(result.body.decode("utf-8"))["success"] is True

    @pytest.mark.asyncio
    async def test_get_all_classifications_empty(self, admin_user):
        with patch("app.api.routes.classifications_service.classifications_query_service.controller") as mock_ctrl:
            mock_ctrl.get_all.return_value = []
            from app.api.routes.classifications_service.classifications_query_service import get_all_classifications
            result = await get_all_classifications(current_user=admin_user)
            assert len(json.loads(result.body.decode("utf-8"))["data"]) == 0

    @pytest.mark.asyncio
    async def test_get_all_classifications_500(self, admin_user):
        with patch("app.api.routes.classifications_service.classifications_query_service.controller") as mock_ctrl:
            mock_ctrl.get_all.side_effect = Exception()
            from app.api.routes.classifications_service.classifications_query_service import get_all_classifications
            with pytest.raises(HTTPException) as exc:
                await get_all_classifications(current_user=admin_user)
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_classification_by_id_ok(self, operator_user, classification_mock):
        with patch("app.api.routes.classifications_service.classifications_query_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = classification_mock
            from app.api.routes.classifications_service.classifications_query_service import get_classification_by_id
            result = await get_classification_by_id(class_id=1, current_user=operator_user)
            assert json.loads(result.body.decode("utf-8"))["success"] is True

    @pytest.mark.asyncio
    async def test_get_classification_by_id_not_found(self, operator_user):
        with patch("app.api.routes.classifications_service.classifications_query_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = None
            from app.api.routes.classifications_service.classifications_query_service import get_classification_by_id
            with pytest.raises(HTTPException) as exc:
                await get_classification_by_id(class_id=99, current_user=operator_user)
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_classification_by_pqr_ok(self, operator_user, classification_mock):
        with patch("app.api.routes.classifications_service.classifications_query_service.controller") as mock_ctrl:
            mock_ctrl.get_by_column.return_value = classification_mock
            from app.api.routes.classifications_service.classifications_query_service import get_classification_by_pqr
            result = await get_classification_by_pqr(pqr_id=10, current_user=operator_user)
            assert json.loads(result.body.decode("utf-8"))["data"]["pqr_id"] == 10

    @pytest.mark.asyncio
    async def test_get_classification_by_pqr_not_found(self, operator_user):
        with patch("app.api.routes.classifications_service.classifications_query_service.controller") as mock_ctrl:
            mock_ctrl.get_by_column.return_value = None
            from app.api.routes.classifications_service.classifications_query_service import get_classification_by_pqr
            with pytest.raises(HTTPException) as exc:
                await get_classification_by_pqr(pqr_id=99, current_user=operator_user)
            assert exc.value.status_code == 404

# ------------------------------------------------------------------------------
# CATEGORIES CUD + QUERY
# ------------------------------------------------------------------------------
class TestCategories:
    @pytest.mark.asyncio
    async def test_create_category_ok(self, admin_user):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            from app.api.routes.classifications_service.classifications_CUD_service import create_category
            payload = CategoryCreate(id=1, nombre="Petición")
            result = await create_category(payload, current_user=admin_user)
            assert json.loads(result.body.decode("utf-8"))["success"] is True

    @pytest.mark.asyncio
    async def test_create_category_500(self, admin_user):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.add.side_effect = Exception()
            from app.api.routes.classifications_service.classifications_CUD_service import create_category
            payload = CategoryCreate(id=1, nombre="Petición")
            with pytest.raises(HTTPException) as exc:
                await create_category(payload, current_user=admin_user)
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_update_category_ok(self, admin_user, category_mock):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = category_mock
            from app.api.routes.classifications_service.classifications_CUD_service import update_category
            payload = CategoryUpdate(id=1, nombre="Queja")
            result = await update_category(payload, current_user=admin_user)
            assert json.loads(result.body.decode("utf-8"))["success"] is True

    @pytest.mark.asyncio
    async def test_update_category_not_found(self, admin_user):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = None
            from app.api.routes.classifications_service.classifications_CUD_service import update_category
            payload = CategoryUpdate(id=99, nombre="Queja")
            with pytest.raises(HTTPException) as exc:
                await update_category(payload, current_user=admin_user)
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_category_ok(self, admin_user, category_mock):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = category_mock
            from app.api.routes.classifications_service.classifications_CUD_service import delete_category
            result = await delete_category(cat_id=1, current_user=admin_user)
            assert json.loads(result.body.decode("utf-8"))["success"] is True

    @pytest.mark.asyncio
    async def test_delete_category_not_found(self, admin_user):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = None
            from app.api.routes.classifications_service.classifications_CUD_service import delete_category
            with pytest.raises(HTTPException) as exc:
                await delete_category(cat_id=99, current_user=admin_user)
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_all_categories(self, operator_user, category_mock):
        with patch("app.api.routes.classifications_service.classifications_query_service.controller") as mock_ctrl:
            mock_ctrl.get_all.return_value = [category_mock]
            from app.api.routes.classifications_service.classifications_query_service import get_all_categories
            result = await get_all_categories(current_user=operator_user)
            assert json.loads(result.body.decode("utf-8"))["success"] is True

    @pytest.mark.asyncio
    async def test_get_category_by_id_ok(self, operator_user, category_mock):
        with patch("app.api.routes.classifications_service.classifications_query_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = category_mock
            from app.api.routes.classifications_service.classifications_query_service import get_category_by_id
            result = await get_category_by_id(cat_id=1, current_user=operator_user)
            assert json.loads(result.body.decode("utf-8"))["success"] is True

    @pytest.mark.asyncio
    async def test_get_category_by_id_not_found(self, operator_user):
        with patch("app.api.routes.classifications_service.classifications_query_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = None
            from app.api.routes.classifications_service.classifications_query_service import get_category_by_id
            with pytest.raises(HTTPException) as exc:
                await get_category_by_id(cat_id=99, current_user=operator_user)
            assert exc.value.status_code == 404

# ------------------------------------------------------------------------------
# PRIORITIES CUD + QUERY
# ------------------------------------------------------------------------------
class TestPriorities:
    @pytest.mark.asyncio
    async def test_create_priority_ok(self, admin_user):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            from app.api.routes.classifications_service.classifications_CUD_service import create_priority
            payload = PriorityCreate(id=1, nombre="Alta")
            result = await create_priority(payload, current_user=admin_user)
            assert json.loads(result.body.decode("utf-8"))["success"] is True

    @pytest.mark.asyncio
    async def test_create_priority_500(self, admin_user):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.add.side_effect = Exception()
            from app.api.routes.classifications_service.classifications_CUD_service import create_priority
            payload = PriorityCreate(id=1, nombre="Alta")
            with pytest.raises(HTTPException) as exc:
                await create_priority(payload, current_user=admin_user)
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_update_priority_ok(self, admin_user, priority_mock):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = priority_mock
            from app.api.routes.classifications_service.classifications_CUD_service import update_priority
            payload = PriorityUpdate(id=1, nombre="Media")
            result = await update_priority(payload, current_user=admin_user)
            assert json.loads(result.body.decode("utf-8"))["success"] is True

    @pytest.mark.asyncio
    async def test_update_priority_not_found(self, admin_user):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = None
            from app.api.routes.classifications_service.classifications_CUD_service import update_priority
            payload = PriorityUpdate(id=99, nombre="Media")
            with pytest.raises(HTTPException) as exc:
                await update_priority(payload, current_user=admin_user)
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_priority_ok(self, admin_user, priority_mock):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = priority_mock
            from app.api.routes.classifications_service.classifications_CUD_service import delete_priority
            result = await delete_priority(prio_id=1, current_user=admin_user)
            assert json.loads(result.body.decode("utf-8"))["success"] is True

    @pytest.mark.asyncio
    async def test_delete_priority_not_found(self, admin_user):
        with patch("app.api.routes.classifications_service.classifications_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = None
            from app.api.routes.classifications_service.classifications_CUD_service import delete_priority
            with pytest.raises(HTTPException) as exc:
                await delete_priority(prio_id=99, current_user=admin_user)
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_all_priorities(self, operator_user, priority_mock):
        with patch("app.api.routes.classifications_service.classifications_query_service.controller") as mock_ctrl:
            mock_ctrl.get_all.return_value = [priority_mock]
            from app.api.routes.classifications_service.classifications_query_service import get_all_priorities
            result = await get_all_priorities(current_user=operator_user)
            assert json.loads(result.body.decode("utf-8"))["success"] is True

    @pytest.mark.asyncio
    async def test_get_priority_by_id_ok(self, operator_user, priority_mock):
        with patch("app.api.routes.classifications_service.classifications_query_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = priority_mock
            from app.api.routes.classifications_service.classifications_query_service import get_priority_by_id
            result = await get_priority_by_id(prio_id=1, current_user=operator_user)
            assert json.loads(result.body.decode("utf-8"))["success"] is True

    @pytest.mark.asyncio
    async def test_get_priority_by_id_not_found(self, operator_user):
        with patch("app.api.routes.classifications_service.classifications_query_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = None
            from app.api.routes.classifications_service.classifications_query_service import get_priority_by_id
            with pytest.raises(HTTPException) as exc:
                await get_priority_by_id(prio_id=99, current_user=operator_user)
            assert exc.value.status_code == 404

# ------------------------------------------------------------------------------
# CONTROL DE ACCESO
# ------------------------------------------------------------------------------
class TestClassificationAccessControl:
    def test_scope_agente_permitido_en_classifications(self):
        from app.core.auth import encode_token, get_current_user
        from fastapi.security import SecurityScopes
        token = encode_token({"sub": "4", "scope": "agente"})
        request = MagicMock()
        request.headers.get.return_value = None
        request.cookies.get.return_value = None
        result = get_current_user(SecurityScopes(scopes=["admin", "supervisor", "operador", "agente"]), request, token)
        assert result["scope"] == "agente"

    def test_scope_usuario_denegado_en_classifications(self):
        from app.core.auth import encode_token, get_current_user
        from fastapi.security import SecurityScopes
        token = encode_token({"sub": "5", "scope": "usuario"})
        request = MagicMock()
        request.headers.get.return_value = None
        request.cookies.get.return_value = None
        with pytest.raises(HTTPException) as exc:
            get_current_user(SecurityScopes(scopes=["admin", "supervisor", "operador", "agente"]), request, token)
        assert exc.value.status_code == 403
