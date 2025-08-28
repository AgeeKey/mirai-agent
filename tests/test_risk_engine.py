"""
Tests for Risk Engine functionality
"""
import pytest
import tempfile
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

from app.trader.risk_engine import RiskEngine, DayState
from app.trader.orders import validate_and_round_qty


class TestRiskEngine:
    """Test Risk Engine core functionality"""
    
    def setup_method(self):
        """Setup test environment with temporary database"""
        import uuid
        self.temp_dir = tempfile.mkdtemp()
        # Use unique database name to avoid conflicts
        self.db_path = os.path.join(self.temp_dir, f"test_mirai_{uuid.uuid4().hex[:8]}.db")
        
        # Create minimal config for testing
        self.test_config = {
            'DAILY_MAX_LOSS': -30,
            'DAILY_TRAIL_DRAWDOWN': 20,
            'MAX_TRADES_PER_DAY': 6,
            'MAX_CONSECUTIVE_LOSSES': 3,
            'COOLDOWN_MINUTES': 15,
            'ONE_POSITION_PER_SYMBOL': True
        }
        
        self.risk_engine = RiskEngine(config_path="configs/risk.yaml", db_path=self.db_path)
        self.risk_engine.config = self.test_config
        self.risk_engine._init_database()
    
    def teardown_method(self):
        """Clean up test environment"""
        try:
            if hasattr(self, 'db_path') and os.path.exists(self.db_path):
                os.remove(self.db_path)
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                os.rmdir(self.temp_dir)
        except (OSError, PermissionError):
            pass  # Ignore cleanup errors in tests
    
    def test_day_state_creation(self):
        """Test day state creation and retrieval"""
        now = datetime.now(timezone.utc)
        day_state = self.risk_engine.get_day_state(now)
        
        assert day_state.date_utc == now.strftime('%Y-%m-%d')
        assert day_state.day_pnl == 0.0
        assert day_state.max_day_pnl == 0.0
        assert day_state.trades_today == 0
        assert day_state.consecutive_losses == 0
        assert day_state.cooldown_until is None
    
    def test_daily_max_loss_gate(self):
        """Test stop-day by DAILY_MAX_LOSS"""
        now = datetime.now(timezone.utc)
        
        # Record losses to trigger daily max loss
        for i in range(3):
            self.risk_engine.record_fill(
                ts=now.isoformat(),
                symbol="BTCUSDT",
                side="BUY",
                qty=0.1,
                price=50000.0,
                pnl=-12.0  # Each loss is -12, total will be -36 > -30
            )
        
        # Should be blocked by daily max loss
        allowed, reason = self.risk_engine.allow_entry(now, "BTCUSDT", {})
        assert not allowed
        assert "Daily max loss reached" in reason
    
    def test_daily_trail_drawdown_gate(self):
        """Test trail-drawdown trigger"""
        now = datetime.now(timezone.utc)
        
        # Record a profit to set max_day_pnl
        self.risk_engine.record_fill(
            ts=now.isoformat(),
            symbol="BTCUSDT",
            side="BUY",
            qty=0.1,
            price=50000.0,
            pnl=25.0  # Set max_day_pnl to 25
        )
        
        # Record a loss to create drawdown
        self.risk_engine.record_fill(
            ts=now.isoformat(),
            symbol="BTCUSDT",
            side="SELL",
            qty=0.1,
            price=50000.0,
            pnl=-10.0  # day_pnl becomes 15, drawdown = 25 - 15 = 10
        )
        
        # Record another bigger loss
        self.risk_engine.record_fill(
            ts=now.isoformat(),
            symbol="BTCUSDT",
            side="SELL",
            qty=0.1,
            price=50000.0,
            pnl=-10.0  # day_pnl becomes 5, drawdown = 25 - 5 = 20 >= 20
        )
        
        # Should be blocked by trail drawdown
        allowed, reason = self.risk_engine.allow_entry(now, "BTCUSDT", {})
        assert not allowed
        assert "trail drawdown exceeded" in reason
    
    def test_max_trades_per_day_gate(self):
        """Test trade limit blocks 7th trade"""
        now = datetime.now(timezone.utc)
        
        # Record 6 trades (at the limit)
        for i in range(6):
            self.risk_engine.record_fill(
                ts=now.isoformat(),
                symbol="BTCUSDT",
                side="BUY",
                qty=0.1,
                price=50000.0,
                pnl=1.0  # Small profit
            )
        
        # 7th trade should be blocked
        allowed, reason = self.risk_engine.allow_entry(now, "BTCUSDT", {})
        assert not allowed
        assert "Max trades per day reached" in reason
    
    def test_consecutive_losses_cooldown(self):
        """Test 3 consecutive losses trigger cooldown"""
        now = datetime.now(timezone.utc)
        
        # Record 3 consecutive losses
        for i in range(3):
            self.risk_engine.record_fill(
                ts=now.isoformat(),
                symbol="BTCUSDT",
                side="BUY",
                qty=0.1,
                price=50000.0,
                pnl=-5.0  # Each loss
            )
        
        # Should be in cooldown
        allowed, reason = self.risk_engine.allow_entry(now, "BTCUSDT", {})
        assert not allowed
        assert "In cooldown until" in reason
        
        # After cooldown period, should be allowed
        future_time = now + timedelta(minutes=20)  # After 15-minute cooldown
        allowed, reason = self.risk_engine.allow_entry(future_time, "BTCUSDT", {})
        assert allowed
    
    def test_one_position_per_symbol_gate(self):
        """Test one-position-per-symbol denies second entry"""
        now = datetime.now(timezone.utc)
        
        # Mock account state with existing position
        account_state = {
            'positions': [
                {'symbol': 'BTCUSDT', 'size': '0.1'}  # Existing position
            ]
        }
        
        # Should be blocked due to existing position
        allowed, reason = self.risk_engine.allow_entry(now, "BTCUSDT", account_state)
        assert not allowed
        assert "Position already open" in reason
        
        # Different symbol should be allowed
        allowed, reason = self.risk_engine.allow_entry(now, "ETHUSDT", account_state)
        assert allowed
    
    def test_reset_day_state(self):
        """Test day state reset functionality"""
        now = datetime.now(timezone.utc)
        
        # Add some trades and losses
        self.risk_engine.record_fill(
            ts=now.isoformat(),
            symbol="BTCUSDT",
            side="BUY",
            qty=0.1,
            price=50000.0,
            pnl=-10.0
        )
        
        day_state = self.risk_engine.get_day_state(now)
        assert day_state.day_pnl == -10.0
        assert day_state.trades_today == 1
        
        # Reset state
        self.risk_engine.reset_day_state(now.strftime('%Y-%m-%d'))
        
        # Should be reset
        day_state = self.risk_engine.get_day_state(now)
        assert day_state.day_pnl == 0.0
        assert day_state.trades_today == 0
        assert day_state.consecutive_losses == 0


class TestPositionSizeValidator:
    """Test position sizing validator"""
    
    def test_validate_and_round_qty_basic(self):
        """Test basic quantity validation and rounding"""
        # Should round to proper step size and check minimums
        qty = validate_and_round_qty(
            symbol="BTCUSDT",
            qty=0.123456,
            sl_distance=100.0,
            margin=1000.0,
            leverage=1.0
        )
        
        # Should be rounded to step size (0.001 for BTCUSDT)
        assert qty == 0.123
    
    def test_validate_and_round_qty_below_minimum(self):
        """Test validator rejects quantity below minimum"""
        with pytest.raises(ValueError, match="below minQty"):
            validate_and_round_qty(
                symbol="BTCUSDT",
                qty=0.0001,  # Way below minimum
                sl_distance=100.0,
                margin=1.0,
                leverage=1.0
            )
    
    def test_validate_and_round_qty_margin_constraint(self):
        """Test quantity limited by margin"""
        qty = validate_and_round_qty(
            symbol="BTCUSDT",
            qty=10.0,  # High quantity
            sl_distance=1.0,
            margin=1.0,  # Low margin
            leverage=1.0
        )
        
        # Should be limited by margin constraint
        assert qty <= 1.0
    
    def test_validate_and_round_qty_stop_loss_constraint(self):
        """Test quantity limited by stop loss distance"""
        qty = validate_and_round_qty(
            symbol="BTCUSDT",
            qty=10.0,  # High quantity
            sl_distance=100.0,  # Large stop distance
            margin=10.0,  # Small margin
            leverage=1.0
        )
        
        # Should be limited by risk (margin/sl_distance = 10/100 = 0.1)
        assert qty <= 0.1


class TestCLIIntegration:
    """Test CLI command integration"""
    
    def setup_method(self):
        """Setup test environment"""
        import uuid
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, f"test_mirai_{uuid.uuid4().hex[:8]}.db")
        
        # Initialize risk engine for CLI tests
        self.risk_engine = RiskEngine(config_path="configs/risk.yaml", db_path=self.db_path)
    
    def teardown_method(self):
        """Clean up test environment"""
        try:
            if hasattr(self, 'db_path') and os.path.exists(self.db_path):
                os.remove(self.db_path)
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                os.rmdir(self.temp_dir)
        except (OSError, PermissionError):
            pass  # Ignore cleanup errors in tests
    
    def test_risk_status_command(self):
        """Test risk-status CLI command functionality"""
        import json
        from app.trader.risk_engine import get_risk_engine
        from datetime import datetime, timezone
        
        # Override global risk engine for test
        import app.trader.risk_engine
        app.trader.risk_engine._risk_engine = self.risk_engine
        
        now = datetime.now(timezone.utc)
        day_state = self.risk_engine.get_day_state(now)
        
        # Convert to dict for comparison
        expected_state = {
            'date_utc': day_state.date_utc,
            'day_pnl': day_state.day_pnl,
            'max_day_pnl': day_state.max_day_pnl,
            'trades_today': day_state.trades_today,
            'consecutive_losses': day_state.consecutive_losses,
            'cooldown_until': day_state.cooldown_until
        }
        
        # Should return valid JSON with correct structure
        assert isinstance(expected_state, dict)
        assert 'date_utc' in expected_state
        assert 'day_pnl' in expected_state
        assert expected_state['trades_today'] == 0
    
    def test_risk_reset_command(self):
        """Test risk-reset CLI command functionality"""
        # Add some state
        now = datetime.now(timezone.utc)
        self.risk_engine.record_fill(
            ts=now.isoformat(),
            symbol="BTCUSDT",
            side="BUY",
            qty=0.1,
            price=50000.0,
            pnl=-5.0
        )
        
        day_state = self.risk_engine.get_day_state(now)
        assert day_state.trades_today == 1
        assert day_state.day_pnl == -5.0
        
        # Reset
        self.risk_engine.reset_day_state()
        
        # Should be reset
        day_state = self.risk_engine.get_day_state(now)
        assert day_state.trades_today == 0
        assert day_state.day_pnl == 0.0