from fastapi.testclient import TestClient

from mirai_api.main import app


def test_healthz():
    c = TestClient(app)
    r = c.get("/healthz")
    assert r.status_code == 200
    assert r.json().get("ok") is True


def test_healthz_head():
    c = TestClient(app)
    r = c.head("/healthz")
    assert r.status_code == 200
