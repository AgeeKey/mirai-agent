#!/bin/bash

# Mirai Agent - Простой запуск мониторинга
# Запускает легковесную панель мониторинга

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Запуск простой панели мониторинга Mirai Agent..."
echo "==================================================="

# Проверяем доступность Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python3 для продолжения."
    exit 1
fi

# Создаем директории если их нет
mkdir -p "$PROJECT_ROOT/logs/monitoring"
mkdir -p "$PROJECT_ROOT/state"

# Проверяем зависимости
echo "📦 Проверка зависимостей..."

DEPENDENCIES=(
    "fastapi"
    "uvicorn"
    "psutil"
    "httpx"
)

MISSING_DEPS=()

for dep in "${DEPENDENCIES[@]}"; do
    if ! python3 -c "import $dep" &> /dev/null; then
        MISSING_DEPS+=("$dep")
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "⚠️  Устанавливаем недостающие зависимости: ${MISSING_DEPS[*]}"
    pip3 install "${MISSING_DEPS[@]}"
fi

echo "✅ Все зависимости установлены"

# Проверяем состояние других сервисов
echo "🔍 Проверка состояния сервисов..."

check_service() {
    local name=$1
    local url=$2
    local timeout=${3:-5}
    
    if curl -s --max-time $timeout "$url" > /dev/null 2>&1; then
        echo "✅ $name - работает"
        return 0
    else
        echo "⚠️  $name - недоступен ($url)"
        return 1
    fi
}

# Проверяем основные сервисы
check_service "Trading API" "http://localhost:8001/health" || true
check_service "Web API" "http://localhost:8000/health" || true
check_service "AI Orchestrator" "http://localhost:8080/health" || true

echo ""
echo "🖥️  Запуск панели мониторинга..."

# Останавливаем существующие процессы на порту 9999
if netstat -tlnp 2>/dev/null | grep -q ":9999 "; then
    echo "⚠️  Порт 9999 занят. Останавливаем существующий процесс..."
    pkill -f "simple_dashboard.py" || true
    sleep 2
fi

# Запускаем панель мониторинга
cd "$SCRIPT_DIR"

echo "🌐 Запуск веб-панели на http://localhost:9999"
echo "📊 Доступ к метрикам: http://localhost:9999/metrics"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo "================================================"

# Запуск с логированием
python3 simple_dashboard.py 2>&1 | tee "$PROJECT_ROOT/logs/monitoring/dashboard.log"