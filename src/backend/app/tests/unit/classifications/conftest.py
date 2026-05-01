"""
conftest.py – Fixtures para pruebas de Classifications.
"""

import pytest


@pytest.fixture
def admin_user():
    return {"sub": "1", "scope": "admin"}


@pytest.fixture
def supervisor_user():
    return {"sub": "2", "scope": "supervisor"}