"""
Pruebas de integración para el Microservicio de Autenticación y Usuarios.
Ejecutar con:
pytest app/tests/unit/integration/test_user_auth.py -v
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.logic.universal_controller_json import UniversalControllerJSON
from app.api.routes.user_auth_service import (
    user_CUD_service,
    user_query_service,
)


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

    # Sobrescribimos controller en módulos de rutas
    user_CUD_service.controller = test_controller
    user_query_service.controller = test_controller

    # App de prueba nueva por test
    app_for_test = FastAPI()
    app_for_test.include_router(user_CUD_service.router)
    app_for_test.include_router(user_query_service.router)

    with TestClient(app_for_test) as client:
        yield client, test_controller

    test_controller.clear_tables()


# ═════════════════════════════════════════════════════════════════════════════
# Tests POST /auth/login
# ═════════════════════════════════════════════════════════════════════════════
class TestLogin:
    def test_login_exitoso(self, test_env):
        client, controller = test_env
        from app.models.user import UserCreate

        controller.add(UserCreate(
        ID=1,
        identificacion=123456,
        nombre="Admin Test",
        correo="admin@pqr.com",
        telefono="3001234567",
        contrasena="secret123",
        rol_id=1,
        area_id=1,
        activo=1,
    ))

        response = client.post(
        "/auth/login",
        data={"username": "admin@pqr.com", "password": "secret123"},
    )

        assert response.status_code == 200
        body = response.json()

    # Ajuste flexible al formato real del endpoint
        assert isinstance(body, dict)

    # Caso 1: respuesta envuelta
        if "data" in body:
            assert "token" in body["data"] or "access_token" in body["data"]
        else:
        # Caso 2: respuesta directa
            assert "token" in body or "access_token" in body

    def test_login_credenciales_invalidas(self, test_env):
        client, _ = test_env

        response = client.post(
            "/auth/login",
            data={"username": "noexiste@pqr.com", "password": "wrong"},
        )
        assert response.status_code == 401

    def test_login_usuario_inactivo(self, test_env):
        client, controller = test_env
        from app.models.user import UserCreate

        controller.add(UserCreate(
            ID=2,
            identificacion=999,
            nombre="Inactivo",
            correo="inactivo@pqr.com",
            telefono="",
            contrasena="pass",
            rol_id=4,
            area_id=1,
            activo=0,
        ))

        response = client.post(
            "/auth/login",
            data={"username": "inactivo@pqr.com", "password": "pass"},
        )
        assert response.status_code == 403


# ═════════════════════════════════════════════════════════════════════════════
# Tests GET /users y GET /users/{id}
# ═════════════════════════════════════════════════════════════════════════════
class TestGetUsers:
    def test_get_all_users(self, test_env):
        client, controller = test_env
        from app.models.user import UserCreate

        controller.add(UserCreate(
            ID=1,
            identificacion=1,
            nombre="Ana",
            correo="ana@pqr.com",
            telefono="",
            contrasena="x",
            rol_id=1,
            area_id=1,
            activo=1,
        ))

        controller.add(UserCreate(
            ID=2,
            identificacion=2,
            nombre="Luis",
            correo="luis@pqr.com",
            telefono="",
            contrasena="x",
            rol_id=3,
            area_id=2,
            activo=1,
        ))

        response = client.get("/users", headers=auth_headers("admin"))
        assert response.status_code == 200

        body = response.json()
        assert body["success"] is True
        assert len(body["data"]) == 2

    def test_get_user_by_id_existente(self, test_env):
        client, controller = test_env
        from app.models.user import UserCreate

        controller.add(UserCreate(
            ID=1,
            identificacion=1,
            nombre="Ana",
            correo="ana@pqr.com",
            telefono="",
            contrasena="x",
            rol_id=1,
            area_id=1,
            activo=1,
        ))

        response = client.get("/users/1", headers=auth_headers("admin"))
        assert response.status_code == 200
        assert response.json()["data"]["nombre"] == "Ana"

    def test_get_user_by_id_no_existente(self, test_env):
        client, _ = test_env

        response = client.get("/users/999", headers=auth_headers("admin"))
        assert response.status_code == 404


# ═════════════════════════════════════════════════════════════════════════════
# Tests POST /users/create
# ═════════════════════════════════════════════════════════════════════════════
class TestCreateUser:
    def test_crear_usuario_exitoso(self, test_env):
        client, _ = test_env

        payload = {
            "ID": 10,
            "identificacion": 98765,
            "nombre": "Carlos Pérez",
            "correo": "carlos@pqr.com",
            "telefono": "3109876543",
            "contrasena": "clave123",
            "rol_id": 3,
            "area_id": 2,
        }

        response = client.post(
            "/users/create",
            json=payload,
            headers=auth_headers("admin")
        )

        assert response.status_code == 201
        assert response.json()["success"] is True

    def test_crear_usuario_duplicado(self, test_env):
        client, controller = test_env
        from app.models.user import UserCreate

        controller.add(UserCreate(
            ID=5,
            identificacion=98765,
            nombre="Existente",
            correo="carlos@pqr.com",
            telefono="",
            contrasena="x",
            rol_id=3,
            area_id=2,
            activo=1,
        ))

        payload = {
            "ID": 10,
            "identificacion": 98765,
            "nombre": "Carlos",
            "correo": "carlos@pqr.com",
            "telefono": "",
            "contrasena": "x",
            "rol_id": 3,
            "area_id": 2,
        }

        response = client.post(
            "/users/create",
            json=payload,
            headers=auth_headers("admin")
        )

        assert response.status_code == 400