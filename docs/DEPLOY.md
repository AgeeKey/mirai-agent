# Mirai Agent Deployment Guide

## Overview
Mirai Agent is a comprehensive crypto trading bot with a web control panel, API, and Telegram notifications.

## Services Architecture

### Core Services
- **mirai-api** (Port 8000): FastAPI backend with JWT authentication
- **mirai-trader**: Core trading engine with risk management
- **mirai-services** (Port 3000): Next.js frontend control panel  
- **mirai-telegram**: Telegram bot for notifications and control

## Environment Variables

### Required Secrets (GitHub Secrets)
```bash
# API Authentication
WEB_USER=admin
WEB_PASS=secure_password_here
JWT_SECRET=random_jwt_secret_256_bits

# Binance API
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHAT_ID_ADMIN=your_telegram_chat_id

# OpenAI (Optional)
OPENAI_API_KEY=your_openai_api_key

# Domains
DOMAIN_PANEL=aimirai.online
DOMAIN_STUDIO=aimirai.info

# GitHub Container Registry
GHCR_TOKEN=your_github_token
GHCR_USERNAME=your_github_username
```

### Generated .env.production
The deployment workflow automatically generates `.env.production` with:
```bash
# === Common ===
ENVIRONMENT=production
OPENAI_API_KEY=${OPENAI_API_KEY}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_CHAT_ID_ADMIN=${TELEGRAM_CHAT_ID_ADMIN}

# === Web Panel / API ===
WEB_USER=${WEB_USER}
WEB_PASS=${WEB_PASS}
JWT_SECRET=${JWT_SECRET}
WEB_PORT=8000

# === Trader ===
BINANCE_API_KEY=${BINANCE_API_KEY}
BINANCE_API_SECRET=${BINANCE_API_SECRET}
DRY_RUN=true
USE_TESTNET=true

# === Services (Next.js) ===
NEXT_PUBLIC_SITE_URL=https://aimirai.info
NEXT_PUBLIC_API_BASE=https://aimirai.online
```

## Local Development

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker & Docker Compose

### Setup
```bash
# Clone repository
git clone https://github.com/AgeeKey/mirai-agent.git
cd mirai-agent

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
cd web/services
npm install
cd ../..

# Copy environment template
cp infra/env/.env.production.template .env.local
# Edit .env.local with your credentials
```

### Run Services Locally
```bash
# Start API
cd app/api && python -m mirai_api.main

# Start Next.js (separate terminal)
cd web/services && npm run dev

# Start Telegram Bot (separate terminal)
cd app && python telegram_bot/main.py
```

## Production Deployment

### Using GitHub Actions
1. Set up all required secrets in GitHub repository settings
2. Create a git tag to trigger deployment:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. Monitor deployment in GitHub Actions

### Manual Deployment
```bash
# On server, clone repository
git clone https://github.com/AgeeKey/mirai-agent.git
cd mirai-agent

# Create .env.production with your secrets
cp infra/env/.env.production.template .env.production
# Edit .env.production with actual values

# Deploy with Docker Compose
export GITHUB_OWNER=ageekey
export TAG=latest
docker compose -f infra/docker-compose.prod.yml pull
docker compose -f infra/docker-compose.prod.yml up -d
```

## Health Checks

### Service Status
```bash
# Check all services
docker ps

# Check specific service logs
docker logs mirai-api-1
docker logs mirai-services-1
docker logs mirai-telegram-1
```

### Web Endpoints
- API Health: `https://aimirai.online/healthz` (should return 200)
- API Docs: `https://aimirai.online/docs` (should show Swagger UI)
- Frontend: `https://aimirai.info` (should redirect to login)

### Telegram Bot
- Send `/start` to your bot
- Should receive welcome message with available commands

## Troubleshooting

### Common Issues

#### 1. Authentication Errors
- Check `WEB_USER`, `WEB_PASS`, and `JWT_SECRET` are set correctly
- Ensure JWT_SECRET is at least 32 characters

#### 2. Telegram Bot Not Responding
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Check `TELEGRAM_CHAT_ID_ADMIN` matches your chat ID
- Ensure bot container is running: `docker logs mirai-telegram-1`

#### 3. API Connection Errors
- Check if API container is healthy: `docker ps`
- Verify API is accessible: `curl https://aimirai.online/healthz`
- Check environment variables in Next.js container

#### 4. Trading Issues
- Ensure `DRY_RUN=true` for safety in production
- Use `USE_TESTNET=true` for testing
- Check `BINANCE_API_KEY` and `BINANCE_API_SECRET` are valid

### Log Locations
- API logs: `docker logs mirai-api-1`
- Trader logs: `docker logs mirai-trader-1`  
- Frontend logs: `docker logs mirai-services-1`
- Bot logs: `docker logs mirai-telegram-1`

### Resource Monitoring
All services have log rotation enabled (10MB max, 5 files) to prevent disk space issues.

## Security Considerations

- All services bind to `127.0.0.1` only (not exposed externally)
- JWT tokens expire after 12 hours
- Trading is in DRY_RUN mode by default
- Testnet is used by default for safety
- UFW firewall should be enabled with only ports 80/443 open
- SSH password authentication should be disabled

## Support

For issues or questions:
1. Check the logs first
2. Verify all environment variables are set correctly
3. Ensure all services are running (`docker ps`)
4. Test individual components (API health check, frontend loading, bot responding)