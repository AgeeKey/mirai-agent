# Mirai Agent — текущее состояние (дата: 2025-09-07)

## 1) Общая инфа

**Репозиторий:** AgeeKey/mirai-agent  
**Ветка:** main  
**Цель спринта:** Настройка CI/CD, исправление совместимости Python 3.9+, подготовка к деплою

## 2) Структура репо

```
mirai-agent/
├── app/
│   ├── __init__.py
│   ├── cli.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── advisor.py
│   │   ├── config.py
│   │   ├── explain_logger.py
│   │   ├── loop.py
│   │   ├── policy.py
│   │   ├── reports.py
│   │   └── schema.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── mirai_api/
│   │       ├── __init__.py
│   │       └── main.py
│   ├── telegram_bot/
│   │   ├── __init__.py
│   │   └── bot.py
│   ├── trader/
│   │   ├── __init__.py
│   │   ├── Dockerfile
│   │   ├── binance_client.py
│   │   ├── exchange_info.py
│   │   ├── orders.py
│   │   ├── pyproject.toml
│   │   ├── risk_engine.py
│   │   └── mirai_trader/
│   │       ├── __init__.py
│   │       └── core.py
│   └── web/
│       ├── __init__.py
│       ├── api.py
│       ├── ui.py
│       └── utils.py
├── web/
│   ├── README.md
│   └── services/
│       ├── __init__.py
│       ├── Dockerfile
│       ├── next-env.d.ts
│       ├── next.config.js
│       ├── package.json
│       ├── tsconfig.json
│       └── src/
│           └── app/
│               ├── layout.tsx
│               ├── page.tsx
│               └── globals.css
├── infra/
│   ├── docker-compose.yml
│   └── README.md
├── configs/
│   ├── logging.yaml
│   ├── risk.yaml
│   └── strategies.yaml
├── logs/
│   ├── explain.log
│   ├── mirai-agent-error.log
│   └── mirai-agent.log
├── reports/
│   ├── advisor_daily_2025-08-29.json
│   ├── advisor_summary_2025-08-29.txt
│   └── README.md
├── state/
│   └── mirai.db
├── .github/
│   └── workflows/
│       ├── ci-api.yml
│       ├── ci-services.yml
│       ├── ci-trader.yml
│       ├── ci.yml
│       └── copilot.yml
├── Dockerfile
├── Makefile
├── pyproject.toml
├── pytest.ini
├── requirements.txt
└── README.md
```

## 3) CI/CD (что есть и статус)

**Workflows:**

- **ci.yml** — ✅ (проверяет импорты, CLI, линтинг, форматирование)
- **ci-api.yml** — ✅ (проверяет API модуль)
- **ci-trader.yml** — ✅ (проверяет trader модуль)
- **ci-services.yml** — ✅ (проверяет web services)
- **copilot.yml** — ✅ (автоматические улучшения)

**Последние запуски:**
- ✅ CI/CD Pipeline (3 дня назад) - успешный
- ❌ CI/CD Pipeline (3 дня назад) - провал на Python 3.9 (datetime.UTC)
- ❌ CI Trader (3 дня назад) - провал на Python 3.9

**Python версия в CI:** 3.9, 3.11, 3.12  
**Форматирование:** ruff + black ✅  
**pre-commit:** установлен ✅

## 4) API (app/api)

**Точки:** 
- `/healthz` ✅ (возвращает `{"ok": true, "service": "mirai-api"}`)

**Импорты и пакеты:**
- `app/api/__init__.py` ✅
- `app/api/mirai_api/__init__.py` ✅

**Запуск локально:** `uvicorn mirai_api.main:app` ✅

**Проблемы/заметки:**
- API работает на 127.0.0.1:8000
- Использует FastAPI

## 5) Trader (app/trader)

**Базовые тесты:** ❌ (папка tests удалена)  
**Risk-engine / advisor:** ✅ (оба модуля присутствуют)

**TODO (что планируешь ближайшим коммитом):**
- Восстановить базовые тесты
- Добавить интеграционные тесты

## 6) Services (web/services)

**Next.js билд проходит:** ✅ (`npm run build` - успешный)  
**Линт:** ✅ (встроенный в Next.js)

**Что уже на странице /:**
- Базовая страница с layout
- Статические страницы

**TODO:**
- Добавить API интеграцию
- Реализовать dashboard для трейдинга

## 7) Инфраструктура / Деплой

**infra/docker-compose.yml:** ✅ (готов для локального запуска)  
**infra/env/.env.production.template:** ❌ (отсутствует)

**GHCR секреты:**
- GHCR_USERNAME, GHCR_TOKEN — ❌ (не проверено)

**SSH секреты:**
- SSH_HOST, SSH_USER, SSH_KEY — ❌ (не проверено)

**Сервер (Сингапур):**
- Docker/Compose — ❌ (не проверено)
- Nginx — ❌ (не проверено)
- Certbot — ❌ (не проверено)

## 8) Домены / DNS

**panel.aimirai.online:** ❌ (не проверено)  
**aimirai.info, www.aimirai.info:** ❌ (не проверено)

## 9) Безопасность

**Bind только 127.0.0.1 в API:** ✅  
**Bandit проходит:** ❌ (не проверено)  
**ENV-секреты не в гите:** ✅ (используется .env)

## 10) Скриншоты/логи

**Последние успешные CI:** 
- https://github.com/AgeeKey/mirai-agent/actions/runs/17472399947 ✅

**Логи ошибок:**
- Python 3.9: `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` (исправлено заменой на `Optional`)

## 11) Риски/блокеры

1. **Отсутствие production конфигурации** - нет docker-compose.prod.yml и .env.production.template
2. **Не настроены секреты GitHub** - нет GHCR и SSH секретов для деплоя
3. **Не проверен сервер** - неизвестно состояние инфраструктуры
4. **Отсутствуют тесты** - удалена папка tests, нет покрытия

## 12) Что хочешь сделать следующим шагом (1–3 пункта)

1. **Создать production конфигурацию** (docker-compose.prod.yml, .env.production.template)
2. **Настроить GHCR секреты** для автоматической сборки образов
3. **Проверить состояние сервера** и настроить Nginx/Certbot

## Быстрые команды для проверки

```bash
# Структура
tree -L 3 -I node_modules

# Версии
python --version && node -v && npm -v
# Python 3.12.1, v22.17.0, 9.8.1

# Локальный тест импортов
PYTHONPATH=./app python -c "import app.cli; import app.agent.loop; import app.trader.binance_client; print('All imports successful')"

# CLI тест
PYTHONPATH=./app python app/cli.py --help

# Next.js билд
cd web/services && npm install && npm run build
```
