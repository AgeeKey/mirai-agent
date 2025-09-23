# Mirai Trading SDK for Python

Official Python SDK for the Mirai Trading System - an autonomous cryptocurrency trading platform with AI-powered decision making.

## Features

- **Complete API Coverage**: Access all Mirai Trading API endpoints
- **Real-time Data**: WebSocket support for live trading updates
- **Async/Await Support**: Built for modern Python async applications
- **Type Safety**: Full type hints and data validation
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Retry Logic**: Automatic retry with exponential backoff
- **Rate Limiting**: Built-in rate limit handling
- **Performance Optimized**: Connection pooling and caching support

## Installation

```bash
pip install mirai-trading-sdk
```

For development:
```bash
pip install mirai-trading-sdk[dev]
```

## Quick Start

### Basic Usage

```python
import asyncio
from mirai_sdk import MiraiClient

async def main():
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
            print(f"{signal.symbol}: {signal.direction} "
                  f"(strength: {signal.strength:.2f})")

if __name__ == "__main__":
    asyncio.run(main())
```

### Authentication

For production environments with authentication:

```python
from mirai_sdk import MiraiClient, MiraiConfig

config = MiraiConfig(
    api_url="https://api.mirai-trading.com",
    api_key="your_api_key_here",
    timeout=30
)

async with MiraiClient(config) as client:
    # Your code here
    pass
```

### Trading Operations

```python
# Place a market order
order_result = await client.place_market_order(
    symbol="BTCUSDT",
    side="BUY",
    quantity=0.001,
    stop_loss=50000.0,
    take_profit=60000.0
)
print(f"Order ID: {order_result.order_id}")

# Place a limit order
order_result = await client.place_limit_order(
    symbol="ETHUSDT",
    side="SELL",
    quantity=0.1,
    price=3500.0
)

# Get current positions
positions = await client.get_positions()
for position in positions:
    print(f"{position.symbol}: {position.side} {position.size}")
```

### Real-time Data Streaming

```python
# Setup WebSocket callbacks
def on_trade_update(data):
    print(f"Trade: {data['symbol']} {data['side']} {data['quantity']}")

def on_price_update(data):
    print(f"Price: {data['symbol']} = ${data['price']}")

def on_ai_signal(data):
    print(f"Signal: {data['symbol']} {data['direction']} "
          f"(strength: {data['strength']:.2f})")

# Subscribe to events
client.subscribe_trades(on_trade_update)
client.subscribe_prices(on_price_update)
client.subscribe_signals(on_ai_signal)

# Connect and listen
await client.connect_websocket()

# Keep running
while True:
    await asyncio.sleep(1)
```

### Error Handling

```python
from mirai_sdk import MiraiAPIError, MiraiRateLimitError, MiraiConnectionError

try:
    status = await client.get_trading_status()
except MiraiRateLimitError:
    print("Rate limited - please wait")
    await asyncio.sleep(60)
except MiraiAPIError as e:
    print(f"API Error: {e.error_code} - {e}")
except MiraiConnectionError as e:
    print(f"Connection failed: {e}")
```

## API Reference

### Client Configuration

```python
from mirai_sdk import MiraiConfig

config = MiraiConfig(
    api_url="http://localhost:8001",      # API base URL
    api_key=None,                         # API key for authentication
    timeout=30,                           # Request timeout in seconds
    max_retries=3,                        # Maximum retry attempts
    retry_delay=1.0,                      # Initial retry delay
    enable_logging=True,                  # Enable SDK logging
    log_level="INFO"                      # Logging level
)
```

### Trading Status

```python
# Get comprehensive trading status
status = await client.get_trading_status()

print(f"Active: {status.is_active}")
print(f"Mode: {status.mode}")
print(f"Balance: ${status.balance['total']}")
print(f"Daily P&L: ${status.daily_pnl}")
print(f"Win Rate: {status.win_rate}%")
print(f"AI Confidence: {status.ai_confidence}")

# Access strategy information
for name, strategy in status.strategies.items():
    print(f"{name}: {strategy['status']} (Win Rate: {strategy['win_rate']}%)")
```

### Market Data

```python
# Get performance data
performance = await client.get_performance_data()
for point in performance['performance']:
    print(f"{point['time']}: P&L ${point['pnl']}, Equity ${point['equity']}")

# Get recent trades
trades = await client.get_recent_trades(limit=10, symbol="BTCUSDT")
for trade in trades:
    print(f"{trade.timestamp}: {trade.action} {trade.quantity} "
          f"{trade.symbol} @ ${trade.price} (P&L: ${trade.pnl})")

# Get AI analysis for specific symbol
analysis = await client.get_ai_analysis("BTCUSDT")
print(f"Trend: {analysis['analysis']['trend']}")
print(f"Recommendation: {analysis['analysis']['recommendation']}")
print(f"Target: ${analysis['analysis']['target_price']}")
```

### Order Management

```python
from mirai_sdk import Order

# Create custom order
order = Order(
    symbol="BTCUSDT",
    side="BUY",
    type="LIMIT",
    quantity=0.001,
    price=58000.0,
    stop_loss=57000.0,
    take_profit=60000.0
)

result = await client.place_order(order)
print(f"Order placed: {result.order_id}")

# Wait for order completion
completed_order = await client.wait_for_order(result.order_id, timeout=60)
if completed_order:
    print("Order completed!")
else:
    print("Order timeout")
```

### Performance Monitoring

```python
# Get performance optimization summary
perf_summary = await client.get_performance_summary()
print(f"Cache hit rate: {perf_summary['data']['cache_performance']['hit_rate']:.2%}")

# Get cache statistics
cache_stats = await client.get_cache_stats()
print(f"Cache requests: {cache_stats['cache_stats']['total_requests']}")

# Invalidate cache
await client.invalidate_cache("market_data")
```

## Advanced Usage

### Custom Event Handling

```python
class TradingBot:
    def __init__(self, client):
        self.client = client
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        self.client.subscribe_trades(self.on_trade)
        self.client.subscribe_signals(self.on_signal)
    
    async def on_trade(self, trade_data):
        # Handle trade updates
        if trade_data['pnl'] > 0:
            print(f"Profitable trade: +${trade_data['pnl']}")
    
    async def on_signal(self, signal_data):
        # Handle AI signals
        if signal_data['strength'] > 0.8:
            await self.execute_signal(signal_data)
    
    async def execute_signal(self, signal):
        try:
            if signal['direction'] == 'BUY':
                result = await self.client.place_market_order(
                    symbol=signal['symbol'],
                    side='BUY',
                    quantity=0.001
                )
                print(f"Executed buy order: {result.order_id}")
        except Exception as e:
            print(f"Failed to execute signal: {e}")

# Usage
async with MiraiClient() as client:
    bot = TradingBot(client)
    await client.connect_websocket()
    
    # Run bot
    while True:
        await asyncio.sleep(1)
```

### Batch Operations

```python
# Get multiple data points concurrently
tasks = [
    client.get_trading_status(),
    client.get_recent_trades(limit=5),
    client.get_ai_signals(),
    client.get_positions()
]

results = await asyncio.gather(*tasks)
status, trades, signals, positions = results

print(f"Status: {status.daily_pnl}")
print(f"Recent trades: {len(trades)}")
print(f"Active signals: {len(signals)}")
print(f"Open positions: {len(positions)}")
```

### Configuration Management

```python
import os
from mirai_sdk import MiraiConfig

# Load from environment variables
config = MiraiConfig(
    api_url=os.getenv("MIRAI_API_URL", "http://localhost:8001"),
    api_key=os.getenv("MIRAI_API_KEY"),
    timeout=int(os.getenv("MIRAI_TIMEOUT", "30")),
    max_retries=int(os.getenv("MIRAI_MAX_RETRIES", "3"))
)

# Use with client
async with MiraiClient(config) as client:
    # Your code here
    pass
```

## Data Models

The SDK provides typed data models for all API responses:

- `TradingStatus`: Complete trading system status
- `Trade`: Individual trade information
- `Position`: Current position data
- `AISignal`: AI-generated trading signals
- `Order`: Order placement data
- `OrderResult`: Order execution results

All models include `from_dict()` class methods for easy deserialization.

## Error Handling

The SDK provides specific exception types:

- `MiraiError`: Base exception class
- `MiraiAPIError`: API-specific errors (4xx, 5xx responses)
- `MiraiConnectionError`: Network/connection issues
- `MiraiRateLimitError`: Rate limiting errors

## Testing

```bash
# Install development dependencies
pip install mirai-trading-sdk[dev]

# Run tests
pytest

# Run with coverage
pytest --cov=mirai_sdk --cov-report=html

# Run async tests
pytest -m asyncio
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Create a pull request

## License

MIT License - see LICENSE file for details.

## Support

- **Documentation**: [https://docs.mirai-trading.com](https://docs.mirai-trading.com)
- **GitHub Issues**: [https://github.com/your-org/mirai-agent/issues](https://github.com/your-org/mirai-agent/issues)
- **Discord**: [https://discord.gg/mirai-trading](https://discord.gg/mirai-trading)
- **Email**: sdk@mirai-trading.com

## Changelog

### 1.0.0 (2024-01-15)
- Initial release
- Complete API coverage
- WebSocket support
- Async/await compatibility
- Type safety with data models
- Comprehensive error handling
- Performance optimizations