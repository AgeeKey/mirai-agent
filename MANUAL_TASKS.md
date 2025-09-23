# 🤖 Mirai Autonomous AI Agent - Manual Tasks Checklist

## ✅ Что уже создано автоматически

Полнофункциональный автономный AI-агент с BabyAGI архитектурой включает:

- 🧠 **Автономный агент** (`app/agent/autonomous_agent.py`) - 470 строк кода
- ⚙️ **Конфигурация** (`app/agent/agent_config.py`) - Настройки безопасности и цели
- 🛠️ **Торговые инструменты** (`app/agent/trading_tools.py`) - Полный набор для анализа и торговли
- 🛡️ **Система безопасности** (`app/agent/safety_system.py`) - Многоуровневая защита
- 🚀 **Лаунчер** (`app/agent/run_agent.py`) - Интерактивный запуск и CLI
- 📋 **Документация** (`docs/AUTONOMOUS_AGENT_SETUP.md`) - Полная инструкция
- 🔧 **Скрипт настройки** (`scripts/setup_autonomous_agent.sh`) - Автоматизация

---

## 🔧 Ручные задачи для пользователя

### 1. 🔑 Настройка OpenAI API (КРИТИЧНО)

**❗ ОБЯЗАТЕЛЬНО для работы агента**

```bash
# Получить API ключ на https://platform.openai.com/api-keys
export OPENAI_API_KEY='sk-your-openai-api-key-here'

# Добавить в профиль для постоянного использования
echo 'export OPENAI_API_KEY="sk-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**Проверка:**
```bash
echo $OPENAI_API_KEY  # Должен отобразить ваш ключ
```

### 2. 📦 Установка зависимостей

```bash
# Автоматическая установка (рекомендуется)
cd /root/mirai-agent
./scripts/setup_autonomous_agent.sh

# Или ручная установка
pip install openai requests pandas numpy yfinance
```

### 3. 🏦 Настройка Binance API (опционально)

**Для реальной торговли:**

```bash
# Testnet (рекомендуется для начала)
export BINANCE_API_KEY='your-testnet-api-key'
export BINANCE_API_SECRET='your-testnet-secret'
export BINANCE_TESTNET='true'

# Mainnet (только для продакшена!)
export BINANCE_API_KEY='your-live-api-key'
export BINANCE_API_SECRET='your-live-secret'
export BINANCE_TESTNET='false'
```

**Как получить:**
1. Регистрация на https://www.binance.com/
2. Account → API Management
3. Создать новый API ключ
4. Включить Spot & Margin Trading

### 4. ⚙️ Конфигурация параметров риска

**Редактировать:** `/root/mirai-agent/app/agent/agent_config.py`

```python
# ВАЖНО: Настройте под свои потребности!
MAX_POSITION_SIZE = 100.0      # Макс. размер позиции в USDT
MAX_DAILY_LOSS = 50.0          # Макс. дневная потеря в USDT  
RISK_TOLERANCE = "MEDIUM"       # LOW, MEDIUM, HIGH
SANDBOX_MODE = True            # True для тестирования!

# Настройки уведомлений
NOTIFICATION_SETTINGS = {
    "telegram_enabled": False,  # Настроить если нужны уведомления
    "email_enabled": False,
    "discord_enabled": False
}
```

### 5. 🗄️ База данных (для продакшена)

**По умолчанию:** SQLite (подходит для большинства случаев)

**Для высоких нагрузок:** PostgreSQL

```bash
# Установка PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Создание базы данных
sudo -u postgres createdb mirai_agent

# Настройка подключения
export DATABASE_URL='postgresql://user:password@localhost/mirai_agent'
```

### 6. 📊 Мониторинг и логирование

**Создать директории логов:**
```bash
mkdir -p /root/mirai-agent/logs
mkdir -p /root/mirai-agent/reports
```

**Настроить ротацию логов (опционально):**
```bash
# Добавить в crontab
crontab -e

# Добавить строку для очистки старых логов
0 0 * * * find /root/mirai-agent/logs -name "*.log" -mtime +7 -delete
```

### 7. 🔐 Безопасность (для продакшена)

**Настройка файрвола:**
```bash
# Только для продакшена, если агент запущен как веб-сервис
sudo ufw allow 8000/tcp  # Если используется веб-интерфейс
sudo ufw enable
```

**Создание пользователя для агента:**
```bash
# Создать отдельного пользователя (рекомендуется для продакшена)
sudo useradd -m -s /bin/bash mirai-agent
sudo usermod -aG sudo mirai-agent

# Скопировать агент в домашнюю директорию пользователя
sudo cp -r /root/mirai-agent /home/mirai-agent/
sudo chown -R mirai-agent:mirai-agent /home/mirai-agent/mirai-agent
```

### 8. 🚀 Настройка автозапуска (опционально)

**Создать systemd сервис:**
```bash
sudo tee /etc/systemd/system/mirai-agent.service > /dev/null <<EOF
[Unit]
Description=Mirai Autonomous Trading Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/mirai-agent
Environment=OPENAI_API_KEY=your-key-here
Environment=BINANCE_API_KEY=your-binance-key
Environment=BINANCE_API_SECRET=your-binance-secret
ExecStart=/usr/bin/python3 app/agent/run_agent.py --continuous
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Активация сервиса
sudo systemctl daemon-reload
sudo systemctl enable mirai-agent
sudo systemctl start mirai-agent
```

### 9. 📱 Уведомления (опционально)

**Telegram бот:**
```bash
# Получить токен от @BotFather
export TELEGRAM_BOT_TOKEN='your-bot-token'
export TELEGRAM_CHAT_ID='your-chat-id'
```

**Email уведомления:**
```bash
# SMTP настройки
export SMTP_SERVER='smtp.gmail.com'
export SMTP_PORT='587'
export SMTP_USERNAME='your-email@gmail.com'
export SMTP_PASSWORD='your-app-password'
```

### 10. 🔄 Резервное копирование

**Настроить бэкап базы данных:**
```bash
# Создать скрипт бэкапа
cat > /root/mirai-agent/scripts/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/mirai-agent/backups"
mkdir -p $BACKUP_DIR

# Бэкап базы данных
cp /root/mirai-agent/state/mirai.db $BACKUP_DIR/mirai_db_$DATE.db

# Бэкап конфигурации
tar -czf $BACKUP_DIR/config_$DATE.tar.gz app/agent/*.py

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
EOF

chmod +x /root/mirai-agent/scripts/backup.sh

# Добавить в crontab для ежедневного бэкапа
echo "0 2 * * * /root/mirai-agent/scripts/backup.sh" | crontab -
```

---

## 🎯 Последовательность первого запуска

### Шаг 1: Быстрая настройка
```bash
cd /root/mirai-agent
./scripts/setup_autonomous_agent.sh
```

### Шаг 2: Настройка API ключей
```bash
export OPENAI_API_KEY='your-openai-key'
# Опционально: export BINANCE_API_KEY='your-binance-key'
```

### Шаг 3: Первый запуск в песочнице
```bash
python app/agent/run_agent.py --interactive
# Выберите цель #1: "Monitor market trends and identify opportunities"
```

### Шаг 4: Мониторинг работы
```bash
# В другом терминале следите за логами
tail -f logs/agent.log
```

### Шаг 5: Анализ результатов
```bash
# Просмотр решений агента
sqlite3 state/mirai.db "SELECT * FROM trading_decisions ORDER BY timestamp DESC LIMIT 10;"
```

---

## ⚠️ Важные замечания

### 🔴 Критично:
- **ВСЕГДА начинайте с `SANDBOX_MODE = True`**
- **Начинайте с малых сумм**: `MAX_POSITION_SIZE = 10.0`
- **Используйте Binance testnet** для первых экспериментов
- **Мониторьте агент первые 24 часа** непрерывно

### 🟡 Рекомендации:
- Изучите логи агента перед увеличением лимитов
- Проверьте качество решений в песочнице
- Постепенно увеличивайте параметры риска
- Регулярно делайте бэкапы

### 🟢 Опционально:
- Настройка уведомлений
- Автозапуск системы
- Мониторинг производительности
- Интеграция с внешними сервисами

---

## 🆘 Поддержка и помощь

**Логи для диагностики:**
- `/root/mirai-agent/logs/agent.log` - Основные логи агента
- `/root/mirai-agent/state/mirai.db` - База данных решений
- `/root/mirai-agent/reports/` - Отчеты анализа

**Команды диагностики:**
```bash
# Проверка статуса
python app/agent/run_agent.py --status

# Тест подключения к API
python -c "import openai; print('OpenAI OK')"

# Проверка базы данных
sqlite3 state/mirai.db ".tables"
```

**В случае проблем:**
1. Проверьте API ключи
2. Убедитесь в наличии интернет-соединения
3. Проверьте логи на ошибки
4. Перезапустите агент в безопасном режиме

---

## ✨ Готово к использованию!

После выполнения ручных задач у вас будет:
- 🤖 Полностью автономный AI-агент
- 🛡️ Система безопасности с ограничениями
- 📊 Анализ рынка в реальном времени
- 💼 Автоматическое управление портфелем
- 📈 Интеллектуальные торговые решения

**Запуск:** `python app/agent/run_agent.py --interactive`

🚀 **Агент будет торговать за вас автономно!**