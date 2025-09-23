# Mirai Agent Monorepo

🤖 **Autonomous Trading Agent** с AI-анализом рынка и автоматическим трейдингом.

## 📦 Структура

- **`app/api/`** - FastAPI backend (REST API, админка, мониторинг)
- **`app/trader/`** - Trading Engine (Binance, стратегии, риск-менеджмент)  
- **`web/services/`** - Next.js frontend (веб-интерфейс, дашборд)

## 🚀 Quick Start

```bash
# Клонируем репозиторий
git clone https://github.com/AgeeKey/mirai-agent.git
cd mirai-agent

# Запускаем все сервисы
docker compose up -d

# Проверяем статус
curl http://localhost:8000/healthz  # API
open http://localhost:3000          # Web UI
```

## 🔧 Development

```bash
# API Development
cd app/api
pip install -e .
uvicorn mirai_api.main:app --reload

# Trader Development  
cd app/trader
pip install -e .
python -m mirai_trader.main

# Services Development
cd web/services
npm install
npm run dev
```

## 📖 Documentation

- **[🚀 Deployment Guide](README_Deploy.md)** - CI/CD, деплой, мониторинг
- **[🐳 Docker Guide](docs/DOCKER.md)** - контейнеризация
- **[🔒 Security Guide](docs/SECURITY.md)** - безопасность

## 🔄 CI/CD

GitHub Actions автоматически:
- ✅ Прогоняет тесты и линтеры для каждого пакета
- ✅ Собирает Docker образы при создании тега
- ✅ Деплоит на production сервер
- ✅ Проверяет health endpoints

**Workflow:** `git tag v1.2.3` → Auto-deploy → Health check

## 🌐 Production

- **Web UI:** https://aimirai.info
- **API:** https://aimirai.online/docs  
- **Health:** https://aimirai.online/healthz

## 📊 Status

- **API:** FastAPI + SQLite + JWT auth ✅
- **Trader:** Binance integration + risk engine ✅  
- **Frontend:** Next.js + TailwindCSS ✅
- **CI/CD:** GitHub Actions + GHCR ✅
- **Deployment:** Docker Compose + VPS ✅