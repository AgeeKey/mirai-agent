# Mirai Trading System - Developer Experience Guide

## Overview

This guide provides comprehensive information for developers working with the Mirai Trading System, including setup, development workflows, testing strategies, and best practices.

## Table of Contents

1. [Quick Setup](#quick-setup)
2. [Development Environment](#development-environment)
3. [Project Structure](#project-structure)
4. [Development Workflows](#development-workflows)
5. [Testing Guide](#testing-guide)
6. [Debugging & Troubleshooting](#debugging--troubleshooting)
7. [Performance Optimization](#performance-optimization)
8. [Security Guidelines](#security-guidelines)
9. [Deployment Strategies](#deployment-strategies)
10. [Monitoring & Observability](#monitoring--observability)
11. [Contributing Guidelines](#contributing-guidelines)

## Quick Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- Docker & Docker Compose
- Git

### One-Command Setup

```bash
# Clone and setup everything
git clone https://github.com/your-org/mirai-agent.git
cd mirai-agent
make setup-dev
```

This will:
- Install all dependencies
- Setup pre-commit hooks
- Create development environment
- Start development databases
- Run initial tests

### Manual Setup

```bash
# Clone repository
git clone https://github.com/your-org/mirai-agent.git
cd mirai-agent

# Setup Python environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"

# Setup pre-commit hooks
pre-commit install

# Start development services
docker-compose -f docker-compose.yml up -d redis postgres

# Run tests to verify setup
pytest
```

## Development Environment

### IDE Configuration

#### VS Code (Recommended)

Install the following extensions:
- Python
- TypeScript and JavaScript
- Docker
- GitLens
- REST Client
- Thunder Client

Copy the provided `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "120"],
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true,
  "editor.rulers": [120],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/node_modules": true,
    "**/dist": true
  }
}
```

#### PyCharm Configuration

1. Set Python interpreter to `./venv/bin/python`
2. Configure code style: Black with 120 character line length
3. Enable pytest as default test runner
4. Set up run configurations for each service

### Environment Variables

Create `.env` file in project root:

```bash
# API Configuration
MIRAI_API_URL=http://localhost:8001
MIRAI_API_KEY=dev_api_key

# Database Configuration
DATABASE_URL=postgresql://mirai:password@localhost:5432/mirai_dev
REDIS_URL=redis://localhost:6379/0

# Trading Configuration
BINANCE_API_KEY=your_testnet_api_key
BINANCE_SECRET_KEY=your_testnet_secret_key
BINANCE_TESTNET=true

# Development Flags
DEBUG=true
DRY_RUN=true
LOG_LEVEL=DEBUG

# Security
SECRET_KEY=your-super-secret-development-key
JWT_SECRET=your-jwt-secret-key

# External Services
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
```

### Development Scripts

We provide convenient development scripts:

```bash
# Start all services for development
./scripts/dev-start.sh

# Run specific service in development mode
./scripts/dev-api.sh        # Start API server
./scripts/dev-trader.sh     # Start trading engine
./scripts/dev-web.sh        # Start web dashboard

# Database operations
./scripts/db-reset.sh       # Reset development database
./scripts/db-migrate.sh     # Run database migrations
./scripts/db-seed.sh        # Seed with test data

# Testing utilities
./scripts/test-all.sh       # Run all tests
./scripts/test-integration.sh  # Run integration tests
./scripts/test-load.sh      # Run load tests

# Code quality
./scripts/lint.sh           # Run linting
./scripts/format.sh         # Format all code
./scripts/security-scan.sh  # Run security checks
```

## Project Structure

```
mirai-agent/
├── app/                    # Main application code
│   ├── api/               # FastAPI backend service
│   │   ├── mirai_api/     # API implementation
│   │   ├── tests/         # API tests
│   │   └── pyproject.toml # API dependencies
│   ├── trader/            # Trading engine
│   │   ├── tests/         # Trading tests
│   │   └── *.py          # Trading logic
│   ├── agent/             # AI decision engine
│   ├── telegram_bot/      # Telegram notifications
│   ├── security/          # Security framework
│   └── performance/       # Performance optimization
├── web/                   # Frontend applications
│   └── services/         # Next.js dashboard
├── sdk/                   # Client SDKs
│   ├── python/           # Python SDK
│   └── javascript/       # JavaScript/TypeScript SDK
├── docs/                  # Documentation
├── tests/                 # Integration tests
├── scripts/              # Development scripts
├── configs/              # Configuration files
├── infra/                # Infrastructure code
├── .github/              # GitHub workflows
└── docker-compose.yml    # Development environment
```

### Key Directories Explained

- **`app/`**: Contains all microservices and core business logic
- **`web/`**: Frontend applications and user interfaces
- **`sdk/`**: Client libraries for external developers
- **`tests/`**: Cross-service integration and end-to-end tests
- **`scripts/`**: Automation scripts for development and deployment
- **`configs/`**: Configuration files for various environments
- **`infra/`**: Docker files, Kubernetes manifests, monitoring configs

## Development Workflows

### Feature Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Development Cycle**
   ```bash
   # Make changes
   # Run tests frequently
   pytest app/api/tests/
   
   # Lint and format
   ./scripts/format.sh
   
   # Run integration tests
   ./scripts/test-integration.sh
   ```

3. **Pre-commit Checks**
   ```bash
   # Automatic via pre-commit hooks:
   # - Code formatting (black, isort)
   # - Linting (flake8, mypy)
   # - Security checks (bandit)
   # - Test validation
   ```

4. **Pull Request**
   ```bash
   git push origin feature/your-feature-name
   # Create PR via GitHub interface
   # Ensure all CI checks pass
   ```

### Service Development

#### API Development

```bash
# Start API in development mode
cd app/api
uvicorn mirai_api.main:app --reload --host 0.0.0.0 --port 8001

# Or using the development script
./scripts/dev-api.sh

# Test API endpoints
curl http://localhost:8001/api/health
curl http://localhost:8001/docs  # Interactive API docs
```

#### Trading Engine Development

```bash
# Start trader in development mode
cd app/trader
python -m mirai_trader.main --dry-run --debug

# Or using the development script
./scripts/dev-trader.sh

# Monitor trading logs
tail -f logs/trader.log
```

#### Frontend Development

```bash
# Start web dashboard
cd web/services
npm run dev

# Or using the development script
./scripts/dev-web.sh

# Access dashboard at http://localhost:3000
```

### Hot Reloading

All services support hot reloading in development:

- **API**: FastAPI auto-reloads on code changes
- **Trader**: File watcher restarts on changes
- **Web**: Next.js hot module replacement
- **Tests**: pytest-watch for continuous testing

```bash
# Continuous testing
ptw app/api/tests/ --runner "pytest -v"

# Continuous linting
watch -n 2 flake8 app/
```

## Testing Guide

### Test Structure

```
tests/
├── unit/              # Unit tests for individual modules
├── integration/       # Integration tests across services
├── e2e/              # End-to-end tests
├── load/             # Performance and load tests
├── fixtures/         # Test data and fixtures
└── conftest.py       # Pytest configuration
```

### Running Tests

```bash
# All tests
pytest

# Specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Service-specific tests
pytest app/api/tests/
pytest app/trader/tests/

# With coverage
pytest --cov=app --cov-report=html

# Load tests
pytest tests/load/ -v

# Parallel execution
pytest -n auto
```

### Test Configuration

Create `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests app
python_files = test_*.py *_test.py
python_functions = test_*
python_classes = Test*
addopts = 
    -v
    --strict-markers
    --disable-warnings
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    load: Load tests
    slow: Slow tests
    asyncio: Async tests
```

### Writing Tests

#### Unit Test Example

```python
# tests/unit/test_trader.py
import pytest
from decimal import Decimal
from app.trader.risk_engine import RiskEngine

class TestRiskEngine:
    def setup_method(self):
        self.risk_engine = RiskEngine({
            'max_position_size': 0.1,
            'max_daily_loss': 1000
        })
    
    def test_position_size_validation(self):
        # Test valid position size
        assert self.risk_engine.validate_position_size(
            Decimal('0.05')
        ) == True
        
        # Test invalid position size
        assert self.risk_engine.validate_position_size(
            Decimal('0.15')
        ) == False
    
    @pytest.mark.parametrize("size,expected", [
        (Decimal('0.01'), True),
        (Decimal('0.1'), True),
        (Decimal('0.11'), False),
    ])
    def test_position_size_limits(self, size, expected):
        assert self.risk_engine.validate_position_size(size) == expected
```

#### Integration Test Example

```python
# tests/integration/test_api_trader.py
import pytest
import asyncio
from app.api.main import app
from app.trader.client import TradingClient
from fastapi.testclient import TestClient

@pytest.mark.integration
@pytest.mark.asyncio
class TestAPITraderIntegration:
    def setup_method(self):
        self.api_client = TestClient(app)
        self.trader_client = TradingClient(testnet=True)
    
    async def test_place_order_flow(self):
        # Place order via API
        response = self.api_client.post("/api/trading/order", json={
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
            "quantity": 0.001
        })
        
        assert response.status_code == 200
        order_data = response.json()
        
        # Verify order appears in trader
        await asyncio.sleep(1)  # Allow processing
        
        positions = await self.trader_client.get_positions()
        assert any(p['symbol'] == 'BTCUSDT' for p in positions)
```

### Test Data Management

Use factories for consistent test data:

```python
# tests/factories.py
import factory
from datetime import datetime
from app.trader.models import Trade

class TradeFactory(factory.Factory):
    class Meta:
        model = Trade
    
    symbol = "BTCUSDT"
    side = "BUY"
    quantity = factory.Faker('pydecimal', left_digits=1, right_digits=3, positive=True)
    price = factory.Faker('pydecimal', left_digits=5, right_digits=2, positive=True)
    timestamp = factory.LazyFunction(datetime.now)
    strategy = "test_strategy"

# Usage in tests
def test_trade_processing():
    trade = TradeFactory()
    # Test with consistent, realistic data
```

## Debugging & Troubleshooting

### Logging Configuration

```python
# configs/logging.yaml
version: 1
disable_existing_loggers: false

formatters:
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
  simple:
    format: '%(levelname)s - %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: DEBUG
    formatter: detailed
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: detailed
    filename: logs/mirai.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

loggers:
  mirai_api:
    level: DEBUG
    handlers: [console, file]
    propagate: false
  
  mirai_trader:
    level: DEBUG
    handlers: [console, file]
    propagate: false

root:
  level: INFO
  handlers: [console]
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Environment variable
export DEBUG=true
export LOG_LEVEL=DEBUG

# Command line
python -m mirai_trader.main --debug --dry-run

# In code
import logging
logging.getLogger('mirai_trader').setLevel(logging.DEBUG)
```

### Common Issues & Solutions

#### Connection Issues

```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs api
docker-compose logs trader

# Test connectivity
curl http://localhost:8001/api/health
ping redis
```

#### Database Issues

```bash
# Reset database
./scripts/db-reset.sh

# Check database connection
python -c "
import sqlite3
conn = sqlite3.connect('state/mirai.db')
print('Database connected successfully')
conn.close()
"

# Manual database inspection
sqlite3 state/mirai.db
.tables
.schema trades
SELECT * FROM trades LIMIT 5;
```

#### Performance Issues

```bash
# Profile API performance
python -m cProfile -o profile.stats app/api/main.py

# Monitor resource usage
htop
docker stats

# Check performance metrics
curl http://localhost:8001/api/performance/summary
```

### Debugging Tools

#### Interactive Debugging

```python
# Add breakpoints in code
import pdb; pdb.set_trace()

# Or use ipdb for better experience
import ipdb; ipdb.set_trace()

# Remote debugging with VS Code
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

#### API Debugging

```bash
# Test API endpoints
curl -X GET http://localhost:8001/api/trading/status | jq

# Monitor API logs
tail -f logs/api.log | grep ERROR

# Interactive API testing
http --json POST localhost:8001/api/trading/order \
    symbol=BTCUSDT side=BUY type=MARKET quantity:=0.001
```

#### WebSocket Debugging

```javascript
// Browser console
const ws = new WebSocket('ws://localhost:8001/ws');
ws.onmessage = event => console.log(JSON.parse(event.data));
ws.send(JSON.stringify({type: 'subscribe', channel: 'trades'}));
```

## Performance Optimization

### Profiling

```python
# Profile specific functions
from cProfile import Profile
from app.trader.engine import TradingEngine

profiler = Profile()
profiler.enable()

# Your code here
engine = TradingEngine()
engine.process_signals()

profiler.disable()
profiler.dump_stats('profile.stats')

# Analyze results
python -m pstats profile.stats
```

### Memory Optimization

```python
# Monitor memory usage
import tracemalloc
import psutil

tracemalloc.start()

# Your code here

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")

# Process memory
process = psutil.Process()
memory_info = process.memory_info()
print(f"RSS: {memory_info.rss / 1024 / 1024:.1f} MB")
```

### Database Optimization

```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM trades WHERE symbol = 'BTCUSDT';

-- Add indexes for frequent queries
CREATE INDEX idx_trades_symbol_timestamp ON trades(symbol, timestamp);
CREATE INDEX idx_trades_strategy ON trades(strategy);

-- Optimize with connection pooling
-- See app/performance/optimization.py
```

### Caching Strategies

```python
# Redis caching example
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiry=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try cache first
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            redis_client.setex(
                cache_key, 
                expiry, 
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator

# Usage
@cache_result(expiry=60)
def get_market_data(symbol):
    # Expensive API call
    return fetch_from_binance(symbol)
```

## Security Guidelines

### API Security

```python
# Input validation
from pydantic import BaseModel, validator

class OrderRequest(BaseModel):
    symbol: str
    side: str
    quantity: float
    
    @validator('symbol')
    def validate_symbol(cls, v):
        allowed_symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        if v not in allowed_symbols:
            raise ValueError('Invalid symbol')
        return v
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0 or v > 1.0:
            raise ValueError('Invalid quantity')
        return v
```

### Secrets Management

```python
# Use environment variables
import os
from cryptography.fernet import Fernet

# Load encryption key from environment
encryption_key = os.environ.get('ENCRYPTION_KEY')
cipher_suite = Fernet(encryption_key)

# Encrypt sensitive data
def encrypt_api_key(api_key):
    return cipher_suite.encrypt(api_key.encode())

def decrypt_api_key(encrypted_key):
    return cipher_suite.decrypt(encrypted_key).decode()
```

### Rate Limiting

```python
# Implement rate limiting
from fastapi import HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/trading/order")
@limiter.limit("10/minute")
async def place_order(request: Request, order: OrderRequest):
    # Order placement logic
    pass
```

## Monitoring & Observability

### Health Checks

```python
# Comprehensive health check
@app.get("/healthz")
async def health_check():
    checks = {
        'database': check_database_health(),
        'redis': check_redis_health(),
        'binance_api': check_binance_health(),
        'disk_space': check_disk_space(),
        'memory': check_memory_usage()
    }
    
    healthy = all(checks.values())
    status_code = 200 if healthy else 503
    
    return JSONResponse(
        content={
            'status': 'healthy' if healthy else 'unhealthy',
            'checks': checks,
            'timestamp': datetime.now().isoformat()
        },
        status_code=status_code
    )
```

### Metrics Collection

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
trade_counter = Counter('trades_total', 'Total trades', ['symbol', 'side'])
order_latency = Histogram('order_latency_seconds', 'Order execution latency')
active_positions = Gauge('active_positions', 'Number of active positions')

# Use in code
@order_latency.time()
def place_order(order):
    # Order logic
    trade_counter.labels(symbol=order.symbol, side=order.side).inc()
    return result
```

### Logging Best Practices

```python
import logging
import structlog

# Structured logging
logger = structlog.get_logger(__name__)

def process_trade(trade):
    logger.info(
        "Processing trade",
        trade_id=trade.id,
        symbol=trade.symbol,
        quantity=float(trade.quantity),
        price=float(trade.price),
        strategy=trade.strategy
    )
    
    try:
        result = execute_trade(trade)
        logger.info(
            "Trade executed successfully",
            trade_id=trade.id,
            order_id=result.order_id,
            execution_time=result.execution_time
        )
    except Exception as e:
        logger.error(
            "Trade execution failed",
            trade_id=trade.id,
            error=str(e),
            exc_info=True
        )
        raise
```

## Contributing Guidelines

### Code Style

We use automated code formatting and linting:

```bash
# Format code
black app/ tests/ --line-length 120
isort app/ tests/

# Lint code
flake8 app/ tests/
mypy app/

# Security check
bandit -r app/
```

### Commit Messages

Follow conventional commit format:

```
feat(api): add portfolio performance endpoint
fix(trader): resolve order execution race condition
docs(sdk): update Python SDK examples
test(integration): add WebSocket connection tests
```

### Pull Request Process

1. **Create descriptive PR title and description**
2. **Ensure all tests pass**
3. **Add tests for new functionality**
4. **Update documentation if needed**
5. **Request review from appropriate team members**
6. **Address review feedback**
7. **Squash commits before merging**

### Code Review Checklist

- [ ] Code follows project conventions
- [ ] Tests are comprehensive and pass
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance impact considered
- [ ] Error handling is appropriate
- [ ] Logging is adequate

## IDE Extensions & Tools

### Recommended Tools

- **HTTPie**: Command-line HTTP client
- **jq**: JSON processor for API responses
- **pgcli**: Better PostgreSQL CLI
- **redis-cli**: Redis command-line interface
- **htop**: Process monitor
- **docker-compose**: Container orchestration

### Useful Commands

```bash
# API testing
http GET localhost:8001/api/trading/status | jq '.daily_pnl'

# Database queries
echo "SELECT COUNT(*) FROM trades;" | sqlite3 state/mirai.db

# Real-time log monitoring
tail -f logs/trader.log | grep ERROR

# Performance monitoring
watch -n 1 'docker stats --no-stream'

# Git shortcuts
git log --oneline --graph --decorate --all
git blame app/trader/engine.py | head -20
```

This developer experience guide should help both new and experienced developers get productive quickly with the Mirai Trading System. The combination of automated tooling, comprehensive documentation, and clear workflows creates an efficient development environment.