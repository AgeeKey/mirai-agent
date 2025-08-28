"""
Tests for the agent module
"""
import pytest
from datetime import datetime

from app.agent.schema import AgentDecision, MarketData, RiskParameters
from app.agent.policy import MockLLMPolicy
from app.agent.loop import AgentLoop


class TestAgentSchemas:
    def test_agent_decision_creation(self):
        """Test AgentDecision schema validation"""
        decision = AgentDecision(
            score=0.8,
            rationale="Test rationale",
            intent="BUY",
            action="MARKET_BUY",
            quantity=0.5
        )
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
            timestamp=datetime.utcnow()
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
            timestamp=datetime.utcnow()
        )
        
        decision = self.policy.analyze_market(market_data)
        
        assert isinstance(decision, AgentDecision)
        assert 0 <= decision.score <= 1
        assert decision.intent in ["BUY", "SELL", "HOLD"]
        assert decision.action in ["MARKET_BUY", "MARKET_SELL", "LIMIT_BUY", "LIMIT_SELL", "HOLD"]
    
    def test_evaluate_risk(self):
        """Test risk evaluation"""
        decision = AgentDecision(
            score=0.8,
            rationale="Test",
            intent="BUY",
            action="MARKET_BUY",
            quantity=0.5
        )
        
        risk_ok = self.policy.evaluate_risk(decision)
        assert isinstance(risk_ok, bool)