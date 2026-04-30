"""
Pruebas Unitarias – Microservicio: Organizacional
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.models.organization import AreaCreate, AreaOut, AreaUpdate

# Fixtures

@pytest.fixture
def admin_user():
    return {"sub": "1", "scope": "admin"}

@pytest.fixture
def supervisor_user():
    return {"sub": "2", "scope": "supervisor"}

@pytest.fixture
def operador_user():
    return {"sub": "3", "scope": "operador"}

@pytest.fixture
def agente_user():
    return {"sub": "4", "scope": "agente"}

@pytest.fixture
def usuario_user():
    return {"sub": "5", "scope": "usuario"}

@pytest.fixture
def area_mock():
    return AreaOut(id=1, nombre="Soporte", descripcion="Soporte técnico")

# ------------------------------------------------------------------------------
# POST /areas/create
# ------------------------------------------------------------------------------
class TestCreateArea:
    @pytest.mark.asyncio
    async def test_create_area_ok(self, admin_user):
        with patch("app.api.routes.organization_service.organization_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_column.return_value = None
            from app.api.routes.organization_service.organization_CUD_service import create_area
            payload = AreaCreate(id=1, nombre="Soporte", descripcion="Soporte técnico")
            result = await create_area(payload, current_user=admin_user)
            content = json.loads(result.body.decode("utf-8"))
            assert content["success"] is True
            assert content["data"]["id"] == 1
            assert mock_ctrl.add.called

    @pytest.mark.asyncio
    async def test_create_area_duplicate(self, admin_user, area_mock):
        with patch("app.api.routes.organization_service.organization_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_column.return_value = area_mock
            from app.api.routes.organization_service.organization_CUD_service import create_area
            payload = AreaCreate(id=1, nombre="Soporte", descripcion="Soporte técnico")
            with pytest.raises(HTTPException) as exc:
                await create_area(payload, current_user=admin_user)
            assert exc.value.status_code == 400
            assert "Ya existe" in exc.value.detail

    @pytest.mark.asyncio
    async def test_create_area_500(self, admin_user):
        with patch("app.api.routes.organization_service.organization_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_column.side_effect = Exception("DB Crash")
            from app.api.routes.organization_service.organization_CUD_service import create_area
            payload = AreaCreate(id=1, nombre="Soporte", descripcion="Soporte técnico")
            with pytest.raises(HTTPException) as exc:
                await create_area(payload, current_user=admin_user)
            assert exc.value.status_code == 500

# ------------------------------------------------------------------------------
# PUT /areas/update
# ------------------------------------------------------------------------------
class TestUpdateArea:
    @pytest.mark.asyncio
    async def test_update_area_ok(self, supervisor_user, area_mock):
        with patch("app.api.routes.organization_service.organization_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = area_mock
            from app.api.routes.organization_service.organization_CUD_service import update_area
            payload = AreaUpdate(id=1, nombre="Soporte Mod", descripcion="Desc mod")
            result = await update_area(payload, current_user=supervisor_user)
            content = json.loads(result.body.decode("utf-8"))
            assert content["success"] is True
            assert mock_ctrl.update.called

    @pytest.mark.asyncio
    async def test_update_area_not_found(self, supervisor_user):
        with patch("app.api.routes.organization_service.organization_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = None
            from app.api.routes.organization_service.organization_CUD_service import update_area
            payload = AreaUpdate(id=99, nombre="Nada", descripcion="Nada")
            with pytest.raises(HTTPException) as exc:
                await update_area(payload, current_user=supervisor_user)
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_area_500(self, supervisor_user, area_mock):
        with patch("app.api.routes.organization_service.organization_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.side_effect = Exception("DB Error")
            from app.api.routes.organization_service.organization_CUD_service import update_area
            payload = AreaUpdate(id=1, nombre="Soporte Mod", descripcion="Desc mod")
            with pytest.raises(HTTPException) as exc:
                await update_area(payload, current_user=supervisor_user)
            assert exc.value.status_code == 500

# ------------------------------------------------------------------------------
# DELETE /areas/delete/{id}
# ------------------------------------------------------------------------------
class TestDeleteArea:
    @pytest.mark.asyncio
    async def test_delete_area_ok(self, admin_user, area_mock):
        with patch("app.api.routes.organization_service.organization_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = area_mock
            from app.api.routes.organization_service.organization_CUD_service import delete_area
            result = await delete_area(area_id=1, current_user=admin_user)
            content = json.loads(result.body.decode("utf-8"))
            assert content["success"] is True
            assert mock_ctrl.delete.called

    @pytest.mark.asyncio
    async def test_delete_area_not_found(self, admin_user):
        with patch("app.api.routes.organization_service.organization_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = None
            from app.api.routes.organization_service.organization_CUD_service import delete_area
            with pytest.raises(HTTPException) as exc:
                await delete_area(area_id=99, current_user=admin_user)
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_area_500(self, admin_user, area_mock):
        with patch("app.api.routes.organization_service.organization_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.side_effect = Exception("DB Crash")
            from app.api.routes.organization_service.organization_CUD_service import delete_area
            with pytest.raises(HTTPException) as exc:
                await delete_area(area_id=1, current_user=admin_user)
            assert exc.value.status_code == 500

# ------------------------------------------------------------------------------
# GET /areas
# ------------------------------------------------------------------------------
class TestQueryAreas:
    @pytest.mark.asyncio
    async def test_get_all_areas_ok(self, usuario_user, area_mock):
        with patch("app.api.routes.organization_service.organization_query_service.controller") as mock_ctrl:
            mock_ctrl.get_all.return_value = [area_mock]
            from app.api.routes.organization_service.organization_query_service import get_all_areas
            result = await get_all_areas(current_user=usuario_user)
            content = json.loads(result.body.decode("utf-8"))
            assert content["success"] is True
            assert len(content["data"]) == 1

    @pytest.mark.asyncio
    async def test_get_all_areas_empty(self, usuario_user):
        with patch("app.api.routes.organization_service.organization_query_service.controller") as mock_ctrl:
            mock_ctrl.get_all.return_value = []
            from app.api.routes.organization_service.organization_query_service import get_all_areas
            result = await get_all_areas(current_user=usuario_user)
            content = json.loads(result.body.decode("utf-8"))
            assert content["success"] is True
            assert len(content["data"]) == 0

    @pytest.mark.asyncio
    async def test_get_all_areas_500(self, usuario_user):
        with patch("app.api.routes.organization_service.organization_query_service.controller") as mock_ctrl:
            mock_ctrl.get_all.side_effect = Exception("DB Error")
            from app.api.routes.organization_service.organization_query_service import get_all_areas
            with pytest.raises(HTTPException) as exc:
                await get_all_areas(current_user=usuario_user)
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_area_by_id_ok(self, usuario_user, area_mock):
        with patch("app.api.routes.organization_service.organization_query_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = area_mock
            from app.api.routes.organization_service.organization_query_service import get_area_by_id
            result = await get_area_by_id(area_id=1, current_user=usuario_user)
            content = json.loads(result.body.decode("utf-8"))
            assert content["success"] is True
            assert content["data"]["nombre"] == "Soporte"

    @pytest.mark.asyncio
    async def test_get_area_by_id_not_found(self, usuario_user):
        with patch("app.api.routes.organization_service.organization_query_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = None
            from app.api.routes.organization_service.organization_query_service import get_area_by_id
            with pytest.raises(HTTPException) as exc:
                await get_area_by_id(area_id=99, current_user=usuario_user)
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_area_by_id_500(self, usuario_user):
        with patch("app.api.routes.organization_service.organization_query_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.side_effect = Exception("DB Error")
            from app.api.routes.organization_service.organization_query_service import get_area_by_id
            with pytest.raises(HTTPException) as exc:
                await get_area_by_id(area_id=1, current_user=usuario_user)
            assert exc.value.status_code == 500

# ------------------------------------------------------------------------------
# Acceso por roles en Organización
# ------------------------------------------------------------------------------
class TestOrganizationAccessControl:
    def test_scope_operador_permitido_en_create(self):
        from app.core.auth import encode_token, get_current_user
        from fastapi.security import SecurityScopes
        token = encode_token({"sub": "3", "scope": "operador"})
        request = MagicMock()
        request.headers.get.return_value = None
        request.cookies.get.return_value = None
        result = get_current_user(SecurityScopes(scopes=["admin", "supervisor", "operador"]), request, token)
        assert result["scope"] == "operador"

    def test_scope_agente_denegado_en_create(self):
        from app.core.auth import encode_token, get_current_user
        from fastapi.security import SecurityScopes
        token = encode_token({"sub": "4", "scope": "agente"})
        request = MagicMock()
        request.headers.get.return_value = None
        request.cookies.get.return_value = None
        with pytest.raises(HTTPException) as exc:
            get_current_user(SecurityScopes(scopes=["admin", "supervisor", "operador"]), request, token)
        assert exc.value.status_code == 403
