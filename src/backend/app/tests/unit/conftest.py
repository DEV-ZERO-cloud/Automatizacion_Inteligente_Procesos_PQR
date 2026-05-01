"""
conftest.py – Configuración global de pytest para pruebas unitarias PQR.
"""

import sys
from unittest.mock import MagicMock

# ── Patch global: evita conexión real a PostgreSQL durante unit tests ──────────
import pytest


@pytest.fixture(autouse=True)
def patch_db_connection(monkeypatch):
    """
    Parchea psycopg2 para que UniversalController no intente
    conectarse a una base de datos real al importar módulos.
    """
    mock_psycopg2 = MagicMock()
    mock_psycopg2.pool = MagicMock()
    monkeypatch.setitem(sys.modules, 'psycopg2', mock_psycopg2)
    monkeypatch.setitem(sys.modules, 'psycopg2.pool', mock_psycopg2.pool)