"""
Tests for the Web API
"""

import base64
import os

# Import our FastAPI app
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

app_root = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_root))

from web.api import app

client = TestClient(app)


class TestWebAPI:
    """Test Web API endpoints"""

    def test_status_endpoint_without_auth(self):
        """Test GET /status endpoint without authentication"""
        response = client.get("/status")
        assert response.status_code == 200

        data = response.json()
        assert "date" in data
        assert "mode" in data
        assert "dayPnL" in data
        assert "maxDayPnL" in data
        assert "tradesToday" in data
        assert "consecutiveLosses" in data
        assert "openPositions" in data
        assert "errorsCount" in data
        assert "agentPaused" in data

    def test_metrics_endpoint(self):
        """Test GET /metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "apiLatencyMs" in data
        assert "signalsPerMin" in data
        assert "riskBlocksToday" in data
        assert "openOrders" in data
        assert "uptimeSec" in data
        assert "apiCalls" in data
        assert "errorsCount" in data

    @patch.dict(os.environ, {"WEB_USER": "testuser", "WEB_PASS": "testpass"})
    def test_kill_endpoint_with_auth(self):
        """Test POST /kill endpoint with authentication"""
        # Create basic auth header
        credentials = base64.b64encode(b"testuser:testpass").decode()
        headers = {"Authorization": f"Basic {credentials}"}

        response = client.post("/kill", json={"symbol": "BTCUSDT"}, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["symbol"] == "BTCUSDT"
        assert "timestamp" in data

    def test_kill_endpoint_without_auth(self):
        """Test POST /kill endpoint without authentication"""
        response = client.post("/kill", json={"symbol": "BTCUSDT"})
        assert response.status_code == 401

    @patch.dict(os.environ, {"WEB_USER": "testuser", "WEB_PASS": "testpass"})
    def test_mode_endpoint_with_auth(self):
        """Test POST /mode endpoint with authentication"""
        credentials = base64.b64encode(b"testuser:testpass").decode()
        headers = {"Authorization": f"Basic {credentials}"}

        response = client.post("/mode", json={"mode": "semi"}, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["new_mode"] == "semi"

    @patch.dict(os.environ, {"WEB_USER": "testuser", "WEB_PASS": "testpass"})
    def test_mode_endpoint_invalid_mode(self):
        """Test POST /mode endpoint with invalid mode"""
        credentials = base64.b64encode(b"testuser:testpass").decode()
        headers = {"Authorization": f"Basic {credentials}"}

        response = client.post("/mode", json={"mode": "invalid"}, headers=headers)
        assert response.status_code == 400

        data = response.json()
        assert "error" in data["detail"]

    @patch.dict(os.environ, {"WEB_USER": "testuser", "WEB_PASS": "testpass"})
    def test_pause_resume_endpoints(self):
        """Test POST /pause and /resume endpoints"""
        credentials = base64.b64encode(b"testuser:testpass").decode()
        headers = {"Authorization": f"Basic {credentials}"}

        # Test pause
        response = client.post("/pause", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["paused"] is True

        # Test resume
        response = client.post("/resume", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["paused"] is False


class TestWebUI:
    """Test Web UI endpoints"""

    @patch.dict(os.environ, {"WEB_USER": "testuser", "WEB_PASS": "testpass"})
    def test_dashboard_with_auth(self):
        """Test GET / dashboard endpoint with authentication"""
        credentials = base64.b64encode(b"testuser:testpass").decode()
        headers = {"Authorization": f"Basic {credentials}"}

        response = client.get("/", headers=headers)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Mirai Agent - Web Panel" in response.text

    def test_dashboard_without_auth(self):
        """Test GET / dashboard endpoint without authentication"""
        response = client.get("/")
        assert response.status_code == 401


class TestWebAuthentication:
    """Test Web authentication"""

    def test_no_credentials_configured(self):
        """Test behavior when no credentials are configured"""
        with patch.dict(os.environ, {}, clear=True):
            response = client.post("/kill", json={"symbol": "BTCUSDT"})
            assert response.status_code == 401

            # The response will be 401 when no credentials are configured
            # The exact message may vary based on how FastAPI handles missing auth

    @patch.dict(os.environ, {"WEB_USER": "testuser", "WEB_PASS": "testpass"})
    def test_wrong_credentials(self):
        """Test behavior with wrong credentials"""
        credentials = base64.b64encode(b"wrong:credentials").decode()
        headers = {"Authorization": f"Basic {credentials}"}

        response = client.post("/kill", json={"symbol": "BTCUSDT"}, headers=headers)
        assert response.status_code == 401

        data = response.json()
        assert "Invalid credentials" in data["detail"]
