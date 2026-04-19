"""
conftest.py – Configuración global de pytest para pruebas unitarias PQR.
"""

import pytest
from unittest.mock import MagicMock, patch


# ── Patch global: evita conexión real a PostgreSQL durante unit tests ──────────
@pytest.fixture(autouse=True)
def patch_db_connection():
    """
    Parchea psycopg2.connect para que UniversalController no intente
    conectarse a una base de datos real al importar módulos.
    """
    with patch("psycopg2.connect") as mock_conn:
        mock_conn.return_value = MagicMock()
        yield mock_conn


# ── Patch global: evita carga de settings desde .env ──────────────────────────
@pytest.fixture(autouse=True)
def patch_settings():
    with patch("app.core.config.settings") as mock_settings:
        mock_settings.SECRET_KEY = "test-secret-key-for-unit-tests"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.PROJECT_NAME = "PQR Test"
        mock_settings.db_config = {
            "host": "localhost",
            "port": "5432",
            "dbname": "test_db",
            "user": "test_user",
            "password": "test_pass",
        }
        yield mock_settings
