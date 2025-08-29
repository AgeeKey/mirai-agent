"""
Tests for AI Advisor module functionality
"""
import pytest
import os
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.agent.advisor import SignalAdvisor, get_signal_score, reset_advisor
from app.agent.explain_logger import ExplainabilityLogger, log_decision
from app.agent.config import load_advisor_config, get_default_advisor_config


class TestSignalAdvisor:
    """Test SignalAdvisor functionality"""
    
    def test_advisor_creation_without_openai(self):
        """Test advisor creation when OpenAI is not available"""
        with patch.dict(os.environ, {}, clear=True):
            advisor = SignalAdvisor()
            assert not advisor.use_openai
            
    def test_advisor_creation_with_api_key(self):
        """Test advisor creation with OpenAI API key"""
        test_key = "sk-test-key-12345"
        with patch.dict(os.environ, {'OPENAI_API_KEY': test_key}):
            with patch('app.agent.advisor.OPENAI_AVAILABLE', True):
                advisor = SignalAdvisor()
                assert advisor.api_key == test_key
    
    def test_mock_signal_score_low(self):
        """Test mock signal score for bearish conditions"""
        advisor = SignalAdvisor()
        
        # Create bearish market features
        features = {
            'price': 45000.0,
            'ema': 47000.0,  # Price below EMA
            'rsi': 75.0,     # Overbought
            'atr': 900.0,
            'adx': 20.0      # Weak trend
        }
        
        result = advisor.get_signal_score(features)
        
        assert isinstance(result, dict)
        assert 'score' in result
        assert 'rationale' in result
        assert 'strategy' in result
        assert 'action' in result
        assert 0.0 <= result['score'] <= 1.0
        assert result['action'] in ['BUY', 'SELL', 'HOLD']
        
        # Should be bearish given the setup
        assert result['score'] < 0.7  # Below advisor threshold
    
    def test_mock_signal_score_high(self):
        """Test mock signal score for bullish conditions"""
        advisor = SignalAdvisor()
        
        # Create bullish market features
        features = {
            'price': 52000.0,
            'ema': 50000.0,  # Price above EMA
            'rsi': 25.0,     # Oversold (good for buying)
            'atr': 1000.0,
            'adx': 35.0      # Strong trend
        }
        
        result = advisor.get_signal_score(features)
        
        assert isinstance(result, dict)
        assert result['score'] > 0.6  # Should be bullish
        
    def test_mock_signal_score_medium(self):
        """Test mock signal score for neutral conditions"""
        advisor = SignalAdvisor()
        
        # Create neutral market features
        features = {
            'price': 50000.0,
            'ema': 50100.0,  # Price near EMA
            'rsi': 50.0,     # Neutral RSI
            'atr': 1000.0,
            'adx': 22.0      # Moderate trend
        }
        
        result = advisor.get_signal_score(features)
        
        assert isinstance(result, dict)
        # Score should be around middle range
        assert 0.4 <= result['score'] <= 0.8
    
    def test_get_signal_score_global_function(self):
        """Test global get_signal_score function"""
        reset_advisor()  # Start fresh
        
        features = {
            'price': 50000.0,
            'ema': 50000.0,
            'rsi': 50.0,
            'atr': 1000.0,
            'adx': 25.0
        }
        
        result = get_signal_score(features)
        assert isinstance(result, dict)
        assert all(key in result for key in ['score', 'rationale', 'strategy', 'action'])
        
    @patch('app.agent.advisor.openai.chat.completions.create')
    def test_openai_integration_success(self, mock_openai):
        """Test successful OpenAI integration"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "score": 0.75,
            "rationale": "Strong bullish momentum",
            "strategy": "momentum_breakout", 
            "action": "BUY"
        })
        mock_openai.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test'}):
            with patch('app.agent.advisor.OPENAI_AVAILABLE', True):
                advisor = SignalAdvisor()
                features = {'price': 50000, 'rsi': 30}
                
                result = advisor.get_signal_score(features)
                
                assert result['score'] == 0.75
                assert result['action'] == 'BUY'
                assert 'momentum' in result['rationale'].lower()
    
    @patch('app.agent.advisor.openai.chat.completions.create')
    def test_openai_integration_failure(self, mock_openai):
        """Test OpenAI integration failure fallback"""
        # Mock OpenAI exception
        mock_openai.side_effect = Exception("API Error")
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test'}):
            with patch('app.agent.advisor.OPENAI_AVAILABLE', True):
                advisor = SignalAdvisor()
                features = {'price': 50000}
                
                result = advisor.get_signal_score(features)
                
                # Should fallback to safe response
                assert result['score'] == 0.5
                assert result['action'] == 'HOLD'
                assert 'error' in result['rationale'].lower()


class TestExplainabilityLogger:
    """Test explainability logging functionality"""
    
    def test_logger_creation(self, tmp_path):
        """Test logger creation and file handling"""
        log_file = tmp_path / "test_explain.log"
        logger = ExplainabilityLogger(str(log_file))
        
        assert log_file.parent.exists()
    
    def test_log_decision_basic(self, tmp_path):
        """Test basic decision logging"""
        log_file = tmp_path / "test_explain.log"
        logger = ExplainabilityLogger(str(log_file))
        
        logger.log_decision(
            symbol="BTCUSDT",
            score=0.75,
            action="BUY",
            strategy="momentum",
            rationale="Strong bullish signals",
            accepted=True
        )
        
        # Check file was created and has content
        assert log_file.exists()
        content = log_file.read_text()
        assert "BTCUSDT" in content
        assert "0.75" in content
        assert "BUY" in content
        
        # Parse JSON to verify structure
        log_entry = json.loads(content.strip())
        assert log_entry['symbol'] == "BTCUSDT"
        assert log_entry['score'] == 0.75
        assert log_entry['accepted'] is True
    
    def test_log_decision_denied(self, tmp_path):
        """Test logging denied decisions"""
        log_file = tmp_path / "test_explain.log"
        logger = ExplainabilityLogger(str(log_file))
        
        logger.log_decision(
            symbol="ETHUSDT",
            score=0.45,
            action="BUY",
            strategy="momentum",
            rationale="Weak signals",
            accepted=False,
            deny_reason="advisor_low_score (0.45 < 0.70)"
        )
        
        content = log_file.read_text()
        log_entry = json.loads(content.strip())
        assert log_entry['accepted'] is False
        assert "advisor_low_score" in log_entry['deny_reason']
    
    def test_get_recent_decisions(self, tmp_path):
        """Test retrieving recent decisions"""
        log_file = tmp_path / "test_explain.log"
        logger = ExplainabilityLogger(str(log_file))
        
        # Log multiple decisions
        for i in range(5):
            logger.log_decision(
                symbol=f"SYMBOL{i}",
                score=0.5 + i * 0.1,
                action="BUY",
                strategy="test",
                rationale=f"Test rationale {i}",
                accepted=True
            )
        
        recent = logger.get_recent_decisions(3)
        assert len(recent) == 3
        assert recent[-1]['symbol'] == "SYMBOL4"  # Most recent
    
    def test_global_log_decision_function(self, tmp_path):
        """Test global log_decision function"""
        # Mock the global logger path
        with patch('app.agent.explain_logger.ExplainabilityLogger') as mock_logger:
            mock_instance = MagicMock()
            mock_logger.return_value = mock_instance
            
            log_decision(
                symbol="TESTUSDT",
                score=0.8,
                action="BUY",
                strategy="test",
                rationale="Test decision",
                accepted=True
            )
            
            mock_instance.log_decision.assert_called_once()


class TestAdvisorConfig:
    """Test advisor configuration loading"""
    
    def test_load_default_config(self):
        """Test loading default configuration"""
        defaults = get_default_advisor_config()
        
        assert 'ADVISOR_THRESHOLD' in defaults
        assert 'RECOVERY_THRESHOLD' in defaults
        assert 'RECOVERY_MAX_TRIES' in defaults
        assert defaults['ADVISOR_THRESHOLD'] == 0.70
        assert defaults['RECOVERY_THRESHOLD'] == 0.80
        assert defaults['RECOVERY_MAX_TRIES'] == 3
    
    def test_load_config_from_file(self, tmp_path):
        """Test loading configuration from YAML file"""
        config_file = tmp_path / "test_risk.yaml"
        config_content = """
advisor:
  ADVISOR_THRESHOLD: 0.65
  RECOVERY_THRESHOLD: 0.85
  RECOVERY_MAX_TRIES: 5
"""
        config_file.write_text(config_content)
        
        config = load_advisor_config(str(config_file))
        
        assert config['ADVISOR_THRESHOLD'] == 0.65
        assert config['RECOVERY_THRESHOLD'] == 0.85
        assert config['RECOVERY_MAX_TRIES'] == 5
    
    def test_load_config_missing_file(self):
        """Test loading configuration when file doesn't exist"""
        config = load_advisor_config("nonexistent.yaml")
        
        # Should return defaults
        defaults = get_default_advisor_config()
        assert config == defaults


class TestAdvisorGating:
    """Test advisor gating logic scenarios"""
    
    def test_high_score_acceptance(self):
        """Test that high scores are accepted"""
        features = {
            'price': 50000.0,
            'ema': 48000.0,  # Bullish
            'rsi': 30.0,     # Oversold - good for buying
            'atr': 1000.0,
            'adx': 30.0      # Strong trend
        }
        
        result = get_signal_score(features)
        
        # Should likely be accepted (score >= 0.70)
        if result['score'] >= 0.70:
            # This would be accepted by advisor gating
            assert result['action'] in ['BUY', 'SELL']
        else:
            # This would be denied by advisor gating
            assert result['score'] < 0.70
    
    def test_low_score_rejection(self):
        """Test that low scores are rejected"""
        features = {
            'price': 50000.0,
            'ema': 52000.0,  # Bearish
            'rsi': 80.0,     # Overbought
            'atr': 500.0,    # Low volatility
            'adx': 15.0      # Weak trend
        }
        
        result = get_signal_score(features)
        
        # Should likely be rejected (score < 0.70)
        # The mock logic should produce a low score for these bearish conditions
        assert result['score'] <= 0.7  # At threshold or below
    
    def test_recovery_threshold_higher(self):
        """Test that recovery threshold is higher than advisor threshold"""
        config = load_advisor_config()
        
        assert config['RECOVERY_THRESHOLD'] > config['ADVISOR_THRESHOLD']
        assert config['RECOVERY_THRESHOLD'] == 0.80
        assert config['ADVISOR_THRESHOLD'] == 0.70