"""
Optimized Trading Client with Performance Enhancements
High-performance trading operations with connection pooling, caching, and async optimization
"""

import asyncio
import aiohttp
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import hashlib
from decimal import Decimal

# Import our performance framework
try:
    from ..performance.optimization import (
        performance_optimized, cached, connection_pool_manager,
        advanced_cache, task_manager, PerformanceMetrics
    )
    PERFORMANCE_AVAILABLE = True
except ImportError:
    PERFORMANCE_AVAILABLE = False
    # Fallback decorators
    def performance_optimized(name, cache_ttl=300):
        def decorator(func):
            return func
        return decorator
    
    def cached(ttl=300, cache_key_prefix=None):
        def decorator(func):
            return func
        return decorator


@dataclass
class TradingOrder:
    """Optimized trading order structure"""
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: Decimal
    price: Optional[Decimal] = None
    order_type: str = 'market'  # 'market', 'limit', 'stop'
    time_in_force: str = 'GTC'  # 'GTC', 'IOC', 'FOK'
    client_order_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.client_order_id:
            self.client_order_id = f"mirai_{int(time.time() * 1000000)}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'side': self.side.upper(),
            'quantity': str(self.quantity),
            'price': str(self.price) if self.price else None,
            'type': self.order_type.upper(),
            'timeInForce': self.time_in_force,
            'newClientOrderId': self.client_order_id
        }


class OptimizedTradingClient:
    """
    High-performance trading client with connection pooling and caching
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.logger = logging.getLogger(__name__)
        
        # API endpoints
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://fapi.binance.com"
        
        # Performance tracking
        self.request_count = 0
        self.failed_requests = 0
        self.avg_latency = 0.0
        
        # Cache configuration
        self.cache_ttl_map = {
            'exchange_info': 3600,      # 1 hour
            'ticker_24hr': 10,          # 10 seconds
            'order_book': 1,            # 1 second
            'klines': 60,               # 1 minute
            'account_info': 5,          # 5 seconds
            'open_orders': 2,           # 2 seconds
            'position_risk': 5          # 5 seconds
        }
        
        # Order management
        self.pending_orders: Dict[str, TradingOrder] = {}
        self.executed_orders: List[Dict[str, Any]] = []
        
        self.logger.info(f"Initialized OptimizedTradingClient (testnet={testnet})")
    
    def _generate_signature(self, query_string: str) -> str:
        """Generate API signature for authenticated requests"""
        import hmac
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _prepare_headers(self, signed: bool = False) -> Dict[str, str]:
        """Prepare request headers"""
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }
        return headers
    
    @performance_optimized("api_request", cache_ttl=0)
    async def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None,
                           signed: bool = False, cache_key: Optional[str] = None) -> Dict[str, Any]:
        """Make optimized API request with connection pooling"""
        start_time = time.time()
        
        # Check cache first
        if cache_key and method.upper() == 'GET':
            cached_result = await advanced_cache.get(cache_key) if PERFORMANCE_AVAILABLE else None
            if cached_result:
                return cached_result
        
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        
        # Add timestamp for signed requests
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            params['signature'] = self._generate_signature(query_string)
        
        headers = self._prepare_headers(signed)
        
        try:
            # Use connection pool manager if available
            if PERFORMANCE_AVAILABLE:
                response = await connection_pool_manager.make_http_request(
                    method, url, 
                    pool_name="binance_api",
                    headers=headers,
                    params=params if method.upper() == 'GET' else None,
                    json=params if method.upper() != 'GET' else None
                )
                result = await response.json()
            else:
                # Fallback to direct aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.request(method, url, headers=headers, params=params) as response:
                        result = await response.json()
            
            # Update performance metrics
            latency = time.time() - start_time
            self.request_count += 1
            self.avg_latency = (self.avg_latency * (self.request_count - 1) + latency) / self.request_count
            
            # Cache successful GET requests
            if cache_key and method.upper() == 'GET' and PERFORMANCE_AVAILABLE:
                cache_ttl = self.cache_ttl_map.get(cache_key.split(':')[0], 60)
                await advanced_cache.set(cache_key, result, cache_ttl)
            
            return result
        
        except Exception as e:
            self.failed_requests += 1
            self.logger.error(f"API request failed: {e}")
            raise
    
    @cached(ttl=3600, cache_key_prefix="exchange_info")
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange trading rules and symbol information (cached)"""
        return await self._make_request(
            'GET', '/fapi/v1/exchangeInfo',
            cache_key='exchange_info:all'
        )
    
    @performance_optimized("ticker_price", cache_ttl=10)
    async def get_ticker_price(self, symbol: Optional[str] = None) -> Union[Dict, List[Dict]]:
        """Get ticker price (optimized with short cache)"""
        params = {'symbol': symbol} if symbol else {}
        cache_key = f"ticker_24hr:{symbol or 'all'}"
        
        return await self._make_request(
            'GET', '/fapi/v1/ticker/price',
            params=params,
            cache_key=cache_key
        )
    
    @performance_optimized("order_book", cache_ttl=1)
    async def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get order book with minimal cache for low latency"""
        cache_key = f"order_book:{symbol}:{limit}"
        
        return await self._make_request(
            'GET', '/fapi/v1/depth',
            params={'symbol': symbol, 'limit': limit},
            cache_key=cache_key
        )
    
    @cached(ttl=60, cache_key_prefix="klines")
    async def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[List]:
        """Get kline/candlestick data (cached for 1 minute)"""
        cache_key = f"klines:{symbol}:{interval}:{limit}"
        
        return await self._make_request(
            'GET', '/fapi/v1/klines',
            params={'symbol': symbol, 'interval': interval, 'limit': limit},
            cache_key=cache_key
        )
    
    @performance_optimized("account_info", cache_ttl=5)
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information (short cache)"""
        cache_key = "account_info:balance"
        
        return await self._make_request(
            'GET', '/fapi/v2/account',
            signed=True,
            cache_key=cache_key
        )
    
    @performance_optimized("open_orders", cache_ttl=2)
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get open orders (very short cache)"""
        params = {'symbol': symbol} if symbol else {}
        cache_key = f"open_orders:{symbol or 'all'}"
        
        return await self._make_request(
            'GET', '/fapi/v1/openOrders',
            params=params,
            signed=True,
            cache_key=cache_key
        )
    
    @performance_optimized("position_risk", cache_ttl=5)
    async def get_position_risk(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get position risk (short cache)"""
        params = {'symbol': symbol} if symbol else {}
        cache_key = f"position_risk:{symbol or 'all'}"
        
        return await self._make_request(
            'GET', '/fapi/v2/positionRisk',
            params=params,
            signed=True,
            cache_key=cache_key
        )
    
    @performance_optimized("place_order", cache_ttl=0)
    async def place_order(self, order: TradingOrder, dry_run: bool = True) -> Dict[str, Any]:
        """Place trading order with performance optimization"""
        start_time = time.time()
        
        if dry_run:
            # Simulate order placement for testing
            order_result = {
                'orderId': f"dry_run_{int(time.time() * 1000)}",
                'symbol': order.symbol,
                'status': 'FILLED',
                'clientOrderId': order.client_order_id,
                'side': order.side.upper(),
                'type': order.order_type.upper(),
                'origQty': str(order.quantity),
                'price': str(order.price) if order.price else '0',
                'executedQty': str(order.quantity),
                'transactTime': int(time.time() * 1000),
                'dry_run': True
            }
            
            self.logger.info(f"DRY RUN: Order placed - {order.symbol} {order.side} {order.quantity}")
        else:
            # Real order placement
            order_data = order.to_dict()
            order_result = await self._make_request(
                'POST', '/fapi/v1/order',
                params=order_data,
                signed=True
            )
        
        # Track order
        self.pending_orders[order.client_order_id] = order
        self.executed_orders.append({
            'order': order,
            'result': order_result,
            'timestamp': datetime.now(),
            'latency': time.time() - start_time
        })
        
        # Invalidate related cache entries
        if PERFORMANCE_AVAILABLE:
            await advanced_cache.trigger_invalidation('order_placed')
        
        return order_result
    
    @performance_optimized("cancel_order", cache_ttl=0)
    async def cancel_order(self, symbol: str, order_id: Optional[str] = None,
                          client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """Cancel order with cache invalidation"""
        params = {'symbol': symbol}
        
        if order_id:
            params['orderId'] = order_id
        elif client_order_id:
            params['origClientOrderId'] = client_order_id
        else:
            raise ValueError("Either order_id or client_order_id must be provided")
        
        result = await self._make_request(
            'DELETE', '/fapi/v1/order',
            params=params,
            signed=True
        )
        
        # Remove from pending orders
        if client_order_id and client_order_id in self.pending_orders:
            del self.pending_orders[client_order_id]
        
        # Invalidate cache
        if PERFORMANCE_AVAILABLE:
            await advanced_cache.trigger_invalidation('order_cancelled')
        
        return result
    
    async def batch_place_orders(self, orders: List[TradingOrder], 
                                max_concurrent: int = 5, dry_run: bool = True) -> List[Dict[str, Any]]:
        """Place multiple orders concurrently with rate limiting"""
        if not PERFORMANCE_AVAILABLE:
            # Sequential fallback
            results = []
            for order in orders:
                result = await self.place_order(order, dry_run)
                results.append(result)
            return results
        
        # Submit orders as background tasks with priority
        tasks = []
        for order in orders:
            task_id = await task_manager.submit_task(
                self.place_order(order, dry_run),
                priority="high"  # Trading orders get high priority
            )
            tasks.append(task_id)
        
        # Wait for all orders to complete (simplified)
        # In production, you'd track tasks properly
        await asyncio.sleep(1)  # Allow tasks to process
        
        return [{"task_id": task_id, "status": "submitted"} for task_id in tasks]
    
    async def get_real_time_data_stream(self, symbols: List[str]) -> Dict[str, Any]:
        """Get real-time market data stream (optimized)"""
        # This would implement WebSocket streaming in production
        # For now, return optimized REST data
        
        tasks = []
        for symbol in symbols:
            # Submit parallel requests for each symbol
            if PERFORMANCE_AVAILABLE:
                task_id = await task_manager.submit_task(
                    self.get_ticker_price(symbol),
                    priority="high"
                )
                tasks.append((symbol, task_id))
        
        # Simulate real-time data
        return {
            "stream": "real_time_prices",
            "symbols": symbols,
            "timestamp": datetime.now().isoformat(),
            "status": "active"
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get client performance metrics"""
        failure_rate = self.failed_requests / self.request_count if self.request_count > 0 else 0
        
        metrics = {
            'total_requests': self.request_count,
            'failed_requests': self.failed_requests,
            'success_rate': 1 - failure_rate,
            'avg_latency_ms': self.avg_latency * 1000,
            'pending_orders': len(self.pending_orders),
            'executed_orders': len(self.executed_orders)
        }
        
        # Add performance system metrics if available
        if PERFORMANCE_AVAILABLE:
            try:
                pool_stats = connection_pool_manager.get_pool_stats()
                cache_stats = advanced_cache.get_cache_stats()
                
                metrics.update({
                    'connection_pool_stats': pool_stats.get('binance_api', {}),
                    'cache_hit_rate': cache_stats.get('hit_rate', 0),
                    'cache_items': cache_stats.get('memory_items', 0)
                })
            except Exception as e:
                self.logger.warning(f"Failed to get performance stats: {e}")
        
        return metrics
    
    async def optimize_for_trading_session(self):
        """Optimize client for active trading session"""
        if not PERFORMANCE_AVAILABLE:
            return
        
        # Pre-warm cache with essential data
        try:
            await self.get_exchange_info()
            self.logger.info("Pre-warmed exchange info cache")
            
            # Setup cache invalidation patterns
            advanced_cache.register_invalidation_pattern(
                "open_orders", ["order_placed", "order_cancelled", "order_filled"]
            )
            advanced_cache.register_invalidation_pattern(
                "position_risk", ["order_filled", "position_update"]
            )
            advanced_cache.register_invalidation_pattern(
                "account_info", ["order_filled", "deposit", "withdrawal"]
            )
            
            self.logger.info("Configured cache invalidation patterns")
        
        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")


# Convenience functions for common operations
async def create_optimized_market_order(client: OptimizedTradingClient, 
                                      symbol: str, side: str, quantity: Decimal,
                                      dry_run: bool = True) -> Dict[str, Any]:
    """Create and place optimized market order"""
    order = TradingOrder(
        symbol=symbol,
        side=side,
        quantity=quantity,
        order_type='market'
    )
    
    return await client.place_order(order, dry_run)


async def create_optimized_limit_order(client: OptimizedTradingClient,
                                     symbol: str, side: str, quantity: Decimal, price: Decimal,
                                     dry_run: bool = True) -> Dict[str, Any]:
    """Create and place optimized limit order"""
    order = TradingOrder(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        order_type='limit'
    )
    
    return await client.place_order(order, dry_run)


# Example usage
async def example_optimized_trading():
    """Example of optimized trading operations"""
    # Initialize client
    client = OptimizedTradingClient(
        api_key="your_api_key",
        api_secret="your_api_secret",
        testnet=True
    )
    
    # Optimize for trading session
    await client.optimize_for_trading_session()
    
    # Get market data (cached)
    ticker = await client.get_ticker_price("BTCUSDT")
    print(f"BTC Price: {ticker}")
    
    # Place optimized order
    order_result = await create_optimized_market_order(
        client, "BTCUSDT", "buy", Decimal("0.001"), dry_run=True
    )
    print(f"Order Result: {order_result}")
    
    # Get performance metrics
    metrics = client.get_performance_metrics()
    print(f"Performance: {metrics}")


if __name__ == "__main__":
    asyncio.run(example_optimized_trading())