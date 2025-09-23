"""
Unit Tests for Performance Optimization Framework
Tests for connection pooling, caching, async optimization, and performance profiling
"""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import datetime, timedelta

# Import modules to test
try:
    from app.performance.optimization import (
        ConnectionPoolManager, AdvancedCache, AsyncTaskManager,
        PerformanceProfiler, PerformanceMetrics, cached, performance_optimized
    )
    from app.trader.optimized_client import OptimizedTradingClient, TradingOrder
    from app.trader.async_loop import AsyncTradingLoop, TradingSignal, TradingState
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False


@pytest.mark.skipif(not MODULES_AVAILABLE, reason="Performance modules not available")
class TestConnectionPoolManager:
    """Test connection pool management"""
    
    @pytest.fixture
    async def pool_manager(self):
        manager = ConnectionPoolManager(max_connections=10)
        yield manager
        await manager.close_all_pools()
    
    @pytest.mark.asyncio
    async def test_http_session_creation(self, pool_manager):
        """Test HTTP session creation and reuse"""
        session1 = await pool_manager.get_http_session("test_pool")
        session2 = await pool_manager.get_http_session("test_pool")
        
        # Should reuse the same session
        assert session1 is session2
        
        # Different pool should create different session
        session3 = await pool_manager.get_http_session("another_pool")
        assert session1 is not session3
    
    @pytest.mark.asyncio
    async def test_pool_statistics(self, pool_manager):
        """Test pool statistics tracking"""
        # Create a session to initialize stats
        await pool_manager.get_http_session("test_pool")
        
        stats = pool_manager.get_pool_stats()
        assert 'http_pools' in stats
        assert 'test_pool' in stats['http_pools']
        assert 'total_requests' in stats['http_pools']['test_pool']
    
    @pytest.mark.asyncio
    async def test_db_connection_pool(self, pool_manager):
        """Test database connection pooling"""
        async with pool_manager.get_db_connection("test_db") as conn:
            assert conn is not None
            assert 'id' in conn  # Mock connection has ID
        
        # Test pool reuse
        async with pool_manager.get_db_connection("test_db") as conn2:
            assert conn2 is not None


@pytest.mark.skipif(not MODULES_AVAILABLE, reason="Performance modules not available")
class TestAdvancedCache:
    """Test advanced caching system"""
    
    @pytest.fixture
    async def cache(self):
        # Use in-memory cache for testing
        cache = AdvancedCache(redis_url="redis://fake")
        cache.redis = None  # Disable Redis for testing
        yield cache
        if cache.redis:
            await cache.redis.close()
    
    @pytest.mark.asyncio
    async def test_memory_cache_operations(self, cache):
        """Test L1 memory cache operations"""
        # Test set and get
        await cache.set("test_key", {"data": "value"}, ttl=60)
        result = await cache.get("test_key")
        
        assert result is not None
        assert result["data"] == "value"
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache):
        """Test cache TTL expiration"""
        # Set with very short TTL
        await cache.set("expire_key", "value", ttl=1)
        
        # Should be available immediately
        result = await cache.get("expire_key")
        assert result == "value"
        
        # Wait for expiration and check
        await asyncio.sleep(1.1)
        result = await cache.get("expire_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache):
        """Test cache invalidation patterns"""
        # Set up test data
        await cache.set("user:123:profile", {"name": "test"})
        await cache.set("user:456:profile", {"name": "test2"})
        await cache.set("other:data", {"value": "keep"})
        
        # Invalidate pattern
        await cache.invalidate("user:")
        
        # Check invalidation worked
        result1 = await cache.get("user:123:profile")
        result2 = await cache.get("user:456:profile")
        result3 = await cache.get("other:data")
        
        assert result1 is None
        assert result2 is None
        assert result3 is not None  # Should remain
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache):
        """Test cache statistics tracking"""
        # Generate some cache activity
        await cache.set("key1", "value1")
        await cache.get("key1")  # Hit
        await cache.get("key2")  # Miss
        
        stats = cache.get_cache_stats()
        
        assert 'hit_rate' in stats
        assert 'total_requests' in stats
        assert stats['total_requests'] >= 2
    
    @pytest.mark.asyncio
    async def test_cached_decorator(self, cache):
        """Test cached decorator functionality"""
        call_count = 0
        
        @cached(ttl=60, cache_key_prefix="test_func")
        async def test_function(param1, param2):
            nonlocal call_count
            call_count += 1
            return f"{param1}_{param2}_{call_count}"
        
        # First call should execute function
        result1 = await test_function("a", "b")
        assert call_count == 1
        
        # Second call should use cache
        result2 = await test_function("a", "b")
        assert call_count == 1  # Function not called again
        assert result1 == result2
        
        # Different parameters should execute function
        result3 = await test_function("c", "d")
        assert call_count == 2


@pytest.mark.skipif(not MODULES_AVAILABLE, reason="Performance modules not available")
class TestAsyncTaskManager:
    """Test async task management"""
    
    @pytest.fixture
    async def task_manager(self):
        manager = AsyncTaskManager(max_concurrent_tasks=5)
        yield manager
        # Cleanup
        if manager._processor_task:
            manager._processor_task.cancel()
            try:
                await manager._processor_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_task_submission(self, task_manager):
        """Test task submission with priorities"""
        async def test_task():
            await asyncio.sleep(0.1)
            return "completed"
        
        # Submit tasks with different priorities
        task_id1 = await task_manager.submit_task(test_task(), priority="high")
        task_id2 = await task_manager.submit_task(test_task(), priority="normal")
        task_id3 = await task_manager.submit_task(test_task(), priority="low")
        
        assert task_id1 is not None
        assert task_id2 is not None
        assert task_id3 is not None
        assert task_id1 != task_id2 != task_id3
        
        # Wait a bit for processing
        await asyncio.sleep(0.5)
    
    @pytest.mark.asyncio
    async def test_task_statistics(self, task_manager):
        """Test task statistics tracking"""
        async def quick_task():
            return "done"
        
        # Submit and wait for some tasks
        for _ in range(3):
            await task_manager.submit_task(quick_task())
        
        await asyncio.sleep(0.5)  # Allow processing
        
        stats = task_manager.get_task_stats()
        
        assert 'completed_tasks' in stats
        assert 'failed_tasks' in stats
        assert 'success_rate' in stats
        assert 'queue_sizes' in stats


@pytest.mark.skipif(not MODULES_AVAILABLE, reason="Performance modules not available")
class TestPerformanceProfiler:
    """Test performance profiling"""
    
    @pytest.fixture
    def profiler(self):
        profiler = PerformanceProfiler()
        yield profiler
        # Cleanup
        if profiler._monitor_task:
            profiler._monitor_task.cancel()
    
    @pytest.mark.asyncio
    async def test_function_profiling(self, profiler):
        """Test function performance profiling"""
        @profiler.profile_function("test_operation")
        async def slow_function():
            await asyncio.sleep(0.1)
            return "result"
        
        result = await slow_function()
        assert result == "result"
        
        # Check if metrics were recorded
        assert len(profiler.metrics_history) > 0
        
        metric = profiler.metrics_history[-1]
        assert metric.operation == "test_operation"
        assert metric.duration >= 0.1
    
    def test_performance_report(self, profiler):
        """Test performance report generation"""
        # Add some mock metrics
        for i in range(5):
            metric = PerformanceMetrics(
                timestamp=datetime.now(),
                operation=f"test_op_{i % 2}",
                duration=0.1 + i * 0.05,
                memory_usage=10.0,
                cpu_usage=20.0
            )
            profiler.metrics_history.append(metric)
        
        report = profiler.get_performance_report()
        
        assert 'overall_stats' in report
        assert 'operation_breakdown' in report
        assert 'recommendations' in report
        
        # Check operation breakdown
        assert len(report['operation_breakdown']) > 0


@pytest.mark.skipif(not MODULES_AVAILABLE, reason="Performance modules not available")
class TestOptimizedTradingClient:
    """Test optimized trading client"""
    
    @pytest.fixture
    def trading_client(self):
        client = OptimizedTradingClient(
            api_key="test_key",
            api_secret="test_secret",
            testnet=True
        )
        return client
    
    def test_client_initialization(self, trading_client):
        """Test client initialization"""
        assert trading_client.api_key == "test_key"
        assert trading_client.testnet is True
        assert trading_client.base_url == "https://testnet.binancefuture.com"
    
    def test_trading_order_creation(self):
        """Test trading order structure"""
        order = TradingOrder(
            symbol="BTCUSDT",
            side="buy",
            quantity=Decimal("0.001"),
            price=Decimal("50000.00"),
            order_type="limit"
        )
        
        assert order.symbol == "BTCUSDT"
        assert order.side == "buy"
        assert order.quantity == Decimal("0.001")
        assert order.client_order_id is not None
        
        order_dict = order.to_dict()
        assert order_dict['symbol'] == "BTCUSDT"
        assert order_dict['side'] == "BUY"
        assert order_dict['type'] == "LIMIT"
    
    @pytest.mark.asyncio
    async def test_dry_run_order_placement(self, trading_client):
        """Test dry run order placement"""
        order = TradingOrder(
            symbol="BTCUSDT",
            side="buy",
            quantity=Decimal("0.001")
        )
        
        result = await trading_client.place_order(order, dry_run=True)
        
        assert result is not None
        assert result.get('dry_run') is True
        assert 'orderId' in result
        assert result['symbol'] == "BTCUSDT"
    
    def test_performance_metrics(self, trading_client):
        """Test client performance metrics"""
        metrics = trading_client.get_performance_metrics()
        
        assert 'total_requests' in metrics
        assert 'success_rate' in metrics
        assert 'avg_latency_ms' in metrics
        assert 'pending_orders' in metrics


@pytest.mark.skipif(not MODULES_AVAILABLE, reason="Performance modules not available")
class TestAsyncTradingLoop:
    """Test async trading loop"""
    
    @pytest.fixture
    def trading_config(self):
        return {
            'symbols': ['BTCUSDT'],
            'loop_interval': 0.1,  # Fast for testing
            'dry_run': True,
            'max_concurrent_operations': 5,
            'testnet': True,
            'api_key': 'test_key',
            'api_secret': 'test_secret'
        }
    
    @pytest.fixture
    async def trading_loop(self, trading_config):
        loop = AsyncTradingLoop(trading_config)
        yield loop
        if loop.state != TradingState.STOPPED:
            await loop.stop()
    
    def test_loop_initialization(self, trading_loop):
        """Test trading loop initialization"""
        assert trading_loop.state == TradingState.STOPPED
        assert trading_loop.dry_run is True
        assert trading_loop.loop_interval == 0.1
    
    def test_trading_signal_creation(self):
        """Test trading signal structure"""
        signal = TradingSignal(
            symbol="BTCUSDT",
            action="buy",
            strength=0.8,
            strategy="test_strategy",
            confidence=0.7
        )
        
        assert signal.symbol == "BTCUSDT"
        assert signal.action == "buy"
        assert signal.strength == 0.8
        assert signal.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_loop_start_stop(self, trading_loop):
        """Test loop start and stop operations"""
        # Test starting
        await trading_loop.start()
        assert trading_loop.state == TradingState.RUNNING
        
        # Let it run briefly
        await asyncio.sleep(0.3)
        
        # Test stopping
        await trading_loop.stop()
        assert trading_loop.state == TradingState.STOPPED
    
    @pytest.mark.asyncio
    async def test_loop_pause_resume(self, trading_loop):
        """Test loop pause and resume operations"""
        await trading_loop.start()
        
        # Test pausing
        await trading_loop.pause()
        await asyncio.sleep(0.2)  # Allow state to update
        assert trading_loop.state in [TradingState.PAUSING, TradingState.PAUSED]
        
        # Test resuming
        await trading_loop.resume()
        await asyncio.sleep(0.2)
        
        await trading_loop.stop()
    
    @pytest.mark.asyncio
    async def test_loop_status_reporting(self, trading_loop):
        """Test loop status and metrics reporting"""
        status = trading_loop.get_status()
        
        assert 'state' in status
        assert 'dry_run' in status
        assert 'loop_metrics' in status
        assert 'queue_status' in status
        
        # Start loop and get updated status
        await trading_loop.start()
        await asyncio.sleep(0.3)
        
        running_status = trading_loop.get_status()
        assert running_status['state'] == 'running'
        assert running_status['loop_metrics']['iterations'] > 0
        
        await trading_loop.stop()


@pytest.mark.skipif(not MODULES_AVAILABLE, reason="Performance modules not available")
class TestPerformanceIntegration:
    """Integration tests for performance optimization"""
    
    @pytest.mark.asyncio
    async def test_full_performance_pipeline(self):
        """Test complete performance optimization pipeline"""
        # Initialize components
        pool_manager = ConnectionPoolManager(max_connections=5)
        cache = AdvancedCache(redis_url="redis://fake")
        cache.redis = None  # Disable Redis for testing
        
        try:
            # Test cached function with connection pooling
            @cached(ttl=30, cache_key_prefix="integration_test")
            async def cached_api_call(symbol: str):
                # Simulate API call
                await asyncio.sleep(0.05)
                return {"symbol": symbol, "price": 50000}
            
            # First call - should execute function
            start_time = time.time()
            result1 = await cached_api_call("BTCUSDT")
            first_duration = time.time() - start_time
            
            # Second call - should use cache (faster)
            start_time = time.time()
            result2 = await cached_api_call("BTCUSDT")
            second_duration = time.time() - start_time
            
            assert result1 == result2
            assert second_duration < first_duration  # Cache should be faster
            
            # Check cache stats
            stats = cache.get_cache_stats()
            assert stats['hit_rate'] > 0
        
        finally:
            await pool_manager.close_all_pools()
            if cache.redis:
                await cache.redis.close()
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test performance optimization under load"""
        task_manager = AsyncTaskManager(max_concurrent_tasks=10)
        
        try:
            async def work_task(task_id: int):
                await asyncio.sleep(0.01)  # Simulate work
                return f"task_{task_id}_completed"
            
            # Submit multiple tasks
            task_ids = []
            for i in range(20):
                task_id = await task_manager.submit_task(
                    work_task(i),
                    priority="normal"
                )
                task_ids.append(task_id)
            
            # Wait for processing
            await asyncio.sleep(1.0)
            
            # Check statistics
            stats = task_manager.get_task_stats()
            assert stats['completed_tasks'] > 0
            assert stats['success_rate'] > 0.8  # Should have high success rate
        
        finally:
            if task_manager._processor_task:
                task_manager._processor_task.cancel()
                try:
                    await task_manager._processor_task
                except asyncio.CancelledError:
                    pass


# Utility functions for testing
def generate_test_data(count: int = 100):
    """Generate test data for performance testing"""
    return [
        {
            'timestamp': datetime.now() - timedelta(seconds=i),
            'symbol': f'TEST{i % 10}USDT',
            'price': 1000 + i,
            'volume': 100 + i * 10
        }
        for i in range(count)
    ]


@pytest.mark.asyncio
async def test_performance_optimized_decorator():
    """Test the performance_optimized decorator"""
    if not MODULES_AVAILABLE:
        pytest.skip("Performance modules not available")
    
    call_count = 0
    
    @performance_optimized("test_decorated_function", cache_ttl=60)
    async def decorated_function(param: str):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.01)
        return f"result_{param}_{call_count}"
    
    # Test function execution
    result = await decorated_function("test")
    assert "result_test" in result
    assert call_count >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])