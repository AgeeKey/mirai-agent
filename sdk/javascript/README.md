# Mirai Trading SDK for JavaScript/TypeScript

Official JavaScript/TypeScript SDK for the Mirai Trading System - an autonomous cryptocurrency trading platform with AI-powered decision making.

## Features

- **Complete API Coverage**: Access all Mirai Trading API endpoints
- **Real-time Data**: WebSocket support for live trading updates  
- **TypeScript Support**: Full type definitions included
- **Modern JavaScript**: ES6+ with async/await support
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Retry Logic**: Automatic retry with exponential backoff
- **Rate Limiting**: Built-in rate limit handling
- **Node.js & Browser**: Works in both environments

## Installation

```bash
npm install @mirai/trading-sdk
```

Or with yarn:
```bash
yarn add @mirai/trading-sdk
```

## Quick Start

### Basic Usage

```javascript
import { MiraiClient } from '@mirai/trading-sdk';

async function main() {
  const client = new MiraiClient({
    apiUrl: 'http://localhost:8001'
  });

  try {
    // Check API health
    const health = await client.getHealth();
    console.log(`API Status: ${health.status}`);

    // Get trading status
    const status = await client.getTradingStatus();
    console.log(`Daily P&L: $${status.daily_pnl}`);
    console.log(`Win Rate: ${status.win_rate}%`);

    // Get AI signals
    const { signals } = await client.getAISignals();
    signals.forEach(signal => {
      console.log(`${signal.symbol}: ${signal.direction} (strength: ${signal.strength.toFixed(2)})`);
    });
  } catch (error) {
    console.error('Error:', error.message);
  }
}

main();
```

### TypeScript Usage

```typescript
import { MiraiClient, MiraiConfig, TradingStatus, AISignal } from '@mirai/trading-sdk';

const config: MiraiConfig = {
  apiUrl: 'https://api.mirai-trading.com',
  apiKey: 'your_api_key_here',
  timeout: 30000
};

const client = new MiraiClient(config);

// Type-safe API calls
const status: TradingStatus = await client.getTradingStatus();
const signals: { signals: AISignal[] } = await client.getAISignals();
```

### Authentication

For production environments:

```javascript
const client = new MiraiClient({
  apiUrl: 'https://api.mirai-trading.com',
  apiKey: process.env.MIRAI_API_KEY,
  timeout: 30000
});
```

## Trading Operations

### Placing Orders

```javascript
// Market order
const marketOrder = await client.placeMarketOrder({
  symbol: 'BTCUSDT',
  side: 'BUY',
  quantity: 0.001,
  stopLoss: 50000.0,
  takeProfit: 60000.0
});

console.log(`Market order placed: ${marketOrder.order_id}`);

// Limit order
const limitOrder = await client.placeLimitOrder({
  symbol: 'ETHUSDT',
  side: 'SELL',
  quantity: 0.1,
  price: 3500.0
});

console.log(`Limit order placed: ${limitOrder.order_id}`);

// Custom order
const customOrder = await client.placeOrder({
  symbol: 'BTCUSDT',
  side: 'BUY',
  type: 'LIMIT',
  quantity: 0.001,
  price: 58000.0,
  stop_loss: 57000.0,
  take_profit: 60000.0
});
```

### Getting Market Data

```javascript
// Get current positions
const { positions } = await client.getPositions();
positions.forEach(position => {
  console.log(`${position.symbol}: ${position.side} ${position.size}`);
});

// Get recent trades
const { trades } = await client.getRecentTrades({ 
  limit: 10, 
  symbol: 'BTCUSDT' 
});

trades.forEach(trade => {
  console.log(`${trade.timestamp}: ${trade.action} ${trade.quantity} ${trade.symbol} @ $${trade.price}`);
});

// Get AI analysis
const analysis = await client.getAIAnalysis('BTCUSDT');
console.log(`Trend: ${analysis.analysis.trend}`);
console.log(`Recommendation: ${analysis.analysis.recommendation}`);
```

## Real-time Data Streaming

### WebSocket Connection

```javascript
// Connect to WebSocket
await client.connectWebSocket();

// Subscribe to trade updates
client.subscribeTrades(data => {
  console.log(`Trade: ${data.symbol} ${data.side} ${data.quantity}`);
});

// Subscribe to price updates
client.subscribePrices(data => {
  console.log(`Price: ${data.symbol} = $${data.price}`);
});

// Subscribe to AI signals
client.subscribeSignals(data => {
  console.log(`Signal: ${data.symbol} ${data.direction} (strength: ${data.strength.toFixed(2)})`);
});

// Keep connection alive
process.on('SIGINT', () => {
  client.disconnectWebSocket();
  process.exit();
});
```

### Event Handling

```javascript
import { MiraiClient } from '@mirai/trading-sdk';

class TradingBot {
  constructor() {
    this.client = new MiraiClient();
    this.setupEventHandlers();
  }

  setupEventHandlers() {
    this.client.subscribeTrades(this.onTrade.bind(this));
    this.client.subscribeSignals(this.onSignal.bind(this));
  }

  onTrade(tradeData) {
    if (tradeData.pnl > 0) {
      console.log(`Profitable trade: +$${tradeData.pnl}`);
    }
  }

  async onSignal(signalData) {
    if (signalData.strength > 0.8) {
      await this.executeSignal(signalData);
    }
  }

  async executeSignal(signal) {
    try {
      if (signal.direction === 'BUY') {
        const result = await this.client.placeMarketOrder({
          symbol: signal.symbol,
          side: 'BUY',
          quantity: 0.001
        });
        console.log(`Executed buy order: ${result.order_id}`);
      }
    } catch (error) {
      console.error(`Failed to execute signal: ${error.message}`);
    }
  }

  async start() {
    await this.client.connectWebSocket();
    console.log('Trading bot started');
  }

  stop() {
    this.client.disconnectWebSocket();
    console.log('Trading bot stopped');
  }
}

// Usage
const bot = new TradingBot();
bot.start();
```

## Error Handling

```javascript
import { 
  MiraiAPIError, 
  MiraiRateLimitError, 
  MiraiConnectionError 
} from '@mirai/trading-sdk';

try {
  const status = await client.getTradingStatus();
} catch (error) {
  if (error instanceof MiraiRateLimitError) {
    console.log('Rate limited - please wait');
    await new Promise(resolve => setTimeout(resolve, 60000));
  } else if (error instanceof MiraiAPIError) {
    console.log(`API Error: ${error.errorCode} - ${error.message}`);
  } else if (error instanceof MiraiConnectionError) {
    console.log(`Connection failed: ${error.message}`);
  } else {
    console.log(`Unexpected error: ${error.message}`);
  }
}
```

## Advanced Usage

### Configuration Options

```javascript
const client = new MiraiClient({
  apiUrl: 'http://localhost:8001',     // API base URL
  apiKey: 'your_api_key',              // API key for authentication
  timeout: 30000,                      // Request timeout in milliseconds
  maxRetries: 3,                       // Maximum retry attempts
  retryDelay: 1000,                    // Initial retry delay in milliseconds
  enableLogging: true                  // Enable SDK logging
});
```

### Batch Operations

```javascript
// Execute multiple operations concurrently
const [status, trades, signals, positions] = await Promise.all([
  client.getTradingStatus(),
  client.getRecentTrades({ limit: 5 }),
  client.getAISignals(),
  client.getPositions()
]);

console.log(`Status: ${status.daily_pnl}`);
console.log(`Recent trades: ${trades.trades.length}`);
console.log(`Active signals: ${signals.signals.length}`);
console.log(`Open positions: ${positions.positions.length}`);
```

### Performance Monitoring

```javascript
// Get performance summary
const perfSummary = await client.getPerformanceSummary();
console.log(`Cache hit rate: ${(perfSummary.data.cache_performance.hit_rate * 100).toFixed(1)}%`);

// Get cache statistics
const cacheStats = await client.getCacheStats();
console.log(`Cache requests: ${cacheStats.cache_stats.total_requests}`);

// Invalidate cache
await client.invalidateCache('market_data');
```

### Custom HTTP Client

For advanced use cases, you can extend the client:

```javascript
class CustomMiraiClient extends MiraiClient {
  constructor(config) {
    super(config);
    
    // Add custom request interceptor
    this.httpClient.interceptors.request.use(config => {
      config.headers['X-Custom-Header'] = 'custom-value';
      return config;
    });
  }

  async customMethod() {
    // Add custom functionality
    const response = await this.httpClient.get('/custom/endpoint');
    return response.data;
  }
}
```

## Browser Usage

The SDK works in browsers with proper bundling:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Mirai Trading Dashboard</title>
</head>
<body>
    <div id="status"></div>
    <div id="trades"></div>

    <script type="module">
        import { MiraiClient } from './node_modules/@mirai/trading-sdk/dist/index.esm.js';

        const client = new MiraiClient({
            apiUrl: 'http://localhost:8001'
        });

        async function updateDashboard() {
            try {
                const status = await client.getTradingStatus();
                document.getElementById('status').innerHTML = 
                    `Daily P&L: $${status.daily_pnl} | Win Rate: ${status.win_rate}%`;

                const { trades } = await client.getRecentTrades({ limit: 5 });
                const tradesHTML = trades.map(trade => 
                    `<div>${trade.symbol} ${trade.action} ${trade.quantity} @ $${trade.price}</div>`
                ).join('');
                document.getElementById('trades').innerHTML = tradesHTML;
            } catch (error) {
                console.error('Dashboard update failed:', error);
            }
        }

        // Update every 30 seconds
        updateDashboard();
        setInterval(updateDashboard, 30000);

        // Setup WebSocket for real-time updates
        await client.connectWebSocket();
        client.subscribeTrades(trade => {
            console.log('New trade:', trade);
            updateDashboard(); // Refresh dashboard
        });
    </script>
</body>
</html>
```

## API Reference

### Client Methods

#### Health & Status
- `getHealth()`: Get API health status
- `getTradingStatus()`: Get current trading status

#### Market Data
- `getPerformanceData()`: Get performance data over time
- `getRecentTrades(options?)`: Get recent trades
- `getPositions()`: Get current positions

#### Orders
- `placeOrder(order)`: Place a custom order
- `placeMarketOrder(params)`: Place a market order
- `placeLimitOrder(params)`: Place a limit order
- `waitForOrder(orderId, timeout?)`: Wait for order completion

#### AI & Analysis
- `getAISignals()`: Get current AI trading signals
- `getAIAnalysis(symbol)`: Get detailed AI analysis

#### Monitoring
- `getMetrics()`: Get Prometheus metrics
- `getAlerts()`: Get active alerts

#### Performance
- `getPerformanceSummary()`: Get performance optimization summary
- `getCacheStats()`: Get cache statistics
- `invalidateCache(pattern)`: Invalidate cache entries

#### WebSocket
- `connectWebSocket()`: Connect to WebSocket
- `disconnectWebSocket()`: Disconnect from WebSocket
- `subscribeTrades(callback)`: Subscribe to trade updates
- `subscribePrices(callback)`: Subscribe to price updates
- `subscribeSignals(callback)`: Subscribe to AI signals

### Type Definitions

The SDK includes comprehensive TypeScript definitions for all data structures:

- `MiraiConfig`: Client configuration options
- `TradingStatus`: Trading system status
- `Trade`: Individual trade data
- `Position`: Position information
- `AISignal`: AI trading signals
- `Order`: Order placement data
- `OrderResult`: Order execution results
- `Alert`: System alerts
- `PerformanceSummary`: Performance metrics

## Testing

```bash
# Install dependencies
npm install

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

## Building

```bash
# Build the SDK
npm run build

# Build in watch mode
npm run build:watch

# Type checking
npm run typecheck

# Linting
npm run lint
npm run lint:fix
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
- TypeScript definitions
- Comprehensive error handling
- Browser and Node.js compatibility