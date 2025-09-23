# Mirai Trading System - Comprehensive API Documentation

## Overview

Mirai is an autonomous cryptocurrency trading system that combines artificial intelligence, risk management, and high-performance trading infrastructure. This documentation provides complete API reference, integration guides, and development resources.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [API Reference](#api-reference)
4. [WebSocket Streams](#websocket-streams)
5. [SDK Usage](#sdk-usage)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Examples](#examples)
9. [Troubleshooting](#troubleshooting)

## Quick Start

### Installation

```bash
# Using Docker (recommended)
docker pull ghcr.io/mirai-agent/mirai-api:latest
docker run -p 8001:8001 ghcr.io/mirai-agent/mirai-api:latest

# From source
git clone https://github.com/your-org/mirai-agent.git
cd mirai-agent/app/api
pip install -e .
uvicorn mirai_api.main:app --host 0.0.0.0 --port 8001
```

### Basic Usage

```python
import requests

# Check API health
response = requests.get("http://localhost:8001/api/health")
print(response.json())
# {"status": "healthy", "timestamp": "2024-01-15T10:30:00Z"}

# Get trading status
response = requests.get("http://localhost:8001/api/trading/status")
status = response.json()
print(f"Trading active: {status['is_active']}")
```

## Authentication

Mirai API uses JWT tokens for authentication in production environments.

### Obtaining an API Token

```bash
# Request token
curl -X POST http://localhost:8001/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

### Using Authentication Headers

```python
headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN",
    "Content-Type": "application/json"
}

response = requests.get(
    "http://localhost:8001/api/trading/account",
    headers=headers
)
```

## API Reference

### Health & Status Endpoints

#### GET /
**Description**: Root endpoint with basic system information.

```python
GET /
```

**Response**:
```json
{
  "message": "🤖 Mirai Trading API активен!",
  "status": "running"
}
```

#### GET /api/health
**Description**: Health check endpoint for monitoring.

```python
GET /api/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Trading Endpoints

#### GET /api/trading/status
**Description**: Get current trading system status and performance metrics.

```python
GET /api/trading/status
```

**Response**:
```json
{
  "is_active": true,
  "mode": "simulation",
  "balance": {
    "total": 10450.75,
    "available": 9200.30,
    "used": 1250.45
  },
  "daily_pnl": 450.75,
  "win_rate": 68.4,
  "risk_level": "medium",
  "ai_confidence": 0.85,
  "strategies": {
    "momentum_breakout": {
      "status": "active",
      "win_rate": 72
    },
    "mean_reversion": {
      "status": "standby", 
      "win_rate": 65
    },
    "grid_trading": {
      "status": "paused",
      "win_rate": 58
    }
  }
}
```

#### GET /api/trading/performance
**Description**: Get detailed performance data over time.

```python
GET /api/trading/performance
```

**Response**:
```json
{
  "performance": [
    {
      "time": "00:00",
      "pnl": 125.50,
      "equity": 10125.50,
      "trades": 2
    },
    {
      "time": "01:00", 
      "pnl": 180.25,
      "equity": 10180.25,
      "trades": 1
    }
  ]
}
```

#### GET /api/trading/trades
**Description**: Get recent trading history.

```python
GET /api/trading/trades
```

**Query Parameters**:
- `limit` (optional): Number of trades to return (default: 50, max: 1000)
- `symbol` (optional): Filter by trading pair (e.g., "BTCUSDT")
- `strategy` (optional): Filter by strategy name

**Response**:
```json
{
  "trades": [
    {
      "id": 1,
      "symbol": "BTCUSDT",
      "action": "BUY",
      "price": 58450.00,
      "quantity": 0.1,
      "pnl": 125.50,
      "timestamp": "2024-01-15T14:32:00Z",
      "strategy": "momentum_breakout"
    }
  ]
}
```

#### GET /api/trading/positions
**Description**: Get current open positions.

```python
GET /api/trading/positions
```

**Response**:
```json
{
  "positions": [
    {
      "symbol": "BTCUSDT",
      "side": "LONG",
      "size": 0.15,
      "entry_price": 58200.00,
      "current_price": 58450.00,
      "unrealized_pnl": 37.50,
      "margin_used": 873.00,
      "leverage": 10
    }
  ]
}
```

#### POST /api/trading/order
**Description**: Place a new trading order.

**Request Body**:
```json
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "type": "MARKET",
  "quantity": 0.001,
  "price": null,
  "stop_loss": 57000.00,
  "take_profit": 60000.00
}
```

**Response**:
```json
{
  "order_id": "abc123def456",
  "status": "FILLED",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "executed_price": 58450.00,
  "executed_quantity": 0.001,
  "timestamp": "2024-01-15T14:32:15Z"
}
```

### AI & Strategy Endpoints

#### GET /api/ai/signals
**Description**: Get current AI trading signals and analysis.

```python
GET /api/ai/signals
```

**Response**:
```json
{
  "signals": [
    {
      "symbol": "BTCUSDT",
      "direction": "BUY",
      "strength": 0.85,
      "confidence": 0.92,
      "strategy": "momentum_breakout",
      "timestamp": "2024-01-15T14:30:00Z",
      "reasoning": "Strong upward momentum with volume confirmation"
    }
  ]
}
```

#### GET /api/ai/analysis/{symbol}
**Description**: Get detailed AI analysis for a specific symbol.

```python
GET /api/ai/analysis/BTCUSDT
```

**Response**:
```json
{
  "symbol": "BTCUSDT",
  "analysis": {
    "trend": "BULLISH",
    "trend_strength": 0.78,
    "support_levels": [57500, 56800, 56000],
    "resistance_levels": [59000, 59800, 60500],
    "indicators": {
      "rsi": 68.5,
      "macd": {
        "macd": 125.8,
        "signal": 118.2,
        "histogram": 7.6
      },
      "bollinger_bands": {
        "upper": 59200,
        "middle": 58400,
        "lower": 57600
      }
    },
    "sentiment": "POSITIVE",
    "recommendation": "BUY",
    "target_price": 60000,
    "stop_loss": 57000
  }
}
```

### Monitoring & Metrics Endpoints

#### GET /api/metrics
**Description**: Get Prometheus-formatted metrics.

```python
GET /api/metrics
```

**Response**: Prometheus metrics format
```
# HELP trading_orders_total Total number of trading orders
# TYPE trading_orders_total counter
trading_orders_total{symbol="BTCUSDT",side="buy",status="filled"} 45

# HELP trading_pnl_total Total profit and loss
# TYPE trading_pnl_total gauge
trading_pnl_total{symbol="BTCUSDT"} 1250.75
```

#### GET /api/alerts
**Description**: Get active trading alerts.

```python
GET /api/alerts
```

**Response**:
```json
{
  "alerts": [
    {
      "id": "alert_001",
      "type": "price_movement",
      "severity": "warning",
      "message": "BTCUSDT price dropped 5% in 1 hour",
      "timestamp": "2024-01-15T14:25:00Z",
      "symbol": "BTCUSDT"
    }
  ]
}
```

### Performance Optimization Endpoints

#### GET /api/performance/summary
**Description**: Get comprehensive performance optimization summary.

```python
GET /api/performance/summary
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "connection_pools": {
      "http_pools": {
        "binance_api": {
          "active_connections": 5,
          "total_requests": 1250,
          "failed_requests": 3,
          "avg_response_time": 0.085
        }
      }
    },
    "cache_performance": {
      "hit_rate": 0.85,
      "total_requests": 2340,
      "memory_items": 456
    },
    "task_management": {
      "active_tasks": 12,
      "completed_tasks": 8945,
      "success_rate": 0.99
    }
  }
}
```

#### GET /api/performance/cache/stats
**Description**: Get detailed cache performance statistics.

```python
GET /api/performance/cache/stats
```

#### POST /api/performance/cache/invalidate
**Description**: Invalidate cache entries matching a pattern.

```python
POST /api/performance/cache/invalidate
Content-Type: application/json

{
  "pattern": "market_data"
}
```

## WebSocket Streams

Mirai provides real-time data streams via WebSocket connections.

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8001/ws');

ws.onopen = function(event) {
    console.log('Connected to Mirai WebSocket');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

### Message Types

#### Trading Updates
```json
{
  "type": "trade_update",
  "data": {
    "symbol": "BTCUSDT",
    "side": "BUY",
    "price": 58450.00,
    "quantity": 0.001,
    "timestamp": "2024-01-15T14:32:15Z"
  }
}
```

#### Price Updates
```json
{
  "type": "price_update",
  "data": {
    "symbol": "BTCUSDT",
    "price": 58450.00,
    "change_24h": 2.5,
    "volume_24h": 125000,
    "timestamp": "2024-01-15T14:32:15Z"
  }
}
```

#### AI Signals
```json
{
  "type": "ai_signal",
  "data": {
    "symbol": "BTCUSDT",
    "direction": "BUY",
    "strength": 0.85,
    "strategy": "momentum_breakout",
    "timestamp": "2024-01-15T14:32:15Z"
  }
}
```

## SDK Usage

### Python SDK

```python
from mirai_sdk import MiraiClient

# Initialize client
client = MiraiClient(
    api_url="http://localhost:8001",
    api_key="your_api_key"  # For production
)

# Get trading status
status = await client.get_trading_status()
print(f"Daily P&L: {status['daily_pnl']}")

# Get AI signals
signals = await client.get_ai_signals()
for signal in signals['signals']:
    print(f"{signal['symbol']}: {signal['direction']} - {signal['strength']}")

# Place order
order = await client.place_order(
    symbol="BTCUSDT",
    side="BUY",
    type="MARKET",
    quantity=0.001
)
print(f"Order placed: {order['order_id']}")

# Subscribe to real-time updates
async def on_trade_update(data):
    print(f"Trade: {data['symbol']} {data['side']} {data['quantity']}")

await client.subscribe_trades(callback=on_trade_update)
```

### JavaScript SDK

```javascript
import { MiraiClient } from '@mirai/sdk';

const client = new MiraiClient({
  apiUrl: 'http://localhost:8001',
  apiKey: 'your_api_key' // For production
});

// Get trading status
const status = await client.getTradingStatus();
console.log(`Daily P&L: ${status.daily_pnl}`);

// Subscribe to real-time data
client.subscribe('trades', (data) => {
  console.log(`Trade: ${data.symbol} ${data.side} ${data.quantity}`);
});

// Place order
const order = await client.placeOrder({
  symbol: 'BTCUSDT',
  side: 'BUY',
  type: 'MARKET',
  quantity: 0.001
});
```

## Error Handling

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error
- `503` - Service Unavailable

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_SYMBOL",
    "message": "Symbol 'INVALID' is not supported",
    "details": {
      "supported_symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
    },
    "timestamp": "2024-01-15T14:32:15Z"
  }
}
```

### Common Error Codes

- `INVALID_SYMBOL` - Trading symbol not supported
- `INSUFFICIENT_BALANCE` - Not enough funds for order
- `INVALID_QUANTITY` - Order quantity outside allowed range
- `MARKET_CLOSED` - Trading not available for symbol
- `RATE_LIMITED` - Too many requests, retry later
- `SYSTEM_MAINTENANCE` - System temporarily unavailable

## Rate Limiting

Mirai implements intelligent rate limiting to ensure fair usage and system stability.

### Rate Limits

- **Public endpoints**: 100 requests per minute
- **Trading endpoints**: 50 requests per minute
- **WebSocket connections**: 10 connections per IP
- **Bulk operations**: 10 requests per minute

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642256400
```

### Handling Rate Limits

```python
import time
import requests

def make_request_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url)
        
        if response.status_code == 429:
            # Rate limited, wait and retry
            retry_after = int(response.headers.get('Retry-After', 60))
            time.sleep(retry_after)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

## Examples

### Complete Trading Bot Example

```python
import asyncio
import logging
from mirai_sdk import MiraiClient

class SimpleTradingBot:
    def __init__(self, api_url, api_key=None):
        self.client = MiraiClient(api_url, api_key)
        self.logger = logging.getLogger(__name__)
    
    async def run(self):
        """Main bot loop"""
        try:
            # Check system status
            health = await self.client.get_health()
            if health['status'] != 'healthy':
                self.logger.error("API not healthy, exiting")
                return
            
            # Monitor trading signals
            while True:
                signals = await self.client.get_ai_signals()
                
                for signal in signals['signals']:
                    if signal['strength'] > 0.8:  # High confidence signals
                        await self.execute_signal(signal)
                
                await asyncio.sleep(30)  # Check every 30 seconds
        
        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user")
        except Exception as e:
            self.logger.error(f"Bot error: {e}")
    
    async def execute_signal(self, signal):
        """Execute a trading signal"""
        try:
            # Check current position
            positions = await self.client.get_positions()
            current_position = None
            
            for pos in positions['positions']:
                if pos['symbol'] == signal['symbol']:
                    current_position = pos
                    break
            
            # Simple strategy: follow strong signals
            if signal['direction'] == 'BUY' and not current_position:
                order = await self.client.place_order(
                    symbol=signal['symbol'],
                    side='BUY',
                    type='MARKET',
                    quantity=0.001  # Small position size
                )
                self.logger.info(f"Bought {signal['symbol']}: {order['order_id']}")
            
            elif signal['direction'] == 'SELL' and current_position:
                order = await self.client.place_order(
                    symbol=signal['symbol'],
                    side='SELL',
                    type='MARKET',
                    quantity=current_position['size']
                )
                self.logger.info(f"Sold {signal['symbol']}: {order['order_id']}")
        
        except Exception as e:
            self.logger.error(f"Failed to execute signal: {e}")

# Run the bot
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot = SimpleTradingBot("http://localhost:8001")
    asyncio.run(bot.run())
```

### Real-time Dashboard Example

```javascript
class MiraiDashboard {
    constructor(apiUrl) {
        this.client = new MiraiClient({ apiUrl });
        this.ws = null;
    }
    
    async initialize() {
        // Get initial data
        const status = await this.client.getTradingStatus();
        this.updateStatus(status);
        
        const trades = await this.client.getRecentTrades();
        this.updateTrades(trades);
        
        // Setup real-time updates
        this.setupWebSocket();
    }
    
    setupWebSocket() {
        this.ws = new WebSocket('ws://localhost:8001/ws');
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            switch(data.type) {
                case 'trade_update':
                    this.addTradeToTable(data.data);
                    break;
                case 'price_update':
                    this.updatePriceDisplay(data.data);
                    break;
                case 'ai_signal':
                    this.showSignalAlert(data.data);
                    break;
            }
        };
    }
    
    updateStatus(status) {
        document.getElementById('daily-pnl').textContent = 
            `$${status.daily_pnl.toFixed(2)}`;
        document.getElementById('win-rate').textContent = 
            `${status.win_rate}%`;
        document.getElementById('ai-confidence').textContent = 
            `${(status.ai_confidence * 100).toFixed(1)}%`;
    }
    
    addTradeToTable(trade) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${trade.symbol}</td>
            <td>${trade.side}</td>
            <td>$${trade.price.toFixed(2)}</td>
            <td>${trade.quantity}</td>
            <td>$${trade.pnl.toFixed(2)}</td>
            <td>${new Date(trade.timestamp).toLocaleTimeString()}</td>
        `;
        document.getElementById('trades-table').appendChild(row);
    }
    
    showSignalAlert(signal) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${signal.direction === 'BUY' ? 'success' : 'warning'}`;
        alert.innerHTML = `
            <strong>${signal.symbol}</strong> - ${signal.direction} 
            (Strength: ${(signal.strength * 100).toFixed(0)}%)
        `;
        document.getElementById('alerts-container').appendChild(alert);
        
        // Remove after 10 seconds
        setTimeout(() => alert.remove(), 10000);
    }
}

// Initialize dashboard
const dashboard = new MiraiDashboard('http://localhost:8001');
dashboard.initialize();
```

## Troubleshooting

### Common Issues

#### Connection Errors
```
Error: Connection refused to http://localhost:8001
```
**Solution**: Ensure the Mirai API server is running:
```bash
docker ps | grep mirai-api
# or
curl http://localhost:8001/api/health
```

#### Authentication Errors
```
{"error": {"code": "UNAUTHORIZED", "message": "Invalid token"}}
```
**Solution**: Check your API key and token expiration:
```python
# Refresh token
new_token = await client.refresh_token()
client.set_api_key(new_token)
```

#### Rate Limiting
```
{"error": {"code": "RATE_LIMITED", "message": "Too many requests"}}
```
**Solution**: Implement exponential backoff:
```python
import time
import random

def exponential_backoff(attempt):
    delay = (2 ** attempt) + random.uniform(0, 1)
    time.sleep(min(delay, 60))  # Max 60 seconds
```

#### WebSocket Disconnections
```
WebSocket connection closed unexpectedly
```
**Solution**: Implement auto-reconnection:
```javascript
class ReconnectingWebSocket {
    constructor(url) {
        this.url = url;
        this.reconnectDelay = 1000;
        this.maxReconnectDelay = 30000;
        this.connect();
    }
    
    connect() {
        this.ws = new WebSocket(this.url);
        
        this.ws.onclose = () => {
            setTimeout(() => {
                this.reconnectDelay = Math.min(
                    this.reconnectDelay * 2, 
                    this.maxReconnectDelay
                );
                this.connect();
            }, this.reconnectDelay);
        };
        
        this.ws.onopen = () => {
            this.reconnectDelay = 1000; // Reset delay
        };
    }
}
```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# For specific modules
logging.getLogger('mirai_sdk').setLevel(logging.DEBUG)
```

### Performance Issues

If experiencing slow response times:

1. **Check system status**:
   ```bash
   curl http://localhost:8001/api/performance/summary
   ```

2. **Monitor cache performance**:
   ```bash
   curl http://localhost:8001/api/performance/cache/stats
   ```

3. **Invalidate cache if needed**:
   ```bash
   curl -X POST http://localhost:8001/api/performance/cache/invalidate \
     -H "Content-Type: application/json" \
     -d '{"pattern": "market_data"}'
   ```

### Support

For additional support:

- **Documentation**: [https://docs.mirai-trading.com](https://docs.mirai-trading.com)
- **GitHub Issues**: [https://github.com/your-org/mirai-agent/issues](https://github.com/your-org/mirai-agent/issues)
- **Discord Community**: [https://discord.gg/mirai-trading](https://discord.gg/mirai-trading)
- **Email Support**: support@mirai-trading.com

---

**Last Updated**: January 15, 2024  
**API Version**: 1.0.0  
**Documentation Version**: 1.0.0