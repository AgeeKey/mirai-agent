import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from mirai_api.main import app


def get_auth_headers():
    """Helper to get auth headers for testing"""
    with patch.dict(os.environ, {"WEB_USER": "testuser", "WEB_PASS": "testpass"}):
        client = TestClient(app)
        login_response = client.post("/auth/login", json={"username": "testuser", "password": "testpass"})
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}


def test_get_risk_config():
    """Test getting risk configuration"""
    with patch.dict(os.environ, {"WEB_USER": "testuser", "WEB_PASS": "testpass"}):
        client = TestClient(app)
        headers = get_auth_headers()

        response = client.get("/risk/config", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "MAX_TRADES_PER_DAY" in data
        assert "COOLDOWN_SEC" in data
        assert "DAILY_MAX_LOSS_USDT" in data
        assert "ADVISOR_THRESHOLD" in data


def test_update_risk_config():
    """Test updating risk configuration"""
    with patch.dict(os.environ, {"WEB_USER": "testuser", "WEB_PASS": "testpass"}):
        client = TestClient(app)
        headers = get_auth_headers()

        update_data = {"MAX_TRADES_PER_DAY": 15, "ADVISOR_THRESHOLD": 0.7}
        response = client.patch("/risk/config", json=update_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["MAX_TRADES_PER_DAY"] == 15
        assert data["ADVISOR_THRESHOLD"] == 0.7


def test_get_recent_orders():
    """Test getting recent orders"""
    with patch.dict(os.environ, {"WEB_USER": "testuser", "WEB_PASS": "testpass"}):
        client = TestClient(app)
        headers = get_auth_headers()

        response = client.get("/orders/recent", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert "total" in data
        assert "limit" in data


def test_get_active_orders():
    """Test getting active orders"""
    with patch.dict(os.environ, {"WEB_USER": "testuser", "WEB_PASS": "testpass"}):
        client = TestClient(app)
        headers = get_auth_headers()

        response = client.get("/orders/active", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert "total" in data


def test_get_logs_tail():
    """Test getting log tail"""
    with patch.dict(os.environ, {"WEB_USER": "testuser", "WEB_PASS": "testpass"}):
        client = TestClient(app)
        headers = get_auth_headers()

        response = client.get("/logs/tail?lines=50", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "lines" in data
