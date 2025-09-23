#!/bin/bash

# Mirai Autonomous Controller
# Главный контроллер автономной системы

set -e

echo "🤖 Mirai Autonomous Controller v1.0"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a /root/mirai-agent/logs/controller.log
}

# Проверка статуса автономной системы
check_autonomous_status() {
    if pgrep -f "mirai_autonomous.py" > /dev/null; then
        log "✅ Автономная система запущена"
        return 0
    else
        log "❌ Автономная система не запущена"
        return 1
    fi
}

# Запуск автономной системы
start_autonomous() {
    log "🚀 Запуск автономной системы..."
    
    if check_autonomous_status; then
        log "ℹ️ Автономная система уже запущена"
        return 0
    fi
    
    # Создаем venv если нужно
    if [ ! -d "/root/mirai-agent/venv" ]; then
        python3 -m venv /root/mirai-agent/venv
        source /root/mirai-agent/venv/bin/activate
        pip install psutil requests
    fi
    
    # Запускаем автономную систему в фоне
    cd /root/mirai-agent
    source /root/mirai-agent/venv/bin/activate
    nohup python3 mirai_autonomous.py > /root/mirai-agent/logs/autonomous_output.log 2>&1 &
    
    sleep 5
    
    if check_autonomous_status; then
        log "✅ Автономная система успешно запущена"
    else
        log "❌ Ошибка запуска автономной системы"
        return 1
    fi
}

# Остановка автономной системы
stop_autonomous() {
    log "🛑 Остановка автономной системы..."
    
    pkill -f "mirai_autonomous.py" || true
    sleep 2
    
    if ! check_autonomous_status; then
        log "✅ Автономная система остановлена"
    else
        log "⚠️ Принудительная остановка..."
        pkill -9 -f "mirai_autonomous.py" || true
    fi
}

# Перезапуск автономной системы
restart_autonomous() {
    log "🔄 Перезапуск автономной системы..."
    stop_autonomous
    sleep 3
    start_autonomous
}

# Проверка статуса всей экосистемы
check_ecosystem_status() {
    log "🔍 Проверка статуса экосистемы..."
    
    local status_file="/root/mirai-agent/status/ecosystem_status.json"
    mkdir -p /root/mirai-agent/status
    
    # Проверяем сервисы
    local api_status="down"
    local web_status="down"
    local autonomous_status="down"
    local monitoring_status="down"
    
    # API
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        api_status="up"
    fi
    
    # Web
    if curl -s http://localhost:3001 > /dev/null 2>&1; then
        web_status="up"
    fi
    
    # Autonomous
    if check_autonomous_status; then
        autonomous_status="up"
    fi
    
    # Monitoring
    if curl -s http://localhost:9090 > /dev/null 2>&1; then
        monitoring_status="up"
    fi
    
    # Создаем отчет
    cat > "$status_file" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "services": {
        "api": "$api_status",
        "web": "$web_status",
        "autonomous": "$autonomous_status",
        "monitoring": "$monitoring_status"
    },
    "system": {
        "cpu_usage": "$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')",
        "memory_usage": "$(free | awk 'FNR==2{printf "%.1f", $3/($3+$4)*100}')",
        "disk_usage": "$(df / | awk 'NR==2 {print $5}')",
        "uptime": "$(uptime -p)"
    },
    "docker": {
        "containers_running": "$(docker ps | wc -l)",
        "images": "$(docker images | wc -l)"
    }
}
EOF
    
    log "📊 Статус экосистемы:"
    log "  API: $api_status"
    log "  Web: $web_status"
    log "  Autonomous: $autonomous_status"
    log "  Monitoring: $monitoring_status"
}

# Инициализация всей экосистемы
init_ecosystem() {
    log "🌱 Инициализация экосистемы Mirai..."
    
    # Создаем необходимые директории
    mkdir -p /root/mirai-agent/{logs,status,reports,secrets,backups}
    
    # Запускаем базовые сервисы
    log "📦 Запуск базовых сервисов..."
    
    # API
    if ! curl -s http://localhost:8001/health > /dev/null 2>&1; then
        cd /root/mirai-agent
        source /root/mirai-agent/venv/bin/activate
        nohup python3 mirai_ecosystem_api.py > /root/mirai-agent/logs/api_output.log 2>&1 &
        sleep 5
        log "🔗 API запущен"
    fi
    
    # Web (Python сервер для dist)
    if ! curl -s http://localhost:3001 > /dev/null 2>&1; then
        cd /root/mirai-agent
        source /root/mirai-agent/venv/bin/activate
        nohup python3 web_server.py > /root/mirai-agent/logs/web_server_output.log 2>&1 &
        sleep 5
        log "🌐 Web интерфейс запущен"
    fi
    
    # Автономная система
    start_autonomous
    
    # Проверяем статус
    sleep 10
    check_ecosystem_status
    
    log "🎉 Инициализация завершена!"
}

# Полная остановка экосистемы
shutdown_ecosystem() {
    log "🛑 Остановка экосистемы..."
    
    # Останавливаем автономную систему
    stop_autonomous
    
    # Останавливаем API
    pkill -f "mirai_ecosystem_api.py" || true
    
    # Останавливаем Web
    pkill -f "npm.*start" || true
    
    # Останавливаем контейнеры
    docker stop $(docker ps -q) 2>/dev/null || true
    
    log "✅ Экосистема остановлена"
}

# Обновление системы
update_system() {
    log "📥 Обновление системы..."
    
    # Останавливаем сервисы
    stop_autonomous
    
    # Обновляем код (если в git)
    if [ -d ".git" ]; then
        git pull origin main || log "⚠️ Не удалось обновить код"
    fi
    
    # Обновляем зависимости
    pip install -r requirements.txt || true
    
    # Перезапускаем
    restart_autonomous
    
    log "✅ Обновление завершено"
}

# Создание backup
create_backup() {
    log "💾 Создание резервной копии..."
    
    local backup_dir="/root/mirai-agent/backups"
    local date_stamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$backup_dir/mirai_backup_$date_stamp.tar.gz"
    
    mkdir -p "$backup_dir"
    
    # Создаем архив
    tar -czf "$backup_file" \
        --exclude='logs/*' \
        --exclude='backups/*' \
        --exclude='node_modules/*' \
        --exclude='__pycache__/*' \
        /root/mirai-agent/
    
    log "✅ Backup создан: $backup_file"
}

# Показать логи
show_logs() {
    local service="${1:-autonomous}"
    
    case $service in
        "autonomous")
            tail -f /root/mirai-agent/logs/autonomous.log 2>/dev/null || echo "Лог файл не найден"
            ;;
        "api")
            tail -f /root/mirai-agent/logs/api_output.log 2>/dev/null || echo "Лог файл не найден"
            ;;
        "web")
            tail -f /root/mirai-agent/logs/web_output.log 2>/dev/null || echo "Лог файл не найден"
            ;;
        "controller")
            tail -f /root/mirai-agent/logs/controller.log 2>/dev/null || echo "Лог файл не найден"
            ;;
        *)
            echo "Доступные логи: autonomous, api, web, controller"
            ;;
    esac
}

# Показать справку
show_help() {
    echo "Mirai Autonomous Controller"
    echo ""
    echo "Использование: $0 [КОМАНДА]"
    echo ""
    echo "Команды:"
    echo "  start                Запустить автономную систему"
    echo "  stop                 Остановить автономную систему"
    echo "  restart              Перезапустить автономную систему"
    echo "  status               Показать статус системы"
    echo "  init                 Инициализировать всю экосистему"
    echo "  shutdown             Полностью остановить экосистему"
    echo "  update               Обновить систему"
    echo "  backup               Создать резервную копию"
    echo "  logs [service]       Показать логи (autonomous/api/web/controller)"
    echo "  help                 Показать эту справку"
    echo ""
}

# Основная функция
main() {
    local command="${1:-status}"
    
    # Создаем директорию для логов
    mkdir -p /root/mirai-agent/logs
    
    case $command in
        "start")
            start_autonomous
            ;;
        "stop")
            stop_autonomous
            ;;
        "restart")
            restart_autonomous
            ;;
        "status")
            check_ecosystem_status
            ;;
        "init")
            init_ecosystem
            ;;
        "shutdown")
            shutdown_ecosystem
            ;;
        "update")
            update_system
            ;;
        "backup")
            create_backup
            ;;
        "logs")
            show_logs "$2"
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo "Неизвестная команда: $command"
            show_help
            exit 1
            ;;
    esac
}

# Запуск
main "$@"