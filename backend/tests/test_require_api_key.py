"""Tests de require_api_key: inerte sin CHAT_API_KEY, timing-safe con ella.

El caso clave es x_api_key=None con CHAT_API_KEY configurada: no debe lanzar
TypeError (compare_digest no acepta None) sino HTTPException 401.
"""

import pytest
from fastapi import HTTPException

from src.api import dependencies
from src.core.config import settings


def test_inerte_sin_clave(monkeypatch):
    monkeypatch.setattr(settings, "CHAT_API_KEY", None)
    # No debe lanzar nada.
    assert dependencies.require_api_key(x_api_key="lo-que-sea") is None
    assert dependencies.require_api_key(x_api_key=None) is None


def test_clave_correcta_ok(monkeypatch):
    monkeypatch.setattr(settings, "CHAT_API_KEY", "secreta")
    assert dependencies.require_api_key(x_api_key="secreta") is None


def test_clave_incorrecta_401(monkeypatch):
    monkeypatch.setattr(settings, "CHAT_API_KEY", "secreta")
    with pytest.raises(HTTPException) as exc:
        dependencies.require_api_key(x_api_key="mala")
    assert exc.value.status_code == 401


def test_clave_none_401_sin_typeerror(monkeypatch):
    monkeypatch.setattr(settings, "CHAT_API_KEY", "secreta")
    with pytest.raises(HTTPException) as exc:
        dependencies.require_api_key(x_api_key=None)
    assert exc.value.status_code == 401
