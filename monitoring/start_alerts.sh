#!/bin/bash

# Mirai Agent - Запуск системы алертов
# Запускает мониторинг критических событий и уведомления

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚨 Запуск системы алертов Mirai Agent..."
echo "======================================="

# Создаем директории если их нет
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/state"

# Проверяем зависимости
echo "📦 Проверка зависимостей..."

if ! python3 -c "import asyncio, sqlite3, httpx" &> /dev/null; then
    echo "⚠️  Устанавливаем зависимости..."
    pip3 install httpx asyncio-background-tasks
fi

echo "✅ Зависимости готовы"

# Проверяем доступность панели мониторинга
echo "🔍 Проверка панели мониторинга..."

if curl -s --max-time 5 "http://localhost:9999/health" > /dev/null 2>&1; then
    echo "✅ Панель мониторинга доступна"
else
    echo "⚠️  Панель мониторинга недоступна. Запустите сначала simple_dashboard.py"
    echo "   cd $SCRIPT_DIR && python3 simple_dashboard.py"
fi

# Проверяем Telegram бота
echo "🔍 Проверка Telegram бота..."

if curl -s --max-time 5 "http://localhost:8002/health" > /dev/null 2>&1; then
    echo "✅ Telegram бот доступен"
else
    echo "⚠️  Telegram бот недоступен. Алерты будут только в логах."
fi

echo ""
echo "🚨 Запуск сервиса алертов..."
echo "📍 Alert API: http://localhost:9998"
echo "📊 Активные алерты: http://localhost:9998/alerts/active"
echo "📈 Статистика: http://localhost:9998/alerts/stats"
echo ""

# Останавливаем существующие процессы
if netstat -tlnp 2>/dev/null | grep -q ":9998 "; then
    echo "⚠️  Порт 9998 занят. Останавливаем существующий процесс..."
    pkill -f "alert_api.py" || true
    sleep 2
fi

# Запускаем API алертов
cd "$SCRIPT_DIR"

echo "🔄 Запуск Alert API на порту 9998..."
echo "Для остановки нажмите Ctrl+C"
echo "======================================="

# Запуск с логированием
python3 alert_api.py 2>&1 | tee "$PROJECT_ROOT/logs/alert_service.log"