
"""
Basic tests for agent module
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from loop import AgentLoop
from schema import AgentDecision, RiskParameters


class TestAgentLoop(unittest.TestCase):
    """Test cases for AgentLoop"""

    def setUp(self):
        """Set up test environment"""
        self.mock_client = MagicMock()
        self.risk_params = RiskParameters()
        self.agent = AgentLoop(self.mock_client, self.risk_params)

    def test_agent_initialization(self):
        """Test agent initialization"""
        self.assertIsNotNone(self.agent.trading_client)
        self.assertIsNotNone(self.agent.risk_params)
        self.assertFalse(self.agent.paused)
        self.assertEqual(len(self.agent.decision_history), 0)

    def test_agent_pause_resume(self):
        """Test agent pause and resume functionality"""
        # Test pause
        self.agent.pause()
        self.assertTrue(self.agent.paused)

        # Test resume
        self.agent.resume()
        self.assertFalse(self.agent.paused)

    @patch('agent.loop.get_signal_score')
    def test_agent_decision_making(self, mock_get_signal_score):
        """Test agent decision making process"""
        # Mock the advisor response
        mock_get_signal_score.return_value = {"signal": "BUY", "confidence": 0.8}

        # Create mock market data
        market_data = {
            "symbol": "BTCUSDT",
            "price": 30000,
            "volume": 1000000
        }

        # Make a decision
        decision = self.agent.make_decision(market_data)

        # Verify decision
        self.assertIsInstance(decision, AgentDecision)
        self.assertEqual(decision.action, "BUY")
        self.assertEqual(decision.confidence, 0.8)


class TestAgentDecision(unittest.TestCase):
    """Test cases for AgentDecision schema"""

    def test_agent_decision_creation(self):
        """Test AgentDecision creation and validation"""
        decision = AgentDecision(
            symbol="BTCUSDT",
            action="BUY",
            price=30000,
            quantity=0.001,
            confidence=0.8,
            timestamp="2023-01-01T00:00:00Z"
        )

        self.assertEqual(decision.symbol, "BTCUSDT")
        self.assertEqual(decision.action, "BUY")
        self.assertEqual(decision.price, 30000)
        self.assertEqual(decision.quantity, 0.001)
        self.assertEqual(decision.confidence, 0.8)


if __name__ == "__main__":
    unittest.main()
