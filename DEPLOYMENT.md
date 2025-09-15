# 🚀 Mirai Agent - Deployment Guide

## Quick Start

### 1. Environment Setup
```bash
# Copy environment template
cp .env.template .env

# Edit environment variables (REQUIRED)
nano .env
```

### 2. Required Configuration
Before deployment, you MUST configure these critical settings in `.env`:

```bash
# Database passwords
POSTGRES_PASSWORD=your_secure_postgres_password_here
REDIS_PASSWORD=your_secure_redis_password_here

# Exchange API (Binance)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here

# Security keys
DASHBOARD_SECRET_KEY=your_secure_dashboard_secret_here
JWT_SECRET=your_jwt_secret_key_here
API_SECRET_KEY=your_secure_api_secret_here

# Admin credentials
ADMIN_PASSWORD=your_secure_admin_password_here
GRAFANA_ADMIN_PASSWORD=your_secure_grafana_password_here

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

### 3. Deploy Production Stack
```bash
# Build and start all services
docker-compose -f docker-compose.production.yml up -d

# Check services status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

### 4. Access Services

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| 📊 **Dashboard** | http://localhost:3000 | admin / [ADMIN_PASSWORD] |
| 📈 **Grafana** | http://localhost:3001 | admin / [GRAFANA_ADMIN_PASSWORD] |
| 🔥 **Prometheus** | http://localhost:9090 | - |
| 🚀 **API** | http://localhost:8000 | API Key required |

## 🛠️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        NGINX (Load Balancer)                │
│                     Rate Limiting & SSL                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
┌───▼────┐    ┌──────▼──────┐    ┌─────▼─────┐
│Dashboard│    │   API       │    │  Mirai    │
│(Next.js)│    │ (FastAPI)   │    │  Agent    │
└────────┘    └─────────────┘    └───────────┘
    │              │                   │
    └──────────────┼───────────────────┘
                   │
    ┌──────────────┼──────────────────────────────┐
    │              │                              │
┌───▼───┐    ┌────▼────┐    ┌─────────┐    ┌────▼────┐
│ Redis │    │PostgreSQL│    │Prometheus│    │ Grafana │
│(Cache)│    │(Database)│    │(Metrics) │    │(Charts) │
└───────┘    └─────────┘    └─────────┘    └─────────┘
```

## 🔧 Service Configuration

### Core Services

#### Mirai Agent (Trading Bot)
- **Purpose**: Main trading logic and decision engine
- **Dependencies**: PostgreSQL, Redis, Exchange API
- **Health Check**: `/health` endpoint
- **Logs**: `docker logs mirai-agent`

#### Mirai API
- **Purpose**: REST API for external integrations
- **Port**: 8000
- **Documentation**: http://localhost:8000/docs
- **Authentication**: API Key required

#### Dashboard
- **Purpose**: Web interface for monitoring and control
- **Port**: 3000
- **Technology**: Next.js, React, TypeScript
- **Features**: Real-time charts, portfolio overview, trade history

### Infrastructure Services

#### PostgreSQL
- **Purpose**: Primary database for trades, signals, performance
- **Port**: 5432
- **Schema**: Auto-initialized from `infra/sql/`
- **Backup**: Automated daily backups

#### Redis
- **Purpose**: Caching and real-time data
- **Port**: 6379
- **Usage**: Session storage, market data cache, job queue

#### Nginx
- **Purpose**: Reverse proxy and load balancer
- **Features**: Rate limiting, security headers, SSL termination
- **Config**: `infra/nginx/nginx.conf`

### Monitoring Stack

#### Prometheus
- **Purpose**: Metrics collection and alerting
- **Port**: 9090
- **Targets**: All services with `/metrics` endpoints
- **Retention**: 15 days

#### Grafana
- **Purpose**: Visualization and dashboards
- **Port**: 3001
- **Dashboards**: Pre-configured trading dashboards
- **Data Sources**: Prometheus, PostgreSQL

## 🔒 Security Features

### Authentication & Authorization
- JWT-based API authentication
- Role-based access control
- Session management with Redis

### Network Security
- Rate limiting (100 req/min per IP)
- CORS protection
- Security headers (HSTS, CSP, X-Frame-Options)
- Private Docker network

### Data Protection
- Encrypted environment variables
- Secure password storage
- API key rotation support

## 📊 Monitoring & Alerts

### Key Metrics
- Trading performance (PnL, win rate, Sharpe ratio)
- System health (CPU, memory, disk usage)
- API response times and error rates
- Exchange connectivity status

### Alerting
- Telegram notifications for trades and alerts
- Email alerts for critical system events
- Grafana alerting rules
- Custom webhook integrations

## 🚨 Troubleshooting

### Common Issues

#### Services won't start
```bash
# Check Docker status
docker-compose -f docker-compose.production.yml ps

# View specific service logs
docker-compose -f docker-compose.production.yml logs mirai-agent

# Restart specific service
docker-compose -f docker-compose.production.yml restart mirai-agent
```

#### Database connection errors
```bash
# Check PostgreSQL logs
docker-compose -f docker-compose.production.yml logs postgres

# Verify environment variables
docker-compose -f docker-compose.production.yml exec mirai-agent env | grep POSTGRES

# Test database connection
docker-compose -f docker-compose.production.yml exec postgres psql -U mirai_user -d mirai_agent -c "\dt"
```

#### API authentication issues
```bash
# Check API logs
docker-compose -f docker-compose.production.yml logs mirai-api

# Verify API key in environment
docker-compose -f docker-compose.production.yml exec mirai-api env | grep API_SECRET

# Test API endpoint
curl -H "X-API-Key: your_api_key" http://localhost:8000/health
```

### Performance Tuning

#### Database Optimization
```sql
-- Check slow queries
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

-- Optimize indexes
ANALYZE;
REINDEX DATABASE mirai_agent;
```

#### Redis Memory Management
```bash
# Check Redis memory usage
docker-compose -f docker-compose.production.yml exec redis redis-cli INFO memory

# Clear cache if needed
docker-compose -f docker-compose.production.yml exec redis redis-cli FLUSHDB
```

## 🔄 Maintenance

### Daily Tasks
- Monitor trading performance metrics
- Check system resource usage
- Review error logs and alerts
- Verify backup completion

### Weekly Tasks
- Update trading strategy parameters
- Review risk management settings
- Analyze portfolio performance
- Update security patches

### Monthly Tasks
- Rotate API keys and passwords
- Archive old log files
- Update exchange API rate limits
- Performance optimization review

## 📈 Scaling Guide

### Horizontal Scaling
```yaml
# Scale specific services
docker-compose -f docker-compose.production.yml up -d --scale mirai-agent=3
docker-compose -f docker-compose.production.yml up -d --scale mirai-api=2
```

### Load Balancing
- Nginx automatically load balances between service instances
- Configure additional upstream servers in `nginx.conf`
- Add health checks for new instances

### Database Scaling
- Read replicas for reporting queries
- Connection pooling optimization
- Partitioning for historical data

## 🆘 Support

### Log Locations
- Application logs: `logs/` directory
- Docker logs: `docker-compose logs`
- System logs: `/var/log/`

### Health Checks
- API: `GET /health`
- Agent: `GET /health`
- Database: `SELECT 1`
- Redis: `PING`

### Emergency Procedures
1. **Trading halt**: Set `EMERGENCY_STOP=true` in environment
2. **Service restart**: `docker-compose restart`
3. **Full rollback**: `docker-compose down && git checkout previous_version`
4. **Database restore**: Use automated backup files

---

## 🎯 Next Steps

1. ✅ Complete environment configuration
2. ✅ Deploy production stack
3. ✅ Configure monitoring dashboards
4. 🔄 Set up security scanning
5. 🔄 Configure automated backups
6. 🔄 Test emergency procedures

For additional support, check the logs or create an issue in the repository.