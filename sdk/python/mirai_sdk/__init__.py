"""
Mirai Trading System - Python SDK
Official Python client library for the Mirai Trading API
"""

import asyncio
import aiohttp
import websockets
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
import time
from urllib.parse import urljoin


__version__ = "1.0.0"
__author__ = "Mirai Trading Team"


@dataclass
class MiraiConfig:
    """Configuration for Mirai SDK"""
    api_url: str = "http://localhost:8001"
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_logging: bool = True
    log_level: str = "INFO"


@dataclass
class TradingStatus:
    """Trading status data structure"""
    is_active: bool
    mode: str
    balance: Dict[str, float]
    daily_pnl: float
    win_rate: float
    risk_level: str
    ai_confidence: float
    strategies: Dict[str, Dict[str, Any]]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingStatus':
        return cls(**data)


@dataclass
class Trade:
    """Trade data structure"""
    id: int
    symbol: str
    action: str
    price: float
    quantity: float
    pnl: float
    timestamp: str
    strategy: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trade':
        return cls(**data)


@dataclass
class Position:
    """Position data structure"""
    symbol: str
    side: str
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    margin_used: float
    leverage: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Position':
        return cls(**data)


@dataclass
class AISignal:
    """AI trading signal data structure"""
    symbol: str
    direction: str
    strength: float
    confidence: float
    strategy: str
    timestamp: str
    reasoning: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AISignal':
        return cls(**data)


@dataclass
class Order:
    """Order data structure"""
    symbol: str
    side: str
    type: str
    quantity: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class OrderResult:
    """Order execution result"""
    order_id: str
    status: str
    symbol: str
    side: str
    executed_price: Optional[float]
    executed_quantity: float
    timestamp: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderResult':
        return cls(**data)


class MiraiError(Exception):
    """Base exception for Mirai SDK"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 status_code: Optional[int] = None):
        super().__init__(message)
        self.error_code = error_code
        self.status_code = status_code


class MiraiAPIError(MiraiError):
    """API-specific errors"""
    pass


class MiraiConnectionError(MiraiError):
    """Connection-related errors"""
    pass


class MiraiRateLimitError(MiraiError):
    """Rate limiting errors"""
    pass


class MiraiWebSocketClient:
    """WebSocket client for real-time data"""
    
    def __init__(self, ws_url: str, logger: logging.Logger):
        self.ws_url = ws_url
        self.logger = logger
        self.ws = None
        self.callbacks: Dict[str, List[Callable]] = {}
        self.running = False
        self.reconnect_delay = 1.0
        self.max_reconnect_delay = 30.0
    
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to specific event type"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from event type"""
        if event_type in self.callbacks:
            try:
                self.callbacks[event_type].remove(callback)
            except ValueError:
                pass
    
    async def connect(self):
        """Connect to WebSocket"""
        try:
            self.ws = await websockets.connect(self.ws_url)
            self.running = True
            self.reconnect_delay = 1.0  # Reset delay on successful connection
            self.logger.info(f"Connected to WebSocket: {self.ws_url}")
            
            # Start message handler
            await self._handle_messages()
        
        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {e}")
            if self.running:
                await self._reconnect()
    
    async def _handle_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    event_type = data.get('type')
                    
                    if event_type and event_type in self.callbacks:
                        for callback in self.callbacks[event_type]:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(data.get('data', data))
                                else:
                                    callback(data.get('data', data))
                            except Exception as e:
                                self.logger.error(f"Callback error: {e}")
                
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Invalid JSON received: {e}")
                except Exception as e:
                    self.logger.error(f"Message handling error: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket connection closed")
            if self.running:
                await self._reconnect()
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
            if self.running:
                await self._reconnect()
    
    async def _reconnect(self):
        """Reconnect with exponential backoff"""
        if not self.running:
            return
        
        self.logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
        await asyncio.sleep(self.reconnect_delay)
        
        # Exponential backoff
        self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
        
        await self.connect()
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        self.running = False
        if self.ws:
            await self.ws.close()


class MiraiClient:
    """
    Main Mirai Trading API client
    """
    
    def __init__(self, config: Union[MiraiConfig, str, None] = None, **kwargs):
        # Handle different config types
        if isinstance(config, str):
            # If string provided, treat as API URL
            self.config = MiraiConfig(api_url=config, **kwargs)
        elif isinstance(config, MiraiConfig):
            self.config = config
        else:
            # Create config from kwargs
            self.config = MiraiConfig(**kwargs)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        if self.config.enable_logging:
            logging.basicConfig(
                level=getattr(logging, self.config.log_level),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        
        # WebSocket client
        ws_url = self.config.api_url.replace('http', 'ws') + '/ws'
        self.ws_client = MiraiWebSocketClient(ws_url, self.logger)
        
        self.logger.info(f"Mirai SDK initialized (version {__version__})")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure HTTP session is created"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            headers = {
                'User-Agent': f'MiraiSDK/{__version__}',
                'Content-Type': 'application/json'
            }
            
            if self.config.api_key:
                headers['Authorization'] = f'Bearer {self.config.api_key}'
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
    
    async def _request(self, method: str, endpoint: str, 
                      params: Optional[Dict] = None, 
                      json_data: Optional[Dict] = None,
                      retry_count: int = 0) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        await self._ensure_session()
        
        url = urljoin(self.config.api_url, endpoint)
        
        try:
            async with self.session.request(
                method, url, params=params, json=json_data
            ) as response:
                
                # Handle rate limiting
                if response.status == 429:
                    if retry_count < self.config.max_retries:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        self.logger.warning(f"Rate limited, retrying in {retry_after}s")
                        await asyncio.sleep(retry_after)
                        return await self._request(method, endpoint, params, json_data, retry_count + 1)
                    else:
                        raise MiraiRateLimitError("Rate limit exceeded and max retries reached")
                
                # Handle other HTTP errors
                if response.status >= 400:
                    try:
                        error_data = await response.json()
                        error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                        error_code = error_data.get('error', {}).get('code')
                        raise MiraiAPIError(error_msg, error_code, response.status)
                    except json.JSONDecodeError:
                        raise MiraiAPIError(f"HTTP {response.status}", status_code=response.status)
                
                # Parse successful response
                try:
                    return await response.json()
                except json.JSONDecodeError:
                    if response.status == 200:
                        return {'status': 'success'}
                    raise MiraiAPIError("Invalid JSON response")
        
        except aiohttp.ClientError as e:
            if retry_count < self.config.max_retries:
                delay = self.config.retry_delay * (2 ** retry_count)
                self.logger.warning(f"Request failed, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
                return await self._request(method, endpoint, params, json_data, retry_count + 1)
            else:
                raise MiraiConnectionError(f"Connection failed: {e}")
    
    # Health & Status Methods
    async def get_health(self) -> Dict[str, Any]:
        """Get API health status"""
        return await self._request('GET', '/api/health')
    
    async def get_trading_status(self) -> TradingStatus:
        """Get current trading status"""
        data = await self._request('GET', '/api/trading/status')
        return TradingStatus.from_dict(data)
    
    # Trading Data Methods
    async def get_performance_data(self) -> Dict[str, Any]:
        """Get performance data over time"""
        return await self._request('GET', '/api/trading/performance')
    
    async def get_recent_trades(self, limit: int = 50, symbol: Optional[str] = None,
                               strategy: Optional[str] = None) -> List[Trade]:
        """Get recent trades"""
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        if strategy:
            params['strategy'] = strategy
        
        data = await self._request('GET', '/api/trading/trades', params=params)
        return [Trade.from_dict(trade) for trade in data.get('trades', [])]
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        data = await self._request('GET', '/api/trading/positions')
        return [Position.from_dict(pos) for pos in data.get('positions', [])]
    
    # Order Management Methods
    async def place_order(self, order: Union[Order, Dict[str, Any]]) -> OrderResult:
        """Place a trading order"""
        if isinstance(order, Order):
            order_data = order.to_dict()
        else:
            order_data = order
        
        result = await self._request('POST', '/api/trading/order', json_data=order_data)
        return OrderResult.from_dict(result)
    
    async def place_market_order(self, symbol: str, side: str, quantity: float,
                                stop_loss: Optional[float] = None,
                                take_profit: Optional[float] = None) -> OrderResult:
        """Convenience method for market orders"""
        order = Order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        return await self.place_order(order)
    
    async def place_limit_order(self, symbol: str, side: str, quantity: float, price: float,
                               stop_loss: Optional[float] = None,
                               take_profit: Optional[float] = None) -> OrderResult:
        """Convenience method for limit orders"""
        order = Order(
            symbol=symbol,
            side=side,
            type='LIMIT',
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        return await self.place_order(order)
    
    # AI & Analysis Methods
    async def get_ai_signals(self) -> List[AISignal]:
        """Get current AI trading signals"""
        data = await self._request('GET', '/api/ai/signals')
        return [AISignal.from_dict(signal) for signal in data.get('signals', [])]
    
    async def get_ai_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get detailed AI analysis for symbol"""
        return await self._request('GET', f'/api/ai/analysis/{symbol}')
    
    # Monitoring Methods
    async def get_metrics(self) -> str:
        """Get Prometheus metrics"""
        response = await self._request('GET', '/api/metrics')
        return response if isinstance(response, str) else str(response)
    
    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts"""
        data = await self._request('GET', '/api/alerts')
        return data.get('alerts', [])
    
    # Performance Methods
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance optimization summary"""
        return await self._request('GET', '/api/performance/summary')
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        return await self._request('GET', '/api/performance/cache/stats')
    
    async def invalidate_cache(self, pattern: str) -> Dict[str, Any]:
        """Invalidate cache entries matching pattern"""
        return await self._request('POST', '/api/performance/cache/invalidate', 
                                 json_data={'pattern': pattern})
    
    # WebSocket Methods
    async def connect_websocket(self):
        """Connect to WebSocket for real-time data"""
        await self.ws_client.connect()
    
    def subscribe_trades(self, callback: Callable):
        """Subscribe to trade updates"""
        self.ws_client.subscribe('trade_update', callback)
    
    def subscribe_prices(self, callback: Callable):
        """Subscribe to price updates"""
        self.ws_client.subscribe('price_update', callback)
    
    def subscribe_signals(self, callback: Callable):
        """Subscribe to AI signals"""
        self.ws_client.subscribe('ai_signal', callback)
    
    def subscribe_all(self, callback: Callable):
        """Subscribe to all events"""
        self.subscribe_trades(callback)
        self.subscribe_prices(callback)
        self.subscribe_signals(callback)
    
    async def disconnect_websocket(self):
        """Disconnect from WebSocket"""
        await self.ws_client.disconnect()
    
    # Utility Methods
    async def wait_for_order(self, order_id: str, timeout: int = 60) -> Optional[Dict[str, Any]]:
        """Wait for order to be filled (using polling)"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                trades = await self.get_recent_trades(limit=10)
                for trade in trades:
                    # This is simplified - in real implementation you'd check order status endpoint
                    if hasattr(trade, 'order_id') and trade.order_id == order_id:
                        return trade
                
                await asyncio.sleep(1)  # Poll every second
            except Exception as e:
                self.logger.warning(f"Error polling for order {order_id}: {e}")
                await asyncio.sleep(5)
        
        return None
    
    async def close(self):
        """Close all connections"""
        await self.disconnect_websocket()
        
        if self.session:
            await self.session.close()
            self.session = None
        
        self.logger.info("Mirai SDK closed")


# Convenience Functions
async def create_client(api_url: str = "http://localhost:8001", 
                       api_key: Optional[str] = None, **kwargs) -> MiraiClient:
    """Create and return configured Mirai client"""
    config = MiraiConfig(api_url=api_url, api_key=api_key, **kwargs)
    client = MiraiClient(config)
    await client._ensure_session()
    return client


# Example Usage
async def example_usage():
    """Example SDK usage"""
    
    # Create client
    async with MiraiClient("http://localhost:8001") as client:
        
        # Check API health
        health = await client.get_health()
        print(f"API Status: {health['status']}")
        
        # Get trading status
        status = await client.get_trading_status()
        print(f"Daily P&L: ${status.daily_pnl}")
        print(f"Win Rate: {status.win_rate}%")
        
        # Get AI signals
        signals = await client.get_ai_signals()
        for signal in signals:
            print(f"Signal: {signal.symbol} {signal.direction} "
                  f"(strength: {signal.strength:.2f})")
        
        # Place a test order
        try:
            order_result = await client.place_market_order(
                symbol="BTCUSDT",
                side="BUY",
                quantity=0.001
            )
            print(f"Order placed: {order_result.order_id}")
        except MiraiAPIError as e:
            print(f"Order failed: {e}")
        
        # Subscribe to real-time updates
        def on_trade_update(data):
            print(f"New trade: {data['symbol']} {data['side']} {data['quantity']}")
        
        client.subscribe_trades(on_trade_update)
        await client.connect_websocket()
        
        # Run for 30 seconds
        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(example_usage())