from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["device"] == "cpu"


def test_ready():
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["model_loaded"] is True
