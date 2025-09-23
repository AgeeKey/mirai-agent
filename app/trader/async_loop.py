"""
Async-Optimized Trading Loop with Performance Enhancements
High-performance autonomous trading with concurrent operations and latency optimization
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from decimal import Decimal

# Import performance framework
try:
    from ..performance.optimization import (
        performance_optimized, task_manager, 
        advanced_cache, PerformanceProfiler
    )
    PERFORMANCE_AVAILABLE = True
except ImportError:
    PERFORMANCE_AVAILABLE = False
    def performance_optimized(name, cache_ttl=300):
        def decorator(func):
            return func
        return decorator

# Import optimized client
try:
    from .optimized_client import OptimizedTradingClient, TradingOrder
except ImportError:
    # Fallback for development
    class OptimizedTradingClient:
        pass
    class TradingOrder:
        pass


class TradingState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class TradingSignal:
    """Optimized trading signal structure"""
    symbol: str
    action: str  # 'buy', 'sell', 'hold'
    strength: float  # 0.0 to 1.0
    price: Optional[Decimal] = None
    quantity: Optional[Decimal] = None
    strategy: str = "unknown"
    timestamp: datetime = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class LoopMetrics:
    """Performance metrics for trading loop"""
    loop_count: int = 0
    avg_loop_time: float = 0.0
    last_loop_time: float = 0.0
    signals_processed: int = 0
    orders_placed: int = 0
    errors_count: int = 0
    cache_hit_rate: float = 0.0
    concurrent_tasks: int = 0


class AsyncTradingLoop:
    """
    High-performance async trading loop with concurrent operations
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Trading state
        self.state = TradingState.STOPPED
        self.dry_run = config.get('dry_run', True)
        
        # Performance configuration
        self.loop_interval = config.get('loop_interval', 1.0)  # seconds
        self.max_concurrent_operations = config.get('max_concurrent_operations', 10)
        self.signal_processing_timeout = config.get('signal_processing_timeout', 5.0)
        
        # Components (will be initialized)
        self.trading_client: Optional[OptimizedTradingClient] = None
        self.signal_generators: List[Any] = []
        self.risk_manager: Optional[Any] = None
        
        # Performance tracking
        self.metrics = LoopMetrics()
        self.loop_times: List[float] = []
        
        # Async coordination
        self.main_task: Optional[asyncio.Task] = None
        self.stop_event = asyncio.Event()
        self.pause_event = asyncio.Event()
        
        # Signal processing
        self.signal_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.order_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        
        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
        
        self.logger.info("AsyncTradingLoop initialized")
    
    async def initialize(self):
        """Initialize trading components"""
        try:
            # Initialize trading client
            self.trading_client = OptimizedTradingClient(
                api_key=self.config.get('api_key', ''),
                api_secret=self.config.get('api_secret', ''),
                testnet=self.config.get('testnet', True)
            )
            
            if self.trading_client:
                await self.trading_client.optimize_for_trading_session()
            
            # Initialize signal processors
            await self._initialize_signal_processors()
            
            # Initialize background tasks
            await self._start_background_tasks()
            
            self.logger.info("Trading loop components initialized")
        
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            self.state = TradingState.ERROR
            raise
    
    async def _initialize_signal_processors(self):
        """Initialize signal generation and processing"""
        # Mock signal generators for now
        self.signal_generators = [
            {"name": "momentum", "enabled": True},
            {"name": "mean_reversion", "enabled": True},
            {"name": "breakout", "enabled": False}
        ]
    
    async def _start_background_tasks(self):
        """Start background processing tasks"""
        if PERFORMANCE_AVAILABLE:
            # Signal processing task
            signal_task = asyncio.create_task(self._process_signals_continuously())
            self.background_tasks.append(signal_task)
            
            # Order execution task
            order_task = asyncio.create_task(self._execute_orders_continuously())
            self.background_tasks.append(order_task)
            
            # Metrics collection task
            metrics_task = asyncio.create_task(self._collect_metrics_continuously())
            self.background_tasks.append(metrics_task)
            
            self.logger.info(f"Started {len(self.background_tasks)} background tasks")
    
    @performance_optimized("trading_loop_iteration", cache_ttl=0)
    async def _main_loop_iteration(self) -> Dict[str, Any]:
        """Single iteration of the main trading loop"""
        iteration_start = time.time()
        
        try:
            # Concurrent market data collection
            market_data_tasks = []
            symbols = self.config.get('symbols', ['BTCUSDT', 'ETHUSDT'])
            
            for symbol in symbols:
                if PERFORMANCE_AVAILABLE:
                    task_id = await task_manager.submit_task(
                        self._collect_market_data(symbol),
                        priority="high"
                    )
                    market_data_tasks.append(task_id)
                else:
                    # Fallback: collect sequentially
                    await self._collect_market_data(symbol)
            
            # Generate trading signals concurrently
            signal_tasks = []
            for generator in self.signal_generators:
                if generator['enabled']:
                    if PERFORMANCE_AVAILABLE:
                        task_id = await task_manager.submit_task(
                            self._generate_signals(generator['name']),
                            priority="normal"
                        )
                        signal_tasks.append(task_id)
                    else:
                        signals = await self._generate_signals(generator['name'])
                        for signal in signals:
                            await self.signal_queue.put(signal)
            
            # Update performance metrics
            iteration_time = time.time() - iteration_start
            self.loop_times.append(iteration_time)
            
            # Keep only last 100 loop times
            if len(self.loop_times) > 100:
                self.loop_times = self.loop_times[-100:]
            
            self.metrics.loop_count += 1
            self.metrics.last_loop_time = iteration_time
            self.metrics.avg_loop_time = sum(self.loop_times) / len(self.loop_times)
            
            return {
                'iteration': self.metrics.loop_count,
                'duration': iteration_time,
                'market_data_tasks': len(market_data_tasks),
                'signal_tasks': len(signal_tasks),
                'queue_sizes': {
                    'signals': self.signal_queue.qsize(),
                    'orders': self.order_queue.qsize()
                }
            }
        
        except Exception as e:
            self.metrics.errors_count += 1
            self.logger.error(f"Loop iteration failed: {e}")
            return {'error': str(e)}
    
    @performance_optimized("collect_market_data", cache_ttl=5)
    async def _collect_market_data(self, symbol: str) -> Dict[str, Any]:
        """Collect market data for symbol with caching"""
        if not self.trading_client:
            return {'error': 'Trading client not initialized'}
        
        try:
            # Collect multiple data points concurrently
            tasks = []
            
            if PERFORMANCE_AVAILABLE:
                # Submit tasks to task manager
                ticker_task = await task_manager.submit_task(
                    self.trading_client.get_ticker_price(symbol),
                    priority="high"
                )
                
                orderbook_task = await task_manager.submit_task(
                    self.trading_client.get_order_book(symbol, limit=20),
                    priority="high"
                )
                
                return {
                    'symbol': symbol,
                    'ticker_task': ticker_task,
                    'orderbook_task': orderbook_task,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Fallback: direct calls
                ticker = await self.trading_client.get_ticker_price(symbol)
                orderbook = await self.trading_client.get_order_book(symbol, limit=20)
                
                return {
                    'symbol': symbol,
                    'ticker': ticker,
                    'orderbook': orderbook,
                    'timestamp': datetime.now().isoformat()
                }
        
        except Exception as e:
            self.logger.error(f"Failed to collect market data for {symbol}: {e}")
            return {'error': str(e), 'symbol': symbol}
    
    @performance_optimized("generate_signals", cache_ttl=10)
    async def _generate_signals(self, strategy_name: str) -> List[TradingSignal]:
        """Generate trading signals from strategy"""
        # Mock signal generation for now
        symbols = self.config.get('symbols', ['BTCUSDT'])
        signals = []
        
        for symbol in symbols:
            # Simulate signal generation logic
            import random
            if random.random() > 0.7:  # 30% chance of signal
                action = random.choice(['buy', 'sell', 'hold'])
                strength = random.uniform(0.3, 1.0)
                
                signal = TradingSignal(
                    symbol=symbol,
                    action=action,
                    strength=strength,
                    strategy=strategy_name,
                    confidence=strength * 0.8,
                    metadata={'source': 'mock_generator'}
                )
                signals.append(signal)
        
        return signals
    
    async def _process_signals_continuously(self):
        """Continuously process signals from queue"""
        while not self.stop_event.is_set():
            try:
                # Wait for signal with timeout
                signal = await asyncio.wait_for(
                    self.signal_queue.get(),
                    timeout=self.signal_processing_timeout
                )
                
                # Process signal
                await self._process_signal(signal)
                self.metrics.signals_processed += 1
                
            except asyncio.TimeoutError:
                # No signals to process, continue
                continue
            except Exception as e:
                self.logger.error(f"Signal processing failed: {e}")
                self.metrics.errors_count += 1
    
    @performance_optimized("process_signal", cache_ttl=0)
    async def _process_signal(self, signal: TradingSignal):
        """Process individual trading signal"""
        try:
            # Apply risk management
            if not await self._validate_signal_risk(signal):
                self.logger.debug(f"Signal rejected by risk management: {signal.symbol}")
                return
            
            # Convert signal to order
            if signal.action in ['buy', 'sell']:
                order = await self._signal_to_order(signal)
                if order:
                    await self.order_queue.put(order)
                    self.logger.debug(f"Order queued: {signal.symbol} {signal.action}")
        
        except Exception as e:
            self.logger.error(f"Failed to process signal {signal.symbol}: {e}")
    
    async def _validate_signal_risk(self, signal: TradingSignal) -> bool:
        """Validate signal against risk management rules"""
        # Mock risk validation
        if signal.strength < 0.5:
            return False
        if signal.confidence < 0.6:
            return False
        return True
    
    async def _signal_to_order(self, signal: TradingSignal) -> Optional[TradingOrder]:
        """Convert trading signal to order"""
        try:
            # Mock order creation
            if signal.action == 'hold':
                return None
            
            # Calculate position size (mock)
            quantity = Decimal('0.001')  # Small test size
            
            order = TradingOrder(
                symbol=signal.symbol,
                side=signal.action,
                quantity=quantity,
                order_type='market'
            )
            
            return order
        
        except Exception as e:
            self.logger.error(f"Failed to create order from signal: {e}")
            return None
    
    async def _execute_orders_continuously(self):
        """Continuously execute orders from queue"""
        while not self.stop_event.is_set():
            try:
                # Wait for order with timeout
                order = await asyncio.wait_for(
                    self.order_queue.get(),
                    timeout=5.0
                )
                
                # Execute order
                await self._execute_order(order)
                self.metrics.orders_placed += 1
                
            except asyncio.TimeoutError:
                # No orders to execute, continue
                continue
            except Exception as e:
                self.logger.error(f"Order execution failed: {e}")
                self.metrics.errors_count += 1
    
    @performance_optimized("execute_order", cache_ttl=0)
    async def _execute_order(self, order: TradingOrder):
        """Execute trading order"""
        if not self.trading_client:
            self.logger.error("Cannot execute order: trading client not initialized")
            return
        
        try:
            result = await self.trading_client.place_order(order, dry_run=self.dry_run)
            self.logger.info(f"Order executed: {order.symbol} {order.side} {order.quantity}")
            
            # Invalidate relevant caches
            if PERFORMANCE_AVAILABLE:
                await advanced_cache.trigger_invalidation('order_executed')
            
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to execute order {order.symbol}: {e}")
            raise
    
    async def _collect_metrics_continuously(self):
        """Continuously collect performance metrics"""
        while not self.stop_event.is_set():
            try:
                if PERFORMANCE_AVAILABLE:
                    # Update cache hit rate
                    cache_stats = advanced_cache.get_cache_stats()
                    self.metrics.cache_hit_rate = cache_stats.get('hit_rate', 0.0)
                    
                    # Update concurrent tasks
                    task_stats = task_manager.get_task_stats()
                    self.metrics.concurrent_tasks = task_stats.get('active_tasks', 0)
                
                await asyncio.sleep(10)  # Collect metrics every 10 seconds
            
            except Exception as e:
                self.logger.error(f"Metrics collection failed: {e}")
                await asyncio.sleep(30)
    
    async def start(self):
        """Start the trading loop"""
        if self.state != TradingState.STOPPED:
            raise RuntimeError(f"Cannot start loop in state: {self.state}")
        
        self.state = TradingState.STARTING
        self.logger.info("Starting trading loop...")
        
        try:
            await self.initialize()
            
            self.state = TradingState.RUNNING
            self.stop_event.clear()
            self.pause_event.clear()
            
            # Start main loop
            self.main_task = asyncio.create_task(self._run_main_loop())
            
            self.logger.info("Trading loop started successfully")
        
        except Exception as e:
            self.state = TradingState.ERROR
            self.logger.error(f"Failed to start trading loop: {e}")
            raise
    
    async def _run_main_loop(self):
        """Run the main trading loop"""
        while not self.stop_event.is_set():
            try:
                # Check if paused
                if self.pause_event.is_set():
                    self.state = TradingState.PAUSED
                    await asyncio.sleep(1)
                    continue
                
                if self.state == TradingState.PAUSED:
                    self.state = TradingState.RUNNING
                
                # Execute main loop iteration
                result = await self._main_loop_iteration()
                
                if 'error' in result:
                    self.logger.warning(f"Loop iteration had error: {result['error']}")
                
                # Wait for next iteration
                await asyncio.sleep(self.loop_interval)
            
            except asyncio.CancelledError:
                self.logger.info("Main loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Main loop error: {e}")
                self.metrics.errors_count += 1
                await asyncio.sleep(5)  # Wait before retrying
        
        self.state = TradingState.STOPPED
    
    async def pause(self):
        """Pause the trading loop"""
        if self.state == TradingState.RUNNING:
            self.state = TradingState.PAUSING
            self.pause_event.set()
            self.logger.info("Trading loop paused")
    
    async def resume(self):
        """Resume the trading loop"""
        if self.state == TradingState.PAUSED:
            self.pause_event.clear()
            self.logger.info("Trading loop resumed")
    
    async def stop(self):
        """Stop the trading loop"""
        if self.state in [TradingState.STOPPED, TradingState.STOPPING]:
            return
        
        self.state = TradingState.STOPPING
        self.logger.info("Stopping trading loop...")
        
        # Signal stop
        self.stop_event.set()
        
        # Cancel main task
        if self.main_task:
            self.main_task.cancel()
            try:
                await self.main_task
            except asyncio.CancelledError:
                pass
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.state = TradingState.STOPPED
        self.logger.info("Trading loop stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current loop status and metrics"""
        client_metrics = {}
        if self.trading_client:
            try:
                client_metrics = self.trading_client.get_performance_metrics()
            except Exception as e:
                client_metrics = {'error': str(e)}
        
        return {
            'state': self.state.value,
            'dry_run': self.dry_run,
            'uptime': time.time() - (self.metrics.loop_count * self.loop_interval) if self.metrics.loop_count > 0 else 0,
            'loop_metrics': {
                'iterations': self.metrics.loop_count,
                'avg_loop_time': self.metrics.avg_loop_time,
                'last_loop_time': self.metrics.last_loop_time,
                'signals_processed': self.metrics.signals_processed,
                'orders_placed': self.metrics.orders_placed,
                'errors': self.metrics.errors_count,
                'cache_hit_rate': self.metrics.cache_hit_rate,
                'concurrent_tasks': self.metrics.concurrent_tasks
            },
            'queue_status': {
                'signals_queued': self.signal_queue.qsize(),
                'orders_queued': self.order_queue.qsize()
            },
            'client_metrics': client_metrics,
            'performance_available': PERFORMANCE_AVAILABLE
        }


# Convenience functions
async def create_optimized_trading_loop(config: Dict[str, Any]) -> AsyncTradingLoop:
    """Create and configure optimized trading loop"""
    loop = AsyncTradingLoop(config)
    return loop


async def run_trading_session(config: Dict[str, Any], duration_minutes: Optional[int] = None):
    """Run a complete trading session with automatic cleanup"""
    loop = await create_optimized_trading_loop(config)
    
    try:
        await loop.start()
        
        if duration_minutes:
            await asyncio.sleep(duration_minutes * 60)
            await loop.stop()
        else:
            # Run indefinitely until manually stopped
            while loop.state == TradingState.RUNNING:
                await asyncio.sleep(10)
    
    except KeyboardInterrupt:
        print("Received interrupt signal")
    finally:
        await loop.stop()
        print("Trading session ended")


# Example usage
async def example_trading_session():
    """Example optimized trading session"""
    config = {
        'symbols': ['BTCUSDT', 'ETHUSDT'],
        'loop_interval': 2.0,
        'dry_run': True,
        'max_concurrent_operations': 15,
        'testnet': True,
        'api_key': 'your_api_key',
        'api_secret': 'your_api_secret'
    }
    
    loop = await create_optimized_trading_loop(config)
    
    try:
        await loop.start()
        
        # Let it run for a bit
        await asyncio.sleep(30)
        
        # Check status
        status = loop.get_status()
        print(f"Loop Status: {json.dumps(status, indent=2, default=str)}")
        
    finally:
        await loop.stop()


if __name__ == "__main__":
    asyncio.run(example_trading_session())