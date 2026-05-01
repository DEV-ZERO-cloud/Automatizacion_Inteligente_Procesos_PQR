"""
conftest.py – Fixtures para pruebas de PQR e Historial.
"""

import pytest
from datetime import datetime


@pytest.fixture
def admin_user():
    return {"sub": "1", "scope": "admin"}


@pytest.fixture
def supervisor_user():
    return {"sub": "2", "scope": "supervisor"}


@pytest.fixture
def agente_user():
    return {"sub": "3", "scope": "agente"}


@pytest.fixture
def usuario_user():
    return {"sub": "4", "scope": "usuario"}