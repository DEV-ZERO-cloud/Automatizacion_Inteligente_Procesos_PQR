"""
Pruebas Unitarias – Microservicio: Autenticación y Usuarios
Cubre: login, register, CRUD de usuarios, validación de tokens y roles.
"""

import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures comunes
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_user_active():
    user = MagicMock()
    user.id = 1
    user.correo = "admin@pqr.com"
    user.contrasena = "$pbkdf2-sha256$29000$hashed_password"
    user.activo = True
    user.rol_id = 1
    user.nombre = "Admin Test"
    user.identificacion = 123456789
    return user


@pytest.fixture
def mock_user_inactive():
    user = MagicMock()
    user.id = 2
    user.correo = "inactivo@pqr.com"
    user.contrasena = "$pbkdf2-sha256$29000$hashed_password"
    user.activo = False
    user.rol_id = 4
    return user


@pytest.fixture
def mock_controller():
    return MagicMock()


# ──────────────────────────────────────────────────────────────────────────────
# 1. SECURITY – hash y verificación de contraseña
# ──────────────────────────────────────────────────────────────────────────────

class TestSecurity:

    def test_hash_password_returns_string(self):
        from app.core.security import hash_password
        hashed = hash_password("MiPassword123")
        assert isinstance(hashed, str)
        assert hashed != "MiPassword123"

    def test_verify_password_correct(self):
        from app.core.security import hash_password, verify_password
        raw = "MiPassword123"
        hashed = hash_password(raw)
        assert verify_password(raw, hashed) is True

    def test_verify_password_wrong(self):
        from app.core.security import hash_password, verify_password
        hashed = hash_password("Correcto123")
        assert verify_password("Incorrecto999", hashed) is False

    def test_is_password_hashed_true(self):
        from app.core.security import hash_password, is_password_hashed
        hashed = hash_password("test123")
        assert is_password_hashed(hashed) is True

    def test_is_password_hashed_false(self):
        from app.core.security import is_password_hashed
        assert is_password_hashed("plaintext") is False

    def test_is_password_hashed_none(self):
        from app.core.security import is_password_hashed
        assert is_password_hashed(None) is False

    def test_is_password_hashed_empty(self):
        from app.core.security import is_password_hashed
        assert is_password_hashed("") is False


# ──────────────────────────────────────────────────────────────────────────────
# 2. AUTH – encode_token y get_current_user
# ──────────────────────────────────────────────────────────────────────────────

class TestAuth:

    def test_encode_token_returns_string(self):
        from app.core.auth import encode_token
        token = encode_token({"sub": "1", "scope": "admin"})
        assert isinstance(token, str)
        assert len(token) > 20

    def test_encode_token_different_payloads(self):
        from app.core.auth import encode_token
        t1 = encode_token({"sub": "1", "scope": "admin"})
        t2 = encode_token({"sub": "2", "scope": "usuario"})
        assert t1 != t2

    def test_get_current_user_valid_token(self):
        from app.core.auth import encode_token, get_current_user
        from fastapi.security import SecurityScopes

        token = encode_token({"sub": "1", "scope": "admin"})
        request = MagicMock()
        request.headers.get.return_value = f"Bearer {token}"
        request.cookies.get.return_value = None
        scopes = SecurityScopes(scopes=["admin"])

        result = get_current_user(scopes, request, token)
        assert result["sub"] == "1"
        assert result["scope"] == "admin"

    def test_get_current_user_empty_token_raises_401(self):
        from app.core.auth import get_current_user
        from fastapi.security import SecurityScopes

        request = MagicMock()
        request.headers.get.return_value = None
        request.cookies.get.return_value = None
        scopes = SecurityScopes(scopes=["admin"])

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(scopes, request, "")
        assert exc_info.value.status_code == 401

    def test_get_current_user_invalid_token_raises_401(self):
        from app.core.auth import get_current_user
        from fastapi.security import SecurityScopes

        request = MagicMock()
        request.headers.get.return_value = None
        request.cookies.get.return_value = None
        scopes = SecurityScopes(scopes=["admin"])

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(scopes, request, "token.invalido.jwt")
        assert exc_info.value.status_code == 401

    def test_get_current_user_wrong_scope_raises_403(self):
        from app.core.auth import encode_token, get_current_user
        from fastapi.security import SecurityScopes

        token = encode_token({"sub": "5", "scope": "usuario"})
        request = MagicMock()
        request.headers.get.return_value = None
        request.cookies.get.return_value = None
        scopes = SecurityScopes(scopes=["admin"])

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(scopes, request, token)
        assert exc_info.value.status_code == 403

    def test_get_current_user_token_from_cookie(self):
        from app.core.auth import encode_token, get_current_user
        from fastapi.security import SecurityScopes

        token = encode_token({"sub": "3", "scope": "supervisor"})
        request = MagicMock()
        request.headers.get.return_value = None
        request.cookies.get.return_value = f"Bearer {token}"
        scopes = SecurityScopes(scopes=["supervisor"])

        result = get_current_user(scopes, request, "dummy")
        assert result["sub"] == "3"
        assert result["scope"] == "supervisor"


# ──────────────────────────────────────────────────────────────────────────────
# 3. LOGIN
# ──────────────────────────────────────────────────────────────────────────────

class TestLogin:

    @pytest.mark.asyncio
    async def test_login_exitoso(self, mock_user_active):
        from app.core.security import hash_password
        mock_user_active.contrasena = hash_password("password123")

        with patch("app.api.routes.user_auth_service.user_CUD_service.controller") as mock_ctrl, \
             patch("app.api.routes.user_auth_service.user_CUD_service.verify_password", return_value=True), \
             patch("app.api.routes.user_auth_service.user_CUD_service.is_password_hashed", return_value=True), \
             patch("app.api.routes.user_auth_service.user_CUD_service.encode_token", return_value="fake.token"):

            mock_ctrl.get_by_column.return_value = mock_user_active
            from app.api.routes.user_auth_service.user_CUD_service import login

            form = MagicMock(spec=OAuth2PasswordRequestForm)
            form.username = "admin@pqr.com"
            form.password = "password123"

            result = await login(form)
            body = json.loads(result.body)
            assert body["access_token"] == "fake.token"
            assert body["role"] == "admin"
            assert body["user_id"] == 1

    @pytest.mark.asyncio
    async def test_login_usuario_no_existe(self):
        with patch("app.api.routes.user_auth_service.user_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_column.return_value = None
            from app.api.routes.user_auth_service.user_CUD_service import login

            form = MagicMock()
            form.username = "noexiste@pqr.com"
            form.password = "cualquier"

            with pytest.raises(HTTPException) as exc:
                await login(form)
            assert exc.value.status_code == 401
            assert "Credenciales" in exc.value.detail

    @pytest.mark.asyncio
    async def test_login_usuario_inactivo(self, mock_user_inactive):
        with patch("app.api.routes.user_auth_service.user_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_column.return_value = mock_user_inactive
            from app.api.routes.user_auth_service.user_CUD_service import login

            form = MagicMock()
            form.username = "inactivo@pqr.com"
            form.password = "password123"

            with pytest.raises(HTTPException) as exc:
                await login(form)
            assert exc.value.status_code == 403
            assert "inactivo" in exc.value.detail.lower()

    @pytest.mark.asyncio
    async def test_login_password_incorrecta(self, mock_user_active):
        with patch("app.api.routes.user_auth_service.user_CUD_service.controller") as mock_ctrl, \
             patch("app.api.routes.user_auth_service.user_CUD_service.verify_password", return_value=False), \
             patch("app.api.routes.user_auth_service.user_CUD_service.is_password_hashed", return_value=True):

            mock_ctrl.get_by_column.return_value = mock_user_active
            from app.api.routes.user_auth_service.user_CUD_service import login

            form = MagicMock()
            form.username = "admin@pqr.com"
            form.password = "mal_password"

            with pytest.raises(HTTPException) as exc:
                await login(form)
            assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_login_scope_segun_rol(self, mock_user_active):
        """Verifica que cada rol_id mapee al scope correcto."""
        role_map = {1: "admin", 2: "supervisor", 3: "agente", 4: "usuario"}

        for rol_id, expected_scope in role_map.items():
            mock_user_active.rol_id = rol_id
            with patch("app.api.routes.user_auth_service.user_CUD_service.controller") as mock_ctrl, \
                 patch("app.api.routes.user_auth_service.user_CUD_service.verify_password", return_value=True), \
                 patch("app.api.routes.user_auth_service.user_CUD_service.is_password_hashed", return_value=True), \
                 patch("app.api.routes.user_auth_service.user_CUD_service.encode_token", return_value="tok"):

                mock_ctrl.get_by_column.return_value = mock_user_active
                from app.api.routes.user_auth_service.user_CUD_service import login

                form = MagicMock()
                form.username = "test@pqr.com"
                form.password = "pass"
                result = await login(form)
                body = json.loads(result.body)
                assert body["role"] == expected_scope


# ──────────────────────────────────────────────────────────────────────────────
# 4. REGISTER
# ──────────────────────────────────────────────────────────────────────────────

class TestRegister:

    @pytest.mark.asyncio
    async def test_register_exitoso(self):
        with patch("app.api.routes.user_auth_service.user_CUD_service.controller") as mock_ctrl, \
             patch("app.api.routes.user_auth_service.user_CUD_service.hash_password", return_value="hashed"), \
             patch("app.api.routes.user_auth_service.user_CUD_service.encode_token", return_value="tok"):

            mock_ctrl.get_by_column.return_value = None
            mock_ctrl.get_all.return_value = []
            mock_ctrl.add.return_value = None

            from app.api.routes.user_auth_service.user_CUD_service import register_user, RegisterRequest

            payload = RegisterRequest(
                identificacion=987654321,
                nombre="Usuario Nuevo",
                correo="nuevo@pqr.com",
                password="password123"
            )
            result = await register_user(payload)
            content = json.loads(result.body.decode('utf-8'))
            assert content["success"] is True
            assert content["data"]["role"] == "usuario"

    @pytest.mark.asyncio
    async def test_register_correo_duplicado(self):
        with patch("app.api.routes.user_auth_service.user_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_column.return_value = MagicMock()  # ya existe
            from app.api.routes.user_auth_service.user_CUD_service import register_user, RegisterRequest

            payload = RegisterRequest(
                identificacion=111,
                nombre="Duplicado",
                correo="duplicado@pqr.com",
                password="password123"
            )
            with pytest.raises(HTTPException) as exc:
                await register_user(payload)
            assert exc.value.status_code == 400
            assert "correo" in exc.value.detail.lower()

    @pytest.mark.asyncio
    async def test_register_identificacion_duplicada(self):
        with patch("app.api.routes.user_auth_service.user_CUD_service.controller") as mock_ctrl:
            # correo no existe, identificación sí
            mock_ctrl.get_by_column.side_effect = [None, MagicMock()]
            from app.api.routes.user_auth_service.user_CUD_service import register_user, RegisterRequest

            payload = RegisterRequest(
                identificacion=123456789,
                nombre="Duplicado ID",
                correo="unico@pqr.com",
                password="password123"
            )
            with pytest.raises(HTTPException) as exc:
                await register_user(payload)
            assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_register_asigna_rol_usuario(self):
        """Usuario registrado vía /auth/register siempre obtiene rol 4 (usuario)."""
        created_users = []

        with patch("app.api.routes.user_auth_service.user_CUD_service.controller") as mock_ctrl, \
             patch("app.api.routes.user_auth_service.user_CUD_service.hash_password", return_value="h"), \
             patch("app.api.routes.user_auth_service.user_CUD_service.encode_token", return_value="t"):

            mock_ctrl.get_by_column.return_value = None
            mock_ctrl.get_all.return_value = []
            mock_ctrl.add.side_effect = lambda u: created_users.append(u)

            from app.api.routes.user_auth_service.user_CUD_service import register_user, RegisterRequest
            payload = RegisterRequest(
                identificacion=555, nombre="Test Rol", correo="roltest@pqr.com", password="pass1234"
            )
            await register_user(payload)
            assert created_users[0].rol_id == 4


# ──────────────────────────────────────────────────────────────────────────────
# 5. CREATE USER (admin/supervisor)
# ──────────────────────────────────────────────────────────────────────────────

class TestCreateUser:

    @pytest.mark.asyncio
    async def test_create_user_exitoso(self):
        from app.models.user import UserCreate
        with patch("app.api.routes.user_auth_service.user_CUD_service.controller") as mock_ctrl, \
             patch("app.api.routes.user_auth_service.user_CUD_service.hash_password", return_value="hashed"):

            mock_ctrl.get_by_column.return_value = None
            mock_ctrl.add.return_value = None

            from app.api.routes.user_auth_service.user_CUD_service import create_user
            payload = UserCreate(
                id=10, identificacion="100", nombre="Nuevo Admin", correo="nadmin@pqr.com",
                telefono="3001234567", contrasena="secret123", rol_id=1, area_id=1
            )
            current_user = {"sub": "1", "scope": "admin"}
            result = await create_user(payload, current_user)
            content = json.loads(result.body.decode("utf-8"))
            assert content["success"] is True

    @pytest.mark.asyncio
    async def test_create_user_correo_duplicado(self):
        from app.models.user import UserCreate
        with patch("app.api.routes.user_auth_service.user_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_column.return_value = MagicMock()

            from app.api.routes.user_auth_service.user_CUD_service import create_user
            payload = UserCreate(
                id=11, identificacion="200", nombre="Dup", correo="dup@pqr.com",
                telefono="", contrasena="pass1234", rol_id=1, area_id=1
            )
            with pytest.raises(HTTPException) as exc:
                await create_user(payload, {"sub": "1", "scope": "admin"})
            assert exc.value.status_code == 400


# ──────────────────────────────────────────────────────────────────────────────
# 6. GET USERS
# ──────────────────────────────────────────────────────────────────────────────

class TestGetUsers:

    @pytest.mark.asyncio
    async def test_get_all_users(self):
        user1 = MagicMock()
        user1.id, user1.nombre, user1.correo, user1.rol_id, user1.area_id = 1, "A", "a@p.com", 1, 1
        user2 = MagicMock()
        user2.id, user2.nombre, user2.correo, user2.rol_id, user2.area_id = 2, "B", "b@p.com", 4, 2

        with patch("app.api.routes.user_auth_service.user_query_service.controller") as mock_ctrl:
            mock_ctrl.get_all.return_value = [user1, user2]
            from app.api.routes.user_auth_service.user_query_service import get_all_users
            result = await get_all_users({"sub": "1", "scope": "admin"})
            content = json.loads(result.body.decode("utf-8"))
            assert len(content["data"]) == 2

    @pytest.mark.asyncio
    async def test_get_all_users_lista_vacia(self):
        with patch("app.api.routes.user_auth_service.user_query_service.controller") as mock_ctrl:
            mock_ctrl.get_all.return_value = []
            from app.api.routes.user_auth_service.user_query_service import get_all_users
            result = await get_all_users({"sub": "1", "scope": "admin"})
            content = json.loads(result.body.decode("utf-8"))
            assert content["data"] == []

    @pytest.mark.asyncio
    async def test_get_user_by_id_found(self):
        user = MagicMock()
        user.id, user.nombre, user.correo, user.rol_id, user.area_id = 5, "Test", "t@p.com", 2, 1

        with patch("app.api.routes.user_auth_service.user_query_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = user
            from app.api.routes.user_auth_service.user_query_service import get_user_by_id
            result = await get_user_by_id(5, {"sub": "1", "scope": "admin"})
            content = json.loads(result.body.decode("utf-8"))
            assert content["data"]["id"] == 5

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self):
        with patch("app.api.routes.user_auth_service.user_query_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = None
            from app.api.routes.user_auth_service.user_query_service import get_user_by_id
            with pytest.raises(HTTPException) as exc:
                await get_user_by_id(999, {"sub": "1", "scope": "admin"})
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_supervisors_solo_rol2(self):
        u1 = MagicMock(); u1.id, u1.nombre, u1.correo, u1.rol_id = 1, "Admin", "a@p.com", 1
        u2 = MagicMock(); u2.id, u2.nombre, u2.correo, u2.rol_id = 2, "Super", "s@p.com", 2
        u3 = MagicMock(); u3.id, u3.nombre, u3.correo, u3.rol_id = 3, "User", "u@p.com", 4

        with patch("app.api.routes.user_auth_service.user_query_service.controller") as mock_ctrl:
            mock_ctrl.get_all.return_value = [u1, u2, u3]
            from app.api.routes.user_auth_service.user_query_service import get_all_supervisors
            result = await get_all_supervisors({"sub": "1", "scope": "admin"})
            content = json.loads(result.body.decode("utf-8"))
            assert len(content["data"]) == 1
            assert content["data"][0]["rol_id"] == 2


# ──────────────────────────────────────────────────────────────────────────────
# 7. UPDATE / DELETE USER
# ──────────────────────────────────────────────────────────────────────────────

class TestUpdateDeleteUser:

    @pytest.mark.asyncio
    async def test_update_user_exitoso(self):
        existing = MagicMock()
        existing.identificacion = "123"
        existing.activo = True
        existing.contrasena = "hashed"

        with patch("app.api.routes.user_auth_service.user_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = existing
            mock_ctrl.update.return_value = None

            from app.api.routes.user_auth_service.user_CUD_service import update_user
            from app.models.user import UserUpdate

            payload = UserUpdate(id=1, nombre="Nuevo Nombre", correo="new@pqr.com", rol_id=2, area_id=1)
            result = await update_user(payload, {"sub": "1", "scope": "admin"})
            content = json.loads(result.body.decode("utf-8"))
            assert content["success"] is True

    @pytest.mark.asyncio
    async def test_update_user_not_found(self):
        with patch("app.api.routes.user_auth_service.user_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = None

            from app.api.routes.user_auth_service.user_CUD_service import update_user
            from app.models.user import UserUpdate

            payload = UserUpdate(id=999, nombre="X", correo="x@p.com", rol_id=1, area_id=1)
            with pytest.raises(HTTPException) as exc:
                await update_user(payload, {"sub": "1", "scope": "admin"})
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_exitoso(self):
        existing = MagicMock()
        with patch("app.api.routes.user_auth_service.user_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = existing
            mock_ctrl.delete.return_value = None

            from app.api.routes.user_auth_service.user_CUD_service import delete_user
            result = await delete_user(1, {"sub": "1", "scope": "admin"})
            content = json.loads(result.body.decode("utf-8"))
            assert content["success"] is True

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self):
        with patch("app.api.routes.user_auth_service.user_CUD_service.controller") as mock_ctrl:
            mock_ctrl.get_by_id.return_value = None

            from app.api.routes.user_auth_service.user_CUD_service import delete_user
            with pytest.raises(HTTPException) as exc:
                await delete_user(999, {"sub": "1", "scope": "admin"})
            assert exc.value.status_code == 404
