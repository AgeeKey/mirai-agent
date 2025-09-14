# 🚀 Mirai Agent - Deployment Guide

## 📋 GitHub Actions Workflows

### Структура CI/CD

У нас есть **4 железных workflow**:

1. **`ci-api.yml`** - CI для FastAPI backend
2. **`ci-trader.yml`** - CI для Trading Engine
3. **`ci-services.yml`** - CI для Next.js frontend
4. **`build-and-deploy.yml`** - Сборка образов + деплой

---

## 🔧 Настройка Secrets

В `Settings → Secrets → Actions` должны быть настроены:

### 🐳 Docker & GitHub Container Registry
```
GHCR_TOKEN=ghp_xxxxxxxxxxxxx  # Personal Access Token с write:packages
```

### 🖥️ Server Access
```
SSH_HOST=your-server.com
SSH_USER=root
SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----
```

### 🌐 Domains
```
DOMAIN_STUDIO=aimirai.info      # Frontend domain
DOMAIN_PANEL=aimirai.online     # API domain
```

### 🔐 Application Secrets
```
JWT_SECRET=your-jwt-secret
WEB_USER=admin
WEB_PASS=your-secure-password
```

### 🤖 AI & Telegram
```
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID_ADMIN=-1001234567890
```

### 📈 Trading (Optional)
```
BINANCE_API_KEY=your-binance-key
BINANCE_API_SECRET=your-binance-secret
```

---

## 🚀 Деплой Process

### 1. Development Workflow

```bash
# 1. Создаем feature branch
git checkout -b feature/new-feature

# 2. Делаем изменения и коммитим
git add .
git commit -m "feat: add new feature"

# 3. Пушим и создаем PR
git push origin feature/new-feature
# Создаем Pull Request в GitHub

# 4. CI автоматически запускается:
# - ci-api.yml (если изменения в app/api/)
# - ci-trader.yml (если изменения в app/trader/)
# - ci-services.yml (если изменения в web/services/)
```

### 2. Release & Deploy

```bash
# 1. Merge PR в main
git checkout main
git pull origin main

# 2. Создаем release tag
git tag v1.2.3
git push origin v1.2.3

# 3. GitHub Actions автоматически:
# ✅ Собирает Docker образы с тегами v1.2.3 и latest
# ✅ Пушит в ghcr.io/ageekey/mirai-*
# ✅ Деплоит на сервер через SSH
# ✅ Проверяет health check endpoints
```

### 3. Manual Deploy

Если нужно задеплоить без создания релиза:

1. Идите в **Actions** → **Build & Deploy**
2. Нажмите **Run workflow**
3. Выберите `production` или `staging`
4. Нажмите **Run workflow**

---

## 🔍 Мониторинг & Health Checks

### Автоматические проверки в CI

После деплоя автоматически проверяются:

```bash
# API Health Check
curl -f https://aimirai.online/healthz

# Web UI Check  
curl -f https://aimirai.info

# API Documentation
curl -f https://aimirai.online/docs
```

### Ручная проверка

```bash
# Логи сервера
ssh root@your-server.com
cd /opt/mirai
docker compose -f docker-compose.prod.yml logs -f

# Статус контейнеров
docker compose -f docker-compose.prod.yml ps

# Проверка образов
docker images | grep ghcr.io/ageekey
```

---

## 🛠️ Troubleshooting

### 1. CI падает с ошибкой зависимостей

```bash
# Обновите pyproject.toml или package.json
# Проверьте что версии пинованы
pip freeze > requirements.txt  # для Python
npm ci  # для Node.js
```

### 2. Docker build падает

```bash
# Локальная проверка
docker build -t test-api app/api/
docker build -t test-trader app/trader/
docker build -t test-services web/services/

# Проверьте Dockerfile в каждом сервисе
```

### 3. GHCR push ошибка

```bash
# Проверьте GHCR_TOKEN
gh auth status

# Локальная проверка
echo "$GHCR_TOKEN" | docker login ghcr.io -u ageekey --password-stdin
docker push ghcr.io/ageekey/mirai-api:test
```

### 4. Деплой падает

```bash
# SSH на сервер
ssh root@your-server.com

# Проверьте логи
cd /opt/mirai
docker compose -f docker-compose.prod.yml logs

# Перезапуск сервисов
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

---

## 📊 Monitoring Commands

### Server Status

```bash
# CPU/Memory usage
top
htop

# Disk space
df -h

# Docker stats
docker stats

# Network connections
netstat -tulpn | grep :80
netstat -tulpn | grep :443
```

### Application Logs

```bash
# Real-time logs
docker compose -f docker-compose.prod.yml logs -f

# Specific service logs
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f trader
docker compose -f docker-compose.prod.yml logs -f services

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100
```

### Database Status

```bash
# SQLite file size
ls -lah /opt/mirai/state/mirai.db

# Recent agent activity
sqlite3 /opt/mirai/state/mirai.db "SELECT * FROM agent_actions ORDER BY timestamp DESC LIMIT 10;"
```

---

## ✅ Production Checklist

### Before Release

- [ ] All CI tests pass
- [ ] Docker builds successfully locally
- [ ] All secrets configured in GitHub
- [ ] Server has enough disk space
- [ ] Backup current database

### After Release

- [ ] API responds at https://aimirai.online/healthz
- [ ] Web UI loads at https://aimirai.info
- [ ] API docs available at https://aimirai.online/docs
- [ ] Telegram bot responds
- [ ] Trading engine connects to Binance (if configured)
- [ ] No errors in docker logs

### Weekly Maintenance

- [ ] Check disk space: `df -h`
- [ ] Clean old Docker images: `docker system prune -af`
- [ ] Review application logs for errors
- [ ] Backup database: `cp /opt/mirai/state/mirai.db backup/`
- [ ] Update dependencies if needed

---

## 🎯 Summary

**Железное правило деплоя:**

1. **Develop** → PR → CI passes → Merge to main
2. **Release** → Create tag `vX.Y.Z` → Auto-deploy
3. **Verify** → Check health endpoints → Monitor logs
4. **Maintain** → Weekly cleanup → Backup data

Эта система гарантирует **стабильную работу CI/CD** без сюрпризов! 🔒

---

## 🤖 Bootstrap AI access

Этот шаг даёт Codex (Codespaces/Actions) полный доступ к GitHub, GHCR, серверу и интеграциям.

### 🔑 Secrets

Задай в Repo → Settings → Secrets and variables (и в Codespaces, и в Actions):

Обязательные

- `GH_TOKEN` (scopes: `repo`, `workflow`, `write:packages`)
- `SSH_HOST` (IP/домен сервера)
- `SSH_USER` (имя пользователя, напр. root или deploy)
- `SSH_KEY` (многострочный приватный ключ) ИЛИ `SSH_KEY_B64` (тот же ключ в base64)

Опциональные

- `GHCR_USERNAME`, `GHCR_TOKEN` (иначе используются `GH_TOKEN` и твой GitHub login)
- `BINANCE_API_KEY`, `BINANCE_API_SECRET`
- `DOMAIN_PANEL`, `DOMAIN_STUDIO`
- `ENVIRONMENT` (например `production`)
- `JWT_SECRET`
- `WEB_USER`, `WEB_PASS`
- `OPENAI_API_KEY`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID_ADMIN`

Пример: `scripts/.env.ai.example`

### 🚀 Запуск

В Codespace:

```bash
bash scripts/bootstrap-ai-access.sh
```

### ✅ Проверки

- `gh auth status` → GitHub доступ активен
- `docker login ghcr.io` → логин успешен (скрипт логинит автоматически)
- `ssh mirai-deploy echo ok` → сервер доступен

### 📦 Что дальше

- пуш веток/тегов, PR/релизы, запуск workflows;
- сборка и push образов в GHCR;
- деплой и перезапуск сервисов на сервере;
- интеграции (Binance, Telegram, OpenAI и др.).
