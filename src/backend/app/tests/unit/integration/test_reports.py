"""
Pruebas de integración para el Microservicio de Reportes y Dashboard.
Ejecutar con:
pytest app/tests/unit/integration/test_reports.py -v
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.logic.universal_controller_json import UniversalControllerJSON
from app.api.routes.reports_service import reports_service


# ─────────────────────────────────────────────────────────────────────────────
# Helper auth
# ─────────────────────────────────────────────────────────────────────────────

def auth_headers(scope="admin"):
    from app.core.auth import encode_token

    token = encode_token({"sub": "1", "scope": scope})
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────────────────────────────────────
# Fixture principal
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def test_env():
    """
    Crea un entorno aislado por test:
    - controller limpio
    - app nueva
    - client nuevo
    """
    test_controller = UniversalControllerJSON()
    test_controller.clear_tables()

    reports_service.controller = test_controller

    app_for_test = FastAPI()
    app_for_test.include_router(reports_service.router)

    with TestClient(app_for_test) as client:
        yield client, test_controller

    test_controller.clear_tables()


# ═════════════════════════════════════════════════════════════════════════════
# Tests de reportes
# ═════════════════════════════════════════════════════════════════════════════

class TestDashboard:
    def test_dashboard_exitoso(self, test_env):
        client, controller = test_env

        controller.seed(
            "PQR",
            [
                {"ID": 1, "categoria": "Queja", "prioridad": "alta", "area_id": 1, "estado": "pendiente"},
                {"ID": 2, "categoria": "Sugerencia", "prioridad": "media", "area_id": 1, "estado": "resuelta"},
                {"ID": 3, "categoria": "Queja", "prioridad": "alta", "area_id": 2, "estado": "resuelta"},
            ],
            overwrite=True,
        )

        response = client.get("/reports/dashboard", headers=auth_headers("admin"))

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["total_pqrs"] == 3
        assert body["data"]["pendientes"] == 1
        assert body["data"]["resueltas"] == 2

    def test_dashboard_sin_permiso(self, test_env):
        client, _ = test_env

        response = client.get("/reports/dashboard", headers=auth_headers("agente"))

        assert response.status_code == 403


class TestByCategory:
    def test_by_category_exitoso(self, test_env):
        client, controller = test_env

        controller.seed(
            "PQR",
            [
                {"ID": 1, "categoria": "Queja", "prioridad": "alta", "area_id": 1, "estado": "pendiente"},
                {"ID": 2, "categoria": "Sugerencia", "prioridad": "media", "area_id": 1, "estado": "resuelta"},
                {"ID": 3, "categoria": "Queja", "prioridad": "alta", "area_id": 2, "estado": "resuelta"},
            ],
            overwrite=True,
        )

        response = client.get("/reports/by-category", headers=auth_headers("admin"))

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"] == [
            {"categoria": "Queja", "cantidad": 2},
            {"categoria": "Sugerencia", "cantidad": 1},
        ]

    def test_by_category_sin_permiso(self, test_env):
        client, _ = test_env

        response = client.get("/reports/by-category", headers=auth_headers("agente"))

        assert response.status_code == 403


class TestByPriority:
    def test_by_priority_exitoso(self, test_env):
        client, controller = test_env

        controller.seed(
            "PQR",
            [
                {"ID": 1, "categoria": "Queja", "prioridad": "alta", "area_id": 1, "estado": "pendiente"},
                {"ID": 2, "categoria": "Sugerencia", "prioridad": "media", "area_id": 1, "estado": "resuelta"},
                {"ID": 3, "categoria": "Queja", "prioridad": "alta", "area_id": 2, "estado": "resuelta"},
            ],
            overwrite=True,
        )

        response = client.get("/reports/by-priority", headers=auth_headers("admin"))

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"] == [
            {"prioridad": "alta", "cantidad": 2},
            {"prioridad": "media", "cantidad": 1},
        ]

    def test_by_priority_sin_permiso(self, test_env):
        client, _ = test_env

        response = client.get("/reports/by-priority", headers=auth_headers("agente"))

        assert response.status_code == 403


class TestByArea:
    def test_by_area_exitoso(self, test_env):
        client, controller = test_env

        controller.seed(
            "PQR",
            [
                {"ID": 1, "categoria": "Queja", "prioridad": "alta", "area_id": 1, "estado": "pendiente"},
                {"ID": 2, "categoria": "Sugerencia", "prioridad": "media", "area_id": 1, "estado": "resuelta"},
                {"ID": 3, "categoria": "Queja", "prioridad": "alta", "area_id": 2, "estado": "resuelta"},
            ],
            overwrite=True,
        )
        controller.seed(
            "Area",
            [
                {"ID": 1, "nombre": "Soporte"},
                {"ID": 2, "nombre": "Ventas"},
            ],
            overwrite=True,
        )

        response = client.get("/reports/by-area", headers=auth_headers("admin"))

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"] == [
            {"area": "Soporte", "cantidad": 2},
            {"area": "Ventas", "cantidad": 1},
        ]

    def test_by_area_sin_permiso(self, test_env):
        client, _ = test_env

        response = client.get("/reports/by-area", headers=auth_headers("agente"))

        assert response.status_code == 403
