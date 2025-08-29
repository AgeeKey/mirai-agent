# Mirai Agent 🤖

[![CI/CD Pipeline](https://github.com/AgeeKey/mirai-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/AgeeKey/mirai-agent/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An advanced trading bot with AI-powered decision making for cryptocurrency futures trading on Binance.

## 🚀 Features

- **AI-Powered Trading**: Mock LLM integration for intelligent market analysis
- **Risk Management**: Comprehensive risk controls with position sizing and stop losses
- **Binance Integration**: Native support for Binance UMFutures with strict filters
- **DRY_RUN Mode**: Safe testing environment with simulated trading
- **CLI Interface**: Easy-to-use command line interface
- **Web Panel**: Real-time monitoring and control interface with BasicAuth
- **Telegram Bot**: Remote monitoring and control via Telegram
- **Monitoring**: Detailed logging and performance metrics

## 🏗️ Architecture

```
mirai-agent/
├── app/                    # Main application code
│   ├── cli.py             # Command line interface
│   ├── agent/             # AI agent components
│   │   ├── schema.py      # Pydantic schemas
│   │   ├── policy.py      # Trading policy and mock LLM
│   │   └── loop.py        # Main agent loop
│   ├── trader/            # Trading components
│   │   ├── binance_client.py   # Binance API client
│   │   ├── exchange_info.py    # Exchange filters
│   │   └── orders.py           # Order management
│   ├── telegram_bot/      # Telegram bot integration
│   └── web/              # Web panel interface
│       ├── api.py        # FastAPI REST endpoints
│       ├── ui.py         # HTML dashboard
│       └── utils.py      # Shared utilities
├── configs/               # Configuration files
│   ├── logging.yaml       # Logging configuration
│   ├── risk.yaml         # Risk management settings
│   └── strategies.yaml   # Trading strategies
├── infra/                # Infrastructure code
│   └── docker-compose.yml # Docker compose config
├── logs/                 # Log files
└── tests/               # Test suite
```

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/AgeeKey/mirai-agent.git
cd mirai-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment template:
```bash
cp .env.example .env
```

4. Configure your settings in `.env` (optional for dry-run mode)

## 🎯 Quick Start

### Dry Run Check
Test the system without making actual trades:
```bash
python app/cli.py dry-run-check
```

### Run Agent Once
Execute a single trading decision cycle:
```bash
python app/cli.py agent-once --symbol BTCUSDT
```

### Available Commands
- `dry-run-check`: Validate system configuration and connectivity
- `agent-once`: Run a single agent decision cycle

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Binance API (optional for dry-run)
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key

# Environment Settings
TESTNET=true
DRY_RUN=true

# Risk Management
MAX_POSITION_SIZE=1000
MAX_DRAWDOWN=0.05
```

### Risk Management (configs/risk.yaml)
Configure position sizing, stop losses, and portfolio limits.

### Trading Strategies (configs/strategies.yaml)
Define and configure trading strategies with parameters.

## 🧪 Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ -v --cov=app --cov-report=html
```

## 🔧 Development

### Code Quality
```bash
# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type checking (if mypy is installed)
mypy app/
```

### Project Structure
- **app/agent/**: AI decision making components
- **app/trader/**: Binance integration and order management
- **configs/**: YAML configuration files
- **tests/**: Comprehensive test suite

## 🚦 Safety Features

- **DRY_RUN Mode**: Default safe mode with simulated trading
- **Strict Filters**: Binance exchange filters for tickSize/stepSize/minQty
- **Risk Controls**: Position sizing and drawdown limits
- **Comprehensive Logging**: Detailed audit trail

## 📊 Monitoring

### Web Panel

Access the web dashboard for real-time monitoring and control:

```bash
# Start the web panel
python app/cli.py web-run

# Custom host/port
python app/cli.py web-run --host 0.0.0.0 --port 8080
```

**Features:**
- Real-time status monitoring with auto-refresh
- Trading mode control (Advisor/Semi/Auto)
- Pause/Resume functionality
- Emergency kill switch for positions
- BasicAuth protection
- API metrics and health monitoring

**Environment Variables:**
```bash
WEB_USER=admin          # Web panel username
WEB_PASS=change-me      # Web panel password
WEB_PORT=8000          # Server port
```

**Endpoints:**
- `GET /` - Dashboard UI (requires auth)
- `GET /status` - Agent status JSON
- `GET /metrics` - Performance metrics
- `POST /kill` - Emergency kill switch (requires auth)
- `POST /mode` - Change trading mode (requires auth)
- `POST /pause` - Pause agent (requires auth)
- `POST /resume` - Resume agent (requires auth)

### Docker Deployment

Run with Docker Compose:

```bash
# Build and start web panel
cd infra/
docker compose up -d web

# View logs
docker compose logs -f web
```

### Logs

Logs are stored in the `logs/` directory:
- `mirai-agent.log`: General application logs
- `mirai-agent-error.log`: Error-specific logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feat/new-feature`)
5. Create a Pull Request

## ⚠️ Disclaimer

This software is for educational and research purposes only. Trading cryptocurrencies involves significant risk. Always test thoroughly in dry-run mode before using real funds.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.