#!/bin/bash

# 🚀 Mirai Agent - Services Management Script
# Управление всеми сервисами платформы

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}                    ${BLUE}🤖 MIRAI SERVICES MANAGER${NC}                    ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}              ${GREEN}Управление полной инфраструктурой${NC}                 ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_service() {
    local service_name="$1"
    local port="$2"
    
    if curl -s "http://localhost:$port" > /dev/null 2>&1; then
        print_status "$service_name запущен на порту $port"
        return 0
    else
        print_warning "$service_name не отвечает на порту $port"
        return 1
    fi
}

start_api() {
    print_info "Запуск FastAPI сервера..."
    cd /root/mirai-agent/app/api
    export $(cat ../../.env | grep -v '^#' | xargs)
    nohup uvicorn mirai_api.main:app --host 0.0.0.0 --port 8000 --reload > ../../logs/api.log 2>&1 &
    API_PID=$!
    sleep 3
    
    if check_service "FastAPI" "8000"; then
        echo $API_PID > /tmp/mirai_api.pid
        print_status "FastAPI запущен (PID: $API_PID)"
    else
        print_error "Ошибка запуска FastAPI"
        return 1
    fi
}

start_web() {
    print_info "Запуск Next.js веб-интерфейса..."
    cd /root/mirai-agent/web/services
    export $(cat ../../.env | grep -v '^#' | xargs)
    nohup npm run dev > ../../logs/web.log 2>&1 &
    WEB_PID=$!
    sleep 5
    
    if check_service "Next.js" "3000"; then
        echo $WEB_PID > /tmp/mirai_web.pid
        print_status "Next.js запущен (PID: $WEB_PID)"
    else
        print_error "Ошибка запуска Next.js"
        return 1
    fi
}

start_agent() {
    print_info "Запуск автономного агента..."
    cd /root/mirai-agent
    export $(cat .env | grep -v '^#' | xargs)
    nohup python3 app/agent/run_agent.py --objective "continuous market monitoring" --continuous > logs/agent.log 2>&1 &
    AGENT_PID=$!
    echo $AGENT_PID > /tmp/mirai_agent.pid
    print_status "Агент запущен в фоне (PID: $AGENT_PID)"
}

stop_services() {
    print_info "Остановка всех сервисов..."
    
    # Остановка по PID файлам
    for service in api web agent; do
        if [ -f "/tmp/mirai_$service.pid" ]; then
            PID=$(cat /tmp/mirai_$service.pid)
            if kill -0 $PID 2>/dev/null; then
                kill $PID
                print_status "Остановлен $service (PID: $PID)"
            fi
            rm -f /tmp/mirai_$service.pid
        fi
    done
    
    # Дополнительная очистка
    pkill -f "uvicorn.*mirai_api" || true
    pkill -f "npm run dev" || true
    pkill -f "run_agent.py" || true
    
    print_status "Все сервисы остановлены"
}

check_status() {
    print_info "Проверка статуса сервисов..."
    echo ""
    
    # Проверка API
    if check_service "FastAPI API" "8000"; then
        echo "  📍 Документация: http://localhost:8000/docs"
    fi
    
    # Проверка веб-интерфейса
    if check_service "Next.js Web" "3000"; then
        echo "  📍 Интерфейс: http://localhost:3000"
    fi
    
    # Проверка агента
    if pgrep -f "run_agent.py" > /dev/null; then
        print_status "Автономный агент активен"
        echo "  📍 Логи: tail -f /root/mirai-agent/logs/agent.log"
    else
        print_warning "Автономный агент не запущен"
    fi
    
    echo ""
    echo "📊 Процессы:"
    ps aux | grep -E "(uvicorn|npm|run_agent)" | grep -v grep || echo "  Нет активных процессов"
}

show_logs() {
    print_info "Выберите логи для просмотра:"
    echo "1. API логи"
    echo "2. Web логи" 
    echo "3. Agent логи"
    echo "4. Все логи"
    
    read -p "Выбор (1-4): " choice
    
    case $choice in
        1) tail -f /root/mirai-agent/logs/api.log ;;
        2) tail -f /root/mirai-agent/logs/web.log ;;
        3) tail -f /root/mirai-agent/logs/agent.log ;;
        4) tail -f /root/mirai-agent/logs/*.log ;;
        *) print_error "Неверный выбор" ;;
    esac
}

restart_services() {
    print_info "Перезапуск всех сервисов..."
    stop_services
    sleep 2
    start_all
}

start_all() {
    print_info "Запуск полной инфраструктуры Mirai..."
    
    # Создание директорий для логов
    mkdir -p /root/mirai-agent/logs
    
    # Загрузка переменных окружения
    if [ ! -f "/root/mirai-agent/.env" ]; then
        print_error "Файл .env не найден! Запустите сначала настройку."
        exit 1
    fi
    
    start_api
    start_web
    
    echo ""
    print_status "🎉 Все сервисы запущены!"
    echo ""
    echo "🌐 Доступные адреса:"
    echo "  📊 API + Docs: http://localhost:8000/docs"
    echo "  🎮 Web UI:     http://localhost:3000"
    echo ""
    echo "🤖 Для запуска агента:"
    echo "  ./start_agent.sh или выберите опцию 6"
}

main_menu() {
    while true; do
        print_banner
        
        echo "Выберите действие:"
        echo "1. 🚀 Запустить все сервисы"
        echo "2. ⏹️  Остановить все сервисы"
        echo "3. 🔄 Перезапустить сервисы"
        echo "4. 📊 Проверить статус"
        echo "5. 📋 Показать логи"
        echo "6. 🤖 Запустить агента"
        echo "7. 🚪 Выход"
        echo ""
        
        read -p "Ваш выбор (1-7): " choice
        
        case $choice in
            1) start_all ;;
            2) stop_services ;;
            3) restart_services ;;
            4) check_status ;;
            5) show_logs ;;
            6) start_agent ;;
            7) print_info "Выход..."; exit 0 ;;
            *) print_error "Неверный выбор! Попробуйте снова." ;;
        esac
        
        echo ""
        read -p "Нажмите Enter для продолжения..."
        clear
    done
}

# Проверка аргументов командной строки
case "${1:-menu}" in
    "start") start_all ;;
    "stop") stop_services ;;
    "restart") restart_services ;;
    "status") check_status ;;
    "logs") show_logs ;;
    "agent") start_agent ;;
    "menu"|*) main_menu ;;
esac