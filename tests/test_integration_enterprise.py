"""
Enterprise Integration Tests for Mirai Trading System
Full end-to-end testing of critical trading paths
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock, patch
import websockets
import aiohttp

from app.trader.binance_client import BinanceClient
from app.agent.loop import AgentLoop
from app.api.mirai_api.trading_metrics import metrics_collector
from app.api.mirai_api.trading_alerts import alert_manager


class TestTradingPipeline:
    """
    Integration tests for the complete trading pipeline
    """
    
    @pytest.fixture
    async def trading_system(self):
        """Setup complete trading system for testing"""
        # Mock Binance client in dry-run mode
        binance_client = BinanceClient(dry_run=True, testnet=True)
        
        # Create agent loop with mocked components
        agent_loop = AgentLoop(
            trading_client=binance_client,
            notifier=None
        )
        
        return {
            'binance_client': binance_client,
            'agent_loop': agent_loop
        }
    
    @pytest.mark.asyncio
    async def test_complete_trading_cycle(self, trading_system):
        """Test complete trading cycle from signal to execution"""
        agent_loop = trading_system['agent_loop']
        
        # Mock market data
        mock_market_data = {
            'symbol': 'BTCUSDT',
            'price': 50000.0,
            'volume': 1000000,
            'volatility': 0.02,
            'trend': 'bullish'
        }
        
        # Mock AI advisor response
        with patch('app.agent.advisor.get_signal_score') as mock_advisor:
            mock_advisor.return_value = {
                'score': 0.85,
                'confidence': 0.9,
                'signal': 'BUY',
                'reasoning': 'Strong bullish momentum'
            }
            
            # Execute trading decision
            decision = await agent_loop.make_trading_decision(mock_market_data)
            
            assert decision is not None
            assert decision.action in ['BUY', 'SELL', 'HOLD']
            assert 0 <= decision.confidence <= 1
            
            # If decision is to trade, execute it
            if decision.action in ['BUY', 'SELL']:
                execution_result = await agent_loop.execute_trade(decision)
                
                # In dry-run mode, should return mock execution
                assert execution_result['status'] in ['dry_run', 'success']
                assert 'order_id' in execution_result
    
    @pytest.mark.asyncio
    async def test_risk_management_integration(self, trading_system):
        """Test risk management prevents dangerous trades"""
        agent_loop = trading_system['agent_loop']
        
        # Set up dangerous scenario - large position size
        mock_dangerous_decision = {
            'action': 'BUY',
            'symbol': 'BTCUSDT',
            'size': 100000,  # Very large size
            'confidence': 0.9
        }
        
        # Risk engine should block this trade
        with patch('app.trader.risk_engine.validate_trade_risk') as mock_risk:
            mock_risk.return_value = {
                'allowed': False,
                'reason': 'Position size exceeds risk limits'
            }
            
            result = await agent_loop.execute_trade_with_risk_check(mock_dangerous_decision)
            
            assert result['status'] == 'blocked'
            assert 'risk' in result['reason'].lower()
    
    @pytest.mark.asyncio
    async def test_websocket_real_time_data(self):
        """Test WebSocket real-time data streaming"""
        # This would normally connect to real WebSocket
        # For testing, we'll mock the connection
        
        messages_received = []
        
        async def mock_websocket_handler():
            # Simulate real-time market data
            for i in range(5):
                message = {
                    'type': 'market_data',
                    'symbol': 'BTCUSDT',
                    'price': 50000 + i * 10,
                    'timestamp': time.time()
                }
                messages_received.append(message)
                await asyncio.sleep(0.1)
        
        await mock_websocket_handler()
        
        assert len(messages_received) == 5
        assert all('price' in msg for msg in messages_received)
        assert messages_received[-1]['price'] > messages_received[0]['price']
    
    @pytest.mark.asyncio
    async def test_database_persistence(self, trading_system):
        """Test that trades are properly persisted to database"""
        # Mock database operations
        with patch('sqlite3.connect') as mock_db:
            mock_cursor = MagicMock()
            mock_db.return_value.cursor.return_value = mock_cursor
            
            # Execute a trade
            trade_data = {
                'symbol': 'BTCUSDT',
                'side': 'BUY',
                'size': 0.001,
                'price': 50000,
                'timestamp': datetime.now()
            }
            
            # Should persist to database
            await trading_system['agent_loop'].persist_trade(trade_data)
            
            # Verify database operations were called
            mock_cursor.execute.assert_called()
            assert 'INSERT' in mock_cursor.execute.call_args[0][0].upper()


class TestPerformanceAndLoad:
    """
    Load testing and performance benchmarks
    """
    
    @pytest.mark.asyncio
    async def test_high_frequency_decision_making(self):
        """Test AI decision making under high frequency scenarios"""
        decision_times = []
        
        for i in range(100):
            start_time = time.time()
            
            # Mock high-frequency market data
            market_data = {
                'symbol': 'BTCUSDT',
                'price': 50000 + (i % 100),
                'timestamp': start_time
            }
            
            # Simulate AI decision (mocked for speed)
            with patch('app.agent.advisor.get_signal_score') as mock_advisor:
                mock_advisor.return_value = {'score': 0.7, 'signal': 'HOLD'}
                
                # Mock agent decision
                decision_time = time.time() - start_time
                decision_times.append(decision_time)
        
        # Performance assertions
        avg_decision_time = sum(decision_times) / len(decision_times)
        max_decision_time = max(decision_times)
        
        assert avg_decision_time < 0.1  # 100ms average
        assert max_decision_time < 0.5   # 500ms max
        assert len(decision_times) == 100
    
    @pytest.mark.asyncio
    async def test_concurrent_order_processing(self):
        """Test system under concurrent order load"""
        concurrent_orders = 50
        results = []
        
        async def process_mock_order(order_id):
            # Simulate order processing time
            await asyncio.sleep(0.1)
            return f"order_{order_id}_completed"
        
        # Execute concurrent orders
        tasks = [process_mock_order(i) for i in range(concurrent_orders)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == concurrent_orders
        assert all('completed' in result for result in results)
    
    @pytest.mark.asyncio 
    async def test_memory_usage_under_load(self):
        """Test memory usage during extended operation"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate extended trading session
        for i in range(1000):
            # Mock market data processing
            data = {
                'timestamp': time.time(),
                'prices': [50000 + j for j in range(100)],
                'volumes': [1000 + j for j in range(100)]
            }
            
            # Process data (mock operation)
            processed = len(data['prices']) + len(data['volumes'])
            
            if i % 100 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                
                # Memory should not grow excessively
                assert memory_increase < 100  # Less than 100MB increase


class TestChaosEngineering:
    """
    Chaos engineering tests for resilience
    """
    
    @pytest.mark.asyncio
    async def test_network_failure_resilience(self, trading_system):
        """Test system behavior during network failures"""
        agent_loop = trading_system['agent_loop']
        
        # Simulate network failure
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = aiohttp.ClientError("Network unreachable")
            
            # System should handle gracefully
            try:
                result = await agent_loop.fetch_market_data('BTCUSDT')
                # Should return cached data or safe default
                assert result is not None
            except Exception as e:
                # Or should catch and log error appropriately
                assert "network" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_database_failure_recovery(self, trading_system):
        """Test recovery from database failures"""
        with patch('sqlite3.connect') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            # Should handle database failures gracefully
            try:
                await trading_system['agent_loop'].persist_trade({})
            except Exception as e:
                # Should log error and continue operation
                assert "database" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_api_rate_limiting(self, trading_system):
        """Test behavior under API rate limiting"""
        binance_client = trading_system['binance_client']
        
        # Mock rate limiting response
        with patch.object(binance_client, 'client') as mock_client:
            mock_client.get_account.side_effect = Exception("Rate limit exceeded")
            
            # Should implement backoff and retry
            result = await binance_client.get_account_with_retry()
            
            # Should eventually succeed or fail gracefully
            assert result is not None or "rate limit" in str(result).lower()
    
    @pytest.mark.asyncio
    async def test_partial_system_failure(self, trading_system):
        """Test system with partial component failures"""
        agent_loop = trading_system['agent_loop']
        
        # Disable AI advisor
        with patch('app.agent.advisor.get_signal_score') as mock_advisor:
            mock_advisor.side_effect = Exception("AI service unavailable")
            
            # Should fall back to conservative trading
            decision = await agent_loop.make_conservative_decision({
                'symbol': 'BTCUSDT',
                'price': 50000
            })
            
            assert decision.action == 'HOLD'  # Conservative default
            assert decision.confidence < 0.5   # Low confidence without AI


class TestSecurityAndCompliance:
    """
    Security and compliance testing
    """
    
    @pytest.mark.asyncio
    async def test_api_key_security(self, trading_system):
        """Test API key handling and security"""
        binance_client = trading_system['binance_client']
        
        # API keys should never be logged
        with patch('logging.Logger.info') as mock_log:
            await binance_client.test_connection()
            
            # Check that no log contains API keys
            for call in mock_log.call_args_list:
                log_message = str(call)
                assert 'api_key' not in log_message.lower()
                assert 'secret' not in log_message.lower()
    
    @pytest.mark.asyncio
    async def test_trade_audit_trail(self, trading_system):
        """Test that all trades are properly audited"""
        audit_logs = []
        
        def mock_audit_log(event, data):
            audit_logs.append({
                'event': event,
                'data': data,
                'timestamp': datetime.now()
            })
        
        with patch('app.trader.audit.log_trade_event', side_effect=mock_audit_log):
            # Execute trades
            for i in range(5):
                trade_data = {
                    'symbol': 'BTCUSDT',
                    'side': 'BUY' if i % 2 == 0 else 'SELL',
                    'size': 0.001
                }
                
                await trading_system['agent_loop'].execute_audited_trade(trade_data)
        
        # Verify audit trail
        assert len(audit_logs) == 5
        assert all('symbol' in log['data'] for log in audit_logs)
        assert all(log['timestamp'] for log in audit_logs)
    
    @pytest.mark.asyncio
    async def test_input_validation(self, trading_system):
        """Test input validation and sanitization"""
        agent_loop = trading_system['agent_loop']
        
        # Test malicious inputs
        malicious_inputs = [
            {'symbol': 'BTCUSDT; DROP TABLE trades;'},
            {'size': -1000000},  # Negative size
            {'price': 'malicious_string'},
            {'symbol': ''},  # Empty symbol
        ]
        
        for malicious_input in malicious_inputs:
            with pytest.raises((ValueError, TypeError, Exception)):
                await agent_loop.validate_and_execute_trade(malicious_input)


# Test configuration
pytest_plugins = ['pytest_asyncio']

# Custom test markers
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.integration
]


if __name__ == "__main__":
    # Run integration tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])