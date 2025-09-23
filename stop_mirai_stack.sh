#!/bin/bash
# Mirai Agent - Full Stack Stopper
# Остановка всех компонентов системы

echo "🛑 Stopping Mirai Agent Full Stack..."
echo "====================================="

# Функция для остановки процесса по PID файлу
stop_service() {
    local name=$1
    local pidfile="/tmp/mirai_${name,,}.pid"
    
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if ps -p $pid > /dev/null 2>&1; then
            echo "🔄 Stopping $name (PID: $pid)..."
            kill -TERM $pid
            sleep 2
            if ps -p $pid > /dev/null 2>&1; then
                echo "⚠️  Force killing $name..."
                kill -9 $pid
            fi
            echo "✅ $name stopped"
        else
            echo "ℹ️  $name was not running"
        fi
        rm -f "$pidfile"
    else
        echo "ℹ️  No PID file for $name"
    fi
}

# Остановка процессов по именам
kill_by_name() {
    local pattern=$1
    local name=$2
    
    local pids=$(pgrep -f "$pattern" || true)
    if [ -n "$pids" ]; then
        echo "🔄 Stopping $name processes..."
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        pids=$(pgrep -f "$pattern" || true)
        if [ -n "$pids" ]; then
            echo "⚠️  Force killing $name..."
            echo "$pids" | xargs kill -9 2>/dev/null || true
        fi
        echo "✅ $name processes stopped"
    else
        echo "ℹ️  No $name processes found"
    fi
}

# Останавливаем сервисы
stop_service "TRADER"
stop_service "WEB" 
stop_service "API"

# Останавливаем процессы по шаблонам
kill_by_name "uvicorn.*mirai_api" "API"
kill_by_name "npm.*dev.*3002" "Web Frontend"
kill_by_name "next.*dev.*3002" "Next.js"
kill_by_name "agent_loop" "Trading Agent"

# Освобождаем порты принудительно
for port in 8002 3002; do
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "🔄 Freeing port $port..."
        echo "$pids" | xargs kill -9 2>/dev/null || true
        echo "✅ Port $port freed"
    fi
done

# Очистка временных файлов
rm -f /tmp/mirai_*.pid
echo ""
echo "🏁 Mirai Agent Full Stack stopped successfully!"
echo "📝 Logs preserved in logs/services/"