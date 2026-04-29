"""
Pruebas Unitarias – Microservicio: Reportes y Dashboard
Cubre: dashboard, by-category, by-priority, by-area, control de acceso.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def admin_user():
    return {"sub": "1", "scope": "admin"}


@pytest.fixture
def supervisor_user():
    return {"sub": "2", "scope": "supervisor"}


@pytest.fixture
def usuario_user():
    return {"sub": "5", "scope": "usuario"}


@pytest.fixture
def dashboard_summary():
    return {"total_pqrs": 100, "pendientes": 30, "resueltas": 70}


@pytest.fixture
def category_data():
    return [
        {"categoria": "Petición", "total": 40},
        {"categoria": "Queja", "total": 35},
        {"categoria": "Reclamo", "total": 25},
    ]


@pytest.fixture
def priority_data():
    return [
        {"prioridad": "Alta", "total": 20},
        {"prioridad": "Media", "total": 50},
        {"prioridad": "Baja", "total": 30},
    ]


@pytest.fixture
def area_data():
    return [
        {"area": "Soporte", "total": 45},
        {"area": "Ventas", "total": 30},
        {"area": "TI", "total": 25},
    ]


# ──────────────────────────────────────────────────────────────────────────────
# 1. GET /reports/dashboard
# ──────────────────────────────────────────────────────────────────────────────

class TestDashboard:

    @pytest.mark.asyncio
    async def test_dashboard_admin_ok(self, admin_user, dashboard_summary):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_dashboard_summary.return_value = dashboard_summary
            from app.api.routes.reports_service.reports_service import get_dashboard
            result = await get_dashboard(admin_user)
            content = json.loads(result.body.decode('utf-8'))
            assert content["success"] is True
            assert content["data"]["total_pqrs"] == 100
            assert content["data"]["pendientes"] == 30
            assert content["data"]["resueltas"] == 70

    @pytest.mark.asyncio
    async def test_dashboard_supervisor_ok(self, supervisor_user, dashboard_summary):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_dashboard_summary.return_value = dashboard_summary
            from app.api.routes.reports_service.reports_service import get_dashboard
            result = await get_dashboard(supervisor_user)
            content = json.loads(result.body.decode('utf-8'))
            assert content["success"] is True

    @pytest.mark.asyncio
    async def test_dashboard_estructura_respuesta(self, admin_user, dashboard_summary):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_dashboard_summary.return_value = dashboard_summary
            from app.api.routes.reports_service.reports_service import get_dashboard
            result = await get_dashboard(admin_user)
            content = json.loads(result.body.decode('utf-8'))
            assert "total_pqrs" in content["data"]
            assert "pendientes" in content["data"]
            assert "resueltas" in content["data"]

    @pytest.mark.asyncio
    async def test_dashboard_pendientes_mas_resueltas_igual_total(self, admin_user):
        summary = {"total_pqrs": 60, "pendientes": 20, "resueltas": 40}
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_dashboard_summary.return_value = summary
            from app.api.routes.reports_service.reports_service import get_dashboard
            result = await get_dashboard(admin_user)
            content = json.loads(result.body.decode('utf-8'))
            d = content["data"]
            assert d["pendientes"] + d["resueltas"] == d["total_pqrs"]

    @pytest.mark.asyncio
    async def test_dashboard_error_interno_raises_500(self, admin_user):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_dashboard_summary.side_effect = Exception("DB error")
            from app.api.routes.reports_service.reports_service import get_dashboard
            with pytest.raises(HTTPException) as exc:
                await get_dashboard(admin_user)
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_dashboard_sin_pqrs(self, admin_user):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_dashboard_summary.return_value = {
                "total_pqrs": 0, "pendientes": 0, "resueltas": 0
            }
            from app.api.routes.reports_service.reports_service import get_dashboard
            result = await get_dashboard(admin_user)
            content = json.loads(result.body.decode('utf-8'))
            assert content["data"]["total_pqrs"] == 0

    @pytest.mark.asyncio
    async def test_dashboard_mensaje_correcto(self, admin_user, dashboard_summary):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_dashboard_summary.return_value = dashboard_summary
            from app.api.routes.reports_service.reports_service import get_dashboard
            result = await get_dashboard(admin_user)
            content = json.loads(result.body.decode('utf-8'))
            assert "dashboard" in content["message"].lower()


# ──────────────────────────────────────────────────────────────────────────────
# 2. GET /reports/by-category
# ──────────────────────────────────────────────────────────────────────────────

class TestByCategory:

    @pytest.mark.asyncio
    async def test_by_category_admin_ok(self, admin_user, category_data):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_category.return_value = category_data
            from app.api.routes.reports_service.reports_service import get_by_category
            result = await get_by_category(admin_user)
            content = json.loads(result.body.decode('utf-8'))
            assert content["success"] is True
            assert len(content["data"]) == 3

    @pytest.mark.asyncio
    async def test_by_category_supervisor_ok(self, supervisor_user, category_data):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_category.return_value = category_data
            from app.api.routes.reports_service.reports_service import get_by_category
            result = await get_by_category(supervisor_user)
            content = json.loads(result.body.decode('utf-8'))
            assert content["success"] is True

    @pytest.mark.asyncio
    async def test_by_category_lista_vacia(self, admin_user):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_category.return_value = []
            from app.api.routes.reports_service.reports_service import get_by_category
            result = await get_by_category(admin_user)
            content = json.loads(result.body.decode('utf-8'))
            assert content["data"] == []

    @pytest.mark.asyncio
    async def test_by_category_error_500(self, admin_user):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_category.side_effect = Exception("DB fail")
            from app.api.routes.reports_service.reports_service import get_by_category
            with pytest.raises(HTTPException) as exc:
                await get_by_category(admin_user)
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_by_category_tipos_esperados(self, admin_user, category_data):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_category.return_value = category_data
            from app.api.routes.reports_service.reports_service import get_by_category
            result = await get_by_category(admin_user)
            content = json.loads(result.body.decode('utf-8'))
            categorias = [item["categoria"] for item in content["data"]]
            assert "Petición" in categorias
            assert "Queja" in categorias
            assert "Reclamo" in categorias

    @pytest.mark.asyncio
    async def test_by_category_mensaje_correcto(self, admin_user, category_data):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_category.return_value = category_data
            from app.api.routes.reports_service.reports_service import get_by_category
            result = await get_by_category(admin_user)
            content = json.loads(result.body.decode('utf-8'))
            assert "categoría" in content["message"].lower() or "categoria" in content["message"].lower()


# ──────────────────────────────────────────────────────────────────────────────
# 3. GET /reports/by-priority
# ──────────────────────────────────────────────────────────────────────────────

class TestByPriority:

    @pytest.mark.asyncio
    async def test_by_priority_admin_ok(self, admin_user, priority_data):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_priority.return_value = priority_data
            from app.api.routes.reports_service.reports_service import get_by_priority
            result = await get_by_priority(admin_user)
            content = json.loads(result.body.decode('utf-8'))
            assert content["success"] is True
            assert len(content["data"]) == 3

    @pytest.mark.asyncio
    async def test_by_priority_supervisor_ok(self, supervisor_user, priority_data):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_priority.return_value = priority_data
            from app.api.routes.reports_service.reports_service import get_by_priority
            result = await get_by_priority(supervisor_user)
            content = json.loads(result.body.decode('utf-8'))
            assert content["success"] is True

    @pytest.mark.asyncio
    async def test_by_priority_prioridades_esperadas(self, admin_user, priority_data):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_priority.return_value = priority_data
            from app.api.routes.reports_service.reports_service import get_by_priority
            result = await get_by_priority(admin_user)
            content = json.loads(result.body.decode('utf-8'))
            prioridades = [item["prioridad"] for item in content["data"]]
            assert "Alta" in prioridades
            assert "Media" in prioridades
            assert "Baja" in prioridades

    @pytest.mark.asyncio
    async def test_by_priority_totales_positivos(self, admin_user, priority_data):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_priority.return_value = priority_data
            from app.api.routes.reports_service.reports_service import get_by_priority
            result = await get_by_priority(admin_user)
            content = json.loads(result.body.decode('utf-8'))
            for item in content["data"]:
                assert item["total"] >= 0

    @pytest.mark.asyncio
    async def test_by_priority_error_500(self, admin_user):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_priority.side_effect = Exception("Error")
            from app.api.routes.reports_service.reports_service import get_by_priority
            with pytest.raises(HTTPException) as exc:
                await get_by_priority(admin_user)
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_by_priority_lista_vacia(self, admin_user):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_priority.return_value = []
            from app.api.routes.reports_service.reports_service import get_by_priority
            result = await get_by_priority(admin_user)
            content = json.loads(result.body.decode('utf-8'))
            assert content["data"] == []


# ──────────────────────────────────────────────────────────────────────────────
# 4. GET /reports/by-area
# ──────────────────────────────────────────────────────────────────────────────

class TestByArea:

    @pytest.mark.asyncio
    async def test_by_area_admin_ok(self, admin_user, area_data):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_area.return_value = area_data
            from app.api.routes.reports_service.reports_service import get_by_area
            result = await get_by_area(admin_user)
            content = json.loads(result.body.decode('utf-8'))
            assert content["success"] is True
            assert len(content["data"]) == 3

    @pytest.mark.asyncio
    async def test_by_area_supervisor_ok(self, supervisor_user, area_data):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_area.return_value = area_data
            from app.api.routes.reports_service.reports_service import get_by_area
            result = await get_by_area(supervisor_user)
            content = json.loads(result.body.decode('utf-8'))
            assert content["success"] is True

    @pytest.mark.asyncio
    async def test_by_area_areas_esperadas(self, admin_user, area_data):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_area.return_value = area_data
            from app.api.routes.reports_service.reports_service import get_by_area
            result = await get_by_area(admin_user)
            content = json.loads(result.body.decode('utf-8'))
            areas = [item["area"] for item in content["data"]]
            assert "Soporte" in areas

    @pytest.mark.asyncio
    async def test_by_area_error_500(self, admin_user):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_area.side_effect = Exception("Error DB")
            from app.api.routes.reports_service.reports_service import get_by_area
            with pytest.raises(HTTPException) as exc:
                await get_by_area(admin_user)
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_by_area_lista_vacia(self, admin_user):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_area.return_value = []
            from app.api.routes.reports_service.reports_service import get_by_area
            result = await get_by_area(admin_user)
            content = json.loads(result.body.decode('utf-8'))
            assert content["data"] == []

    @pytest.mark.asyncio
    async def test_by_area_mensaje_correcto(self, admin_user, area_data):
        with patch("app.api.routes.reports_service.reports_service.controller") as mock_ctrl:
            mock_ctrl.get_pqrs_by_area.return_value = area_data
            from app.api.routes.reports_service.reports_service import get_by_area
            result = await get_by_area(admin_user)
            content = json.loads(result.body.decode('utf-8'))
            assert "área" in content["message"].lower() or "area" in content["message"].lower()


# ──────────────────────────────────────────────────────────────────────────────
# 5. CONTROL DE ACCESO – verify_role para reportes
# ──────────────────────────────────────────────────────────────────────────────

class TestReportAccessControl:
    """
    Valida que solo admin/supervisor acceden a reportes.
    Simula la verificación de scope directamente en auth.
    """

    def test_scope_admin_permitido(self):
        from app.core.auth import encode_token, get_current_user
        from fastapi.security import SecurityScopes

        token = encode_token({"sub": "1", "scope": "admin"})
        request = MagicMock()
        request.headers.get.return_value = None
        request.cookies.get.return_value = None

        result = get_current_user(SecurityScopes(scopes=["admin", "supervisor"]), request, token)
        assert result["scope"] == "admin"

    def test_scope_supervisor_permitido(self):
        from app.core.auth import encode_token, get_current_user
        from fastapi.security import SecurityScopes

        token = encode_token({"sub": "2", "scope": "supervisor"})
        request = MagicMock()
        request.headers.get.return_value = None
        request.cookies.get.return_value = None

        result = get_current_user(SecurityScopes(scopes=["admin", "supervisor"]), request, token)
        assert result["scope"] == "supervisor"

    def test_scope_agente_denegado_en_reportes(self):
        from app.core.auth import encode_token, get_current_user
        from fastapi.security import SecurityScopes

        token = encode_token({"sub": "3", "scope": "agente"})
        request = MagicMock()
        request.headers.get.return_value = None
        request.cookies.get.return_value = None

        with pytest.raises(HTTPException) as exc:
            get_current_user(SecurityScopes(scopes=["admin", "supervisor"]), request, token)
        assert exc.value.status_code == 403

    def test_scope_usuario_denegado_en_reportes(self):
        from app.core.auth import encode_token, get_current_user
        from fastapi.security import SecurityScopes

        token = encode_token({"sub": "5", "scope": "usuario"})
        request = MagicMock()
        request.headers.get.return_value = None
        request.cookies.get.return_value = None

        with pytest.raises(HTTPException) as exc:
            get_current_user(SecurityScopes(scopes=["admin", "supervisor"]), request, token)
        assert exc.value.status_code == 403

    def test_sin_token_denegado(self):
        from app.core.auth import get_current_user
        from fastapi.security import SecurityScopes

        request = MagicMock()
        request.headers.get.return_value = None
        request.cookies.get.return_value = None

        with pytest.raises(HTTPException) as exc:
            get_current_user(SecurityScopes(scopes=["admin", "supervisor"]), request, "")
        assert exc.value.status_code == 401
