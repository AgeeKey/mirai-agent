# 🤖 Автономный AI-Агент Mirai - Инструкция по настройке

## 📋 Обзор системы

Создан полнофункциональный автономный AI-агент для торговой платформы Mirai с архитектурой BabyAGI. Агент способен:

- 🧠 **Автономное принятие решений** с использованием OpenAI GPT-4
- 📊 **Анализ рынка** в реальном времени 
- 🔄 **Самостоятельное планирование** и выполнение задач
- ⚡ **Автоматическое размещение ордеров** (с системой безопасности)
- 📈 **Технический анализ** и анализ новостей
- 🛡️ **Многоуровневая система безопасности**

## 🎯 Что сделано автоматически

✅ **Архитектура агента** (`app/agent/autonomous_agent.py`)
- BabyAGI цикл: планирование → выполнение → анализ → новые задачи
- Интеграция с OpenAI GPT-4
- Система памяти на SQLite
- Автономное принятие решений

✅ **Продвинутые торговые инструменты** (`app/agent/trading_tools.py`)
- Реальные рыночные данные через Binance API
- Технический анализ (RSI, MACD, Bollinger Bands)
- Анализ новостей и настроений рынка
- Оптимизация портфеля
- Риск-менеджмент

✅ **Система безопасности** (`app/agent/safety_system.py`)
- Песочница для тестирования
- Лимиты по размеру позиций
- Подтверждения для критических операций
- Многоуровневая валидация

✅ **Конфигурация** (`app/agent/agent_config.py`)
- Предустановленные торговые цели
- Настройки безопасности
- Промпты для AI
- Параметры риска

✅ **Исполняемый лаунчер** (`app/agent/run_agent.py`)
- Интерактивный режим
- Проверка требований
- Командная строка
- Отображение статуса

## 🔧 Что нужно настроить вручную

### 1. 🔑 API ключи OpenAI (ОБЯЗАТЕЛЬНО)

```bash
# Экспорт переменной окружения
export OPENAI_API_KEY='your-openai-api-key-here'

# Или добавить в ~/.bashrc для постоянного использования
echo 'export OPENAI_API_KEY="your-openai-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**Где получить:**
- Регистрация: https://platform.openai.com/
- Создание API ключа: https://platform.openai.com/api-keys
- Модель: Требуется доступ к GPT-4

### 2. 📦 Установка зависимостей

```bash
# Переход в директорию агента
cd /root/mirai-agent

# Установка OpenAI библиотеки
pip install openai

# Установка дополнительных зависимостей для торговли
pip install requests pandas numpy yfinance

# Проверка установки
python -c "import openai; print('OpenAI installed successfully')"
```

### 3. 🏦 Binance API (для реальной торговли)

```bash
# Добавить в .env файл или экспортировать
export BINANCE_API_KEY='your-binance-api-key'
export BINANCE_API_SECRET='your-binance-api-secret'

# Для тестовой сети (рекомендуется для начала)
export BINANCE_TESTNET='true'
```

**Настройка Binance:**
- Создать аккаунт: https://www.binance.com/
- API управление: Account → API Management
- Включить Spot & Margin Trading
- **⚠️ ВАЖНО:** Начните с testnet!

### 4. ⚙️ Конфигурация риска

Отредактируйте `/root/mirai-agent/app/agent/agent_config.py`:

```python
# Настройки риска - ИЗМЕНИТЕ ПОД СВОИ ПОТРЕБНОСТИ
MAX_POSITION_SIZE = 100.0  # Максимальный размер позиции в USDT
MAX_DAILY_LOSS = 50.0      # Максимальная дневная потеря
RISK_TOLERANCE = "MEDIUM"   # LOW, MEDIUM, HIGH
SANDBOX_MODE = True         # Начните с True!
```

### 5. 🗄️ База данных (для продакшена)

По умолчанию используется SQLite. Для продакшена рекомендуется PostgreSQL:

```bash
# Установка PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Создание базы данных
sudo -u postgres createdb mirai_agent

# Настройка подключения в .env
export DATABASE_URL='postgresql://user:password@localhost/mirai_agent'
```

## 🚀 Запуск агента

### Интерактивный режим (рекомендуется)

```bash
cd /root/mirai-agent
python app/agent/run_agent.py --interactive
```

Вы увидите:
```
🤖 === MIRAI AUTONOMOUS AGENT ===
🛡️  Safety Status: SANDBOX_MODE=True
📊 Available Tools: Market Analysis, Risk Management, Portfolio Optimization
⚙️  Configuration: Loaded from agent_config.py

Select objective:
1. Monitor market trends and identify opportunities
2. Optimize current portfolio positions
3. Research specific cryptocurrency
4. Execute conservative trading strategy
5. Custom objective

Choice: 
```

### Режим командной строки

```bash
# Выполнить конкретную цель
python app/agent/run_agent.py --objective "analyze BTC trends"

# Запуск с кастомными параметрами
python app/agent/run_agent.py --max-iterations 10 --sandbox-mode
```

### Фоновый режим

```bash
# Запуск как демон
nohup python app/agent/run_agent.py --objective "monitor market" --continuous > agent.log 2>&1 &
```

## 🔍 Мониторинг работы

### Логи агента

```bash
# Просмотр логов в реальном времени
tail -f /root/mirai-agent/logs/agent.log

# Просмотр последних действий
cat /root/mirai-agent/state/mirai.db | sqlite3 "SELECT * FROM agent_memory ORDER BY timestamp DESC LIMIT 10;"
```

### Веб-интерфейс мониторинга

```bash
# Запуск веб-панели (если настроена)
cd /root/mirai-agent
python web_panel_production.py
```

## ⚠️ Система безопасности

### Уровни риска

- **🟢 LOW**: Только анализ, никаких сделок
- **🟡 MEDIUM**: Микро-позиции, строгие лимиты  
- **🔴 HIGH**: Полная торговля (только для экспертов!)

### Режим песочницы

```python
# В agent_config.py
SANDBOX_MODE = True  # Все операции симулируются

# Лог операций в песочнице
[SANDBOX] Would place BUY order: BTC/USDT, amount: 0.001, price: 43250
[SANDBOX] Risk assessment: LOW risk (2.1% portfolio allocation)
```

### Экстренная остановка

```bash
# Найти процесс агента
ps aux | grep autonomous_agent

# Остановить агент
kill -TERM <process_id>

# Или если запущен в фоне
pkill -f "autonomous_agent"
```

## 🛠️ Устранение неполадок

### Проблема: "OpenAI API key not found"

```bash
# Проверить переменную
echo $OPENAI_API_KEY

# Если пустая, установить
export OPENAI_API_KEY='your-key-here'
```

### Проблема: "Binance connection error"

```bash
# Проверить подключение к интернету
ping api.binance.com

# Проверить API ключи
python -c "
import os
print('API Key set:', bool(os.getenv('BINANCE_API_KEY')))
print('API Secret set:', bool(os.getenv('BINANCE_API_SECRET')))
"
```

### Проблема: "Memory database locked"

```bash
# Проверить процессы, использующие базу
lsof /root/mirai-agent/state/mirai.db

# Если нужно, удалить блокировку
rm -f /root/mirai-agent/state/mirai.db-wal
rm -f /root/mirai-agent/state/mirai.db-shm
```

## 📈 Первые шаги

1. **Начните с песочницы**: `SANDBOX_MODE = True`
2. **Малые суммы**: `MAX_POSITION_SIZE = 10.0`  
3. **Мониторинг**: Следите за логами первые 24 часа
4. **Анализ результатов**: Изучите решения агента
5. **Постепенное увеличение**: Повышайте лимиты по мере уверенности

## 🎯 Заключение

Автономный AI-агент готов к работе! Основные компоненты созданы и протестированы. 

**Требуется только:**
- Настройка API ключей
- Конфигурация параметров риска
- Постепенное масштабирование

**Агент уже умеет:**
- Анализировать рынок самостоятельно
- Принимать торговые решения
- Управлять рисками
- Учиться на своем опыте

🚀 **Запускайте и наблюдайте, как AI торгует за вас!**