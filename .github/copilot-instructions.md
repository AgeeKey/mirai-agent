# Mirai Agent - AI Coding Assistant Instructions

## 🏗️ Architecture Overview

Mirai is an **autonomous trading agent monorepo** with microservices architecture:

- **`app/api/`** - FastAPI backend (REST API, WebSocket, admin panel)
- **`app/trader/`** - Trading engine (Binance integration, order management)
- **`app/agent/`** - AI decision engine (LLM policies, risk assessment)
- **`app/telegram_bot/`** - Notification service and manual controls
- **`web/services/`** - Next.js frontend dashboard
- **`microservices/`** - Standalone services (AI engine, analytics, notifications)

## 🔧 Development Patterns

### Multi-Package Structure
Each major component has its own `pyproject.toml` with independent dependencies:
```
app/api/pyproject.toml     # FastAPI, SQLite, JWT
app/trader/pyproject.toml  # Binance client, pandas
app/telegram_bot/         # python-telegram-bot
```

### Path Resolution Pattern
All modules use dynamic path resolution for CLI/import flexibility:
```python
# Standard pattern in all modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from ..trader.risk_engine import get_risk_engine  # Package import
except ImportError:
    from trader.risk_engine import get_risk_engine     # CLI import
```

### Configuration Management
- **YAML configs** in `configs/` (risk.yaml, strategies.yaml, logging.yaml)
- **Environment variables** for secrets (.env, docker compose)
- **Database state** in `state/mirai.db` (SQLite)

## 🚀 Development Workflows

### Local Development
```bash
# API development
cd app/api && uvicorn mirai_api.main:app --reload

# Trader testing (dry-run mode default)
cd app/trader && python -m mirai_trader.main

# Frontend development  
cd web/services && npm run dev

# Full stack
docker-compose up -d
```

### Testing Strategy
```bash
# Root-level unified testing
pytest  # Tests all packages via pyproject.toml paths

# Package-specific testing
cd app/api && pytest tests/
cd app/trader && pytest tests/
```

### Build & Release
```bash
# Release workflow (creates Docker images + GitHub release)
./scripts/create-release.sh 1.2.3

# Manual Docker builds
make docker-build  # Uses infra/docker-compose.yml
```

## 🎯 Trading Engine Specifics

### Risk Management Integration
The `AgentLoop` orchestrates decision-making with multiple safety layers:
- **Risk Engine**: Position sizing, stop-loss validation (`app/trader/risk_engine.py`)
- **AI Advisor**: Signal scoring with configurable thresholds (`app/agent/advisor.py`)
- **Policy Layer**: LLM-based decision policies (`app/agent/policy.py`)

### Dry-Run Mode Pattern
All trading components support dry-run testing:
```python
# Always check dry_run status
if self.dry_run:
    logger.info(f"DRY RUN: Would place order {order_data}")
    return {"status": "dry_run", "order_id": f"dry_{timestamp}"}
```

### State Persistence
- **Positions/Orders**: SQLite database in `state/mirai.db`
- **Logs**: Structured logging to `logs/` directory
- **Reports**: JSON advisor reports in `reports/`

## 🔌 Integration Points

### WebSocket Real-time Data
API serves live trading data via WebSocket (`/ws` endpoint) with connection manager pattern for frontend dashboard updates.

### Telegram Notifications
Bot integration allows remote monitoring and manual trading controls. Check `TELEGRAM_AVAILABLE` flag for graceful degradation.

### External APIs
- **Binance UMFutures**: Testnet and mainnet support via `binance-connector`
- **Redis**: Caching and pub/sub (production deployment)
- **PostgreSQL**: Production database (development uses SQLite)

## 📦 Docker & Deployment

### Multi-stage Builds
Each service uses optimized Dockerfiles with base image sharing:
- `Dockerfile.base` - Common Python dependencies
- Component-specific Dockerfiles for API/Trader/Web

### Production Stack
```yaml
# docker-compose.production.yml includes:
- PostgreSQL + Redis
- Nginx reverse proxy  
- Prometheus monitoring
- Multi-platform builds (amd64/arm64)
```

### Health Checks
All services implement `/healthz` endpoints for monitoring and deployment validation.

## 🧪 Testing & Quality

### Code Standards
- **Formatting**: `ruff format` + `black` (120 char line length)
- **Linting**: `ruff` + `mypy` with relaxed settings for AI development
- **Pre-commit**: Automated formatting and basic validation

### Test Organization
Tests follow pytest conventions with async support. Use `filterwarnings` for dependencies (Pydantic deprecation warnings ignored).

When editing this codebase, prioritize maintaining the risk management safeguards and dry-run capabilities that prevent accidental live trading.