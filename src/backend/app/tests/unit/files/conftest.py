"""
conftest.py – Fixtures para pruebas de Files (Archivos).
"""

import pytest


@pytest.fixture
def admin_user():
    return {"sub": "1", "scope": "admin"}


@pytest.fixture
def supervisor_user():
    return {"sub": "2", "scope": "supervisor"}


@pytest.fixture
def usuario_user():
    return {"sub": "4", "scope": "usuario"}