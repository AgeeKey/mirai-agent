
"""
Basic tests for API module
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from mirai_api.main import app


class TestMiraiAPI(unittest.TestCase):
    """Test cases for Mirai API"""

    def setUp(self):
        """Set up test environment"""
        self.client = TestClient(app)
        # Mock JWT secret for testing
        os.environ["JWT_SECRET"] = "test-secret-key"

    def test_health_endpoint(self):
        """Test health endpoint"""
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["service"], "mirai-api")

    def test_login_endpoint(self):
        """Test login endpoint"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = self.client.post("/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())

    def test_protected_endpoint_without_token(self):
        """Test protected endpoint without token"""
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 403)

    @patch('mirai_api.main.verify_token')
    def test_protected_endpoint_with_valid_token(self, mock_verify_token):
        """Test protected endpoint with valid token"""
        # Mock token verification
        mock_verify_token.return_value = {"sub": "admin", "role": "admin"}

        # Create a mock token
        headers = {"Authorization": "Bearer mock-token"}

        response = self.client.get("/dashboard", headers=headers)
        self.assertEqual(response.status_code, 200)

    @patch('mirai_api.main.verify_token')
    def test_protected_endpoint_with_invalid_token(self, mock_verify_token):
        """Test protected endpoint with invalid token"""
        # Mock token verification to raise an exception
        mock_verify_token.side_effect = Exception("Invalid token")

        # Create a mock token
        headers = {"Authorization": "Bearer invalid-token"}

        response = self.client.get("/dashboard", headers=headers)
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
