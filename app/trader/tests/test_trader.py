
"""
Basic tests for trader module
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from binance_client import BinanceClient
from risk_engine import RiskEngine
from orders import OrderManager


class TestBinanceClient(unittest.TestCase):
    """Test cases for BinanceClient"""

    def setUp(self):
        """Set up test environment"""
        self.client = BinanceClient(dry_run=True, testnet=True)

    @patch.dict(os.environ, {"BINANCE_API_KEY": "test_key", "BINANCE_SECRET_KEY": "test_secret"})
    def test_client_initialization_with_keys(self):
        """Test client initialization with API keys"""
        client = BinanceClient(dry_run=False, testnet=True)
        self.assertTrue(hasattr(client, "api_key"))
        self.assertTrue(hasattr(client, "secret_key"))

    def test_client_initialization_without_keys(self):
        """Test client initialization without API keys"""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            client = BinanceClient(dry_run=False, testnet=True)
            self.assertIsNone(client.client)

    def test_dry_run_mode(self):
        """Test dry run mode functionality"""
        client = BinanceClient(dry_run=True, testnet=True)
        self.assertTrue(client.dry_run)
        self.assertTrue(client.testnet)


class TestRiskEngine(unittest.TestCase):
    """Test cases for RiskEngine"""

    def setUp(self):
        """Set up test environment"""
        self.risk_engine = RiskEngine()

    def test_risk_parameters_validation(self):
        """Test risk parameters validation"""
        # Test valid parameters
        valid_params = {
            "max_position_size": 1000,
            "stop_loss_percent": 0.02,
            "max_drawdown": 0.1
        }
        self.assertTrue(self.risk_engine.validate_risk_parameters(valid_params))

        # Test invalid parameters
        invalid_params = {
            "max_position_size": -100,
            "stop_loss_percent": 0.02,
            "max_drawdown": 0.1
        }
        self.assertFalse(self.risk_engine.validate_risk_parameters(invalid_params))

    def test_position_sizing(self):
        """Test position size calculation"""
        account_balance = 10000
        risk_percent = 0.02
        expected_position_size = account_balance * risk_percent

        position_size = self.risk_engine.calculate_position_size(account_balance, risk_percent)
        self.assertEqual(position_size, expected_position_size)


class TestOrderManager(unittest.TestCase):
    """Test cases for OrderManager"""

    def setUp(self):
        """Set up test environment"""
        self.order_manager = OrderManager()
        self.mock_client = MagicMock()
        self.order_manager.client = self.mock_client

    def test_order_creation(self):
        """Test order creation"""
        order_data = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "LIMIT",
            "quantity": 0.001,
            "price": 30000
        }

        # Mock the response
        self.mock_client.create_order.return_value = {"orderId": 12345}

        order = self.order_manager.create_order(order_data)
        self.assertIsNotNone(order)
        self.mock_client.create_order.assert_called_once_with(**order_data)

    def test_order_cancellation(self):
        """Test order cancellation"""
        order_id = 12345
        symbol = "BTCUSDT"

        # Mock the response
        self.mock_client.cancel_order.return_value = {"orderId": order_id, "status": "CANCELED"}

        result = self.order_manager.cancel_order(order_id, symbol)
        self.assertEqual(result["status"], "CANCELED")
        self.mock_client.cancel_order.assert_called_once_with(symbol=symbol, orderId=order_id)


if __name__ == "__main__":
    unittest.main()
