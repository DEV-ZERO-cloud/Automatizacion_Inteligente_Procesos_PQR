"""
conftest.py – Fixtures para pruebas de Organization (Áreas).
"""

import pytest


@pytest.fixture
def admin_user():
    return {"sub": "1", "scope": "admin"}