"""Smoke test del endpoint /health (no toca OpenAI ni la BD).

Se usa TestClient SIN el context manager para no disparar el lifespan, que
abriría el pool e intentaría conectar a Postgres. /health no usa la BD.
"""

from fastapi.testclient import TestClient

from src.main import app


def test_health():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
