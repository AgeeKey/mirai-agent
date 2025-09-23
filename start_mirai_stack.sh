#!/bin/bash
# Mirai Agent - Full Stack Launcher
# Запуск полной экосистемы автономного торгового агента

set -e

echo "🚀 Launching Mirai Agent Full Stack..."
echo "=================================="

# Активируем виртуальное окружение
if [ -f "/root/mirai-agent/.venv/bin/activate" ]; then
    source /root/mirai-agent/.venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Virtual environment not found, using system Python"
fi

# Переходим в корневую директорию
cd /root/mirai-agent

# Функция для проверки портов
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is in use"
        return 1
    else
        echo "✅ Port $1 is available"
        return 0
    fi
}

# Функция для запуска с логами
start_service() {
    local name=$1
    local command=$2
    local logfile=$3
    
    echo "🔄 Starting $name..."
    nohup $command > $logfile 2>&1 &
    local pid=$!
    echo $pid > /tmp/mirai_${name,,}.pid
    echo "✅ $name started (PID: $pid)"
    sleep 2
}

# Создаем директорию для логов
mkdir -p logs/services

# 1. Запуск API Backend
echo ""
echo "1️⃣  Starting API Backend..."
if check_port 8002; then
    start_service "API" "python3 simple_api.py" "logs/services/api.log"
else
    echo "ℹ️  API already running on port 8002"
fi

# 2. Запуск Web Frontend  
echo ""
echo "2️⃣  Starting Web Frontend..."
if check_port 3002; then
    cd web/services
    start_service "WEB" "npm run dev -- -p 3002" "../../logs/services/web.log"
    cd ../..
else
    echo "ℹ️  Web already running on port 3002"
fi

# 3. Запуск Trading Agent
echo ""
echo "3️⃣  Starting Trading Agent..."
start_service "TRADER" "python3 simple_trader.py" "logs/services/trader.log"

# 4. Мониторинг статуса
echo ""
echo "4️⃣  System Status Check..."
sleep 5

# Проверяем API
if curl -s http://localhost:8002/ | grep -q "Mirai"; then
    echo "✅ API Backend is responding"
else
    echo "❌ API Backend is not responding"
fi

# Проверяем Web
if curl -s http://localhost:3002/ | grep -q "html\|DOCTYPE"; then
    echo "✅ Web Frontend is responding"
else
    echo "❌ Web Frontend is not responding"
fi

# Проверяем Trader
if ps -p $(cat /tmp/mirai_trader.pid 2>/dev/null) > /dev/null 2>&1; then
    echo "✅ Trading Agent is running"
else
    echo "❌ Trading Agent is not running"
fi

echo ""
echo "🎯 Mirai Agent Full Stack Status:"
echo "================================="
echo "📊 API Backend:    http://localhost:8002"
echo "🌐 Web Frontend:   http://localhost:3002"
echo "🤖 Trading Agent:  Running in dry-run mode"
echo "📝 Logs:          logs/services/"
echo ""
echo "📋 Management Commands:"
echo "  View API logs:    tail -f logs/services/api.log"
echo "  View Web logs:    tail -f logs/services/web.log"
echo "  View Trader logs: tail -f logs/services/trader.log"
echo "  Stop all:         ./stop_mirai_stack.sh"
echo ""
echo "🚀 Mirai Agent Full Stack is operational!"