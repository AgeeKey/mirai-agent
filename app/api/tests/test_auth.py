import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from mirai_api.main import app


def test_login_success():
    """Test successful login"""
    with patch.dict(os.environ, {"WEB_USER": "testuser", "WEB_PASS": "testpass"}):
        client = TestClient(app)
        response = client.post("/auth/login", json={"username": "testuser", "password": "testpass"})
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    with patch.dict(os.environ, {"WEB_USER": "testuser", "WEB_PASS": "testpass"}):
        client = TestClient(app)
        response = client.post("/auth/login", json={"username": "wrong", "password": "wrong"})
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]


def test_login_no_config():
    """Test login when credentials are not configured"""
    with patch.dict(os.environ, {}, clear=True):
        client = TestClient(app)
        response = client.post("/auth/login", json={"username": "test", "password": "test"})
        
        assert response.status_code == 500
        assert "Authentication not configured" in response.json()["detail"]


def test_protected_route_without_auth():
    """Test accessing protected route without authentication"""
    client = TestClient(app)
    response = client.get("/auth/me")
    
    assert response.status_code == 403  # No auth header


def test_protected_route_with_auth():
    """Test accessing protected route with valid authentication"""
    with patch.dict(os.environ, {"WEB_USER": "testuser", "WEB_PASS": "testpass"}):
        client = TestClient(app)
        
        # Login first
        login_response = client.post("/auth/login", json={"username": "testuser", "password": "testpass"})
        token = login_response.json()["access_token"]
        
        # Use token to access protected route
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["role"] == "admin"


def test_status_endpoint():
    """Test status endpoint with authentication"""
    with patch.dict(os.environ, {"WEB_USER": "testuser", "WEB_PASS": "testpass", "DRY_RUN": "true"}):
        client = TestClient(app)
        
        # Login first
        login_response = client.post("/auth/login", json={"username": "testuser", "password": "testpass"})
        token = login_response.json()["access_token"]
        
        # Access status endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "mode" in data
        assert "testnet" in data
        assert "uptime" in data