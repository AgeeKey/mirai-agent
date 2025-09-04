"""
Tests for the agent module
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

from app.agent.loop import AgentLoop
from app.agent.policy import MockLLMPolicy
from app.agent.schema import AgentDecision, MarketData


class TestAgentSchemas:
    def test_agent_decision_creation(self):
        """Test AgentDecision schema validation"""
        decision = AgentDecision(score=0.8, rationale="Test rationale", intent="BUY", action="MARKET_BUY", quantity=0.5)
        assert decision.score == 0.8
        assert decision.intent == "BUY"
        assert decision.action == "MARKET_BUY"

    def test_market_data_creation(self):
        """Test MarketData schema validation"""
        market_data = MarketData(
            symbol="BTCUSDT",
            price=45000.0,
            volume=1000000.0,
            change_24h=0.05,
            timestamp=datetime.now(timezone.utc),
        )
        assert market_data.symbol == "BTCUSDT"
        assert market_data.price == 45000.0


class TestMockLLMPolicy:
    def setup_method(self):
        self.policy = MockLLMPolicy()

    def test_analyze_market(self):
        """Test market analysis returns valid decision"""
        market_data = MarketData(
            symbol="BTCUSDT",
            price=45000.0,
            volume=1000000.0,
            change_24h=0.05,
            timestamp=datetime.now(timezone.utc),
        )

        decision = self.policy.analyze_market(market_data)

        assert isinstance(decision, AgentDecision)
        assert 0 <= decision.score <= 1
        assert decision.intent in ["BUY", "SELL", "HOLD"]
        assert decision.action in ["MARKET_BUY", "MARKET_SELL", "LIMIT_BUY", "LIMIT_SELL", "HOLD"]

    def test_evaluate_risk(self):
        """Test risk evaluation"""
        decision = AgentDecision(score=0.8, rationale="Test", intent="BUY", action="MARKET_BUY", quantity=0.5)

        risk_ok = self.policy.evaluate_risk(decision)
        assert isinstance(risk_ok, bool)


class TestAgentLoopWithAdvisor:
    """Test AgentLoop with AI Advisor integration"""

    def test_agent_loop_creation_with_advisor(self):
        """Test that AgentLoop loads advisor configuration"""
        mock_client = Mock()
        mock_client.get_market_data.return_value = {
            "price": 50000.0,
            "volume": 1000000.0,
            "change_24h": 0.02,
        }

        agent_loop = AgentLoop(mock_client)

        # Check advisor config is loaded
        assert hasattr(agent_loop, "advisor_config")
        assert "ADVISOR_THRESHOLD" in agent_loop.advisor_config
        assert "RECOVERY_THRESHOLD" in agent_loop.advisor_config
        assert "RECOVERY_MAX_TRIES" in agent_loop.advisor_config

        # Check advisor state is initialized
        assert hasattr(agent_loop, "latest_advisor_result")
        assert hasattr(agent_loop, "recovery_tries")
        assert agent_loop.recovery_tries == 0

    @patch("app.agent.loop.get_signal_score")
    @patch("app.agent.loop.get_risk_engine")
    def test_advisor_high_score_acceptance(self, mock_risk_engine, mock_get_signal_score):
        """Test that high advisor scores allow trades"""
        # Mock advisor response with high score
        mock_get_signal_score.return_value = {
            "score": 0.85,
            "rationale": "Strong bullish momentum",
            "strategy": "momentum_breakout",
            "action": "BUY",
        }

        # Mock risk engine to allow trades
        mock_risk_instance = Mock()
        mock_risk_instance.get_day_state.return_value = Mock(consecutive_losses=0)
        mock_risk_instance.allow_entry.return_value = (True, "allowed")
        mock_risk_engine.return_value = mock_risk_instance

        # Mock client
        mock_client = Mock()
        mock_client.get_market_data.return_value = {
            "price": 50000.0,
            "volume": 1000000.0,
            "change_24h": 0.02,
        }
        mock_client.get_account_info.return_value = {}

        agent_loop = AgentLoop(mock_client)
        decision = agent_loop.make_decision("BTCUSDT")

        # Should allow trade with high score
        assert decision["advisor_score"] == 0.85
        assert "advisor_rationale" in decision
        # The actual action depends on the base policy, but advisor should be recorded
        assert decision["advisor_action"] == "BUY"

    @patch("app.agent.loop.get_signal_score")
    @patch("app.agent.loop.get_risk_engine")
    def test_advisor_low_score_rejection(self, mock_risk_engine, mock_get_signal_score):
        """Test that low advisor scores block trades"""
        # Mock advisor response with low score
        mock_get_signal_score.return_value = {
            "score": 0.45,  # Below 0.70 threshold
            "rationale": "Weak market signals",
            "strategy": "wait_and_see",
            "action": "HOLD",
        }

        # Mock risk engine
        mock_risk_instance = Mock()
        mock_risk_instance.get_day_state.return_value = Mock(consecutive_losses=0)
        mock_risk_instance.allow_entry.return_value = (True, "allowed")
        mock_risk_engine.return_value = mock_risk_instance

        # Mock client
        mock_client = Mock()
        mock_client.get_market_data.return_value = {
            "price": 50000.0,
            "volume": 1000000.0,
            "change_24h": 0.02,
        }

        # Mock the policy to return a BUY decision that should be overridden
        with patch.object(MockLLMPolicy, "analyze_market") as mock_analyze:
            mock_analyze.return_value = AgentDecision(
                score=0.8, rationale="Mock policy says BUY", intent="BUY", action="MARKET_BUY"
            )

            agent_loop = AgentLoop(mock_client)
            decision = agent_loop.make_decision("BTCUSDT")

            # Should be overridden to HOLD due to low advisor score
            assert decision["action"] == "HOLD"
            assert decision["advisor_score"] == 0.45
            assert "advisor denied" in decision["rationale"].lower()

    def test_get_advisor_state(self):
        """Test getting advisor state"""
        mock_client = Mock()
        agent_loop = AgentLoop(mock_client)

        # Initially no advisor result
        state = agent_loop.get_advisor_state()
        assert state["score"] == 0.0
        assert state["rationale"] == "No advisor analysis yet"

        # After setting advisor result
        agent_loop.latest_advisor_result = {
            "score": 0.8,
            "rationale": "Test rationale",
            "strategy": "test_strategy",
            "action": "BUY",
        }

        state = agent_loop.get_advisor_state()
        assert state["score"] == 0.8
        assert state["rationale"] == "Test rationale"
        assert state["recovery_tries"] == 0
