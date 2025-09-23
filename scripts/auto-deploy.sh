#!/bin/bash

# Mirai Ecosystem Auto-Deploy Script
# Автоматическое развертывание всех компонентов

set -e

echo "🚀 Запуск автоматического развертывания экосистемы Mirai"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Проверка требований
check_requirements() {
    log "Проверка системных требований..."
    
    if ! command -v docker &> /dev/null; then
        log "❌ Docker не найден"
        exit 1
    fi
    
    if ! command -v node &> /dev/null; then
        log "❌ Node.js не найден"
        exit 1
    fi
    
    log "✅ Все требования выполнены"
}

# Сборка backend
build_backend() {
    log "🏗️ Сборка backend контейнеров..."
    
    cd /root/mirai-agent
    docker build -t mirai-ecosystem:latest -f Dockerfile.ecosystem .
    
    log "✅ Backend собран"
}

# Сборка frontend
build_frontend() {
    log "🎨 Сборка frontend..."
    
    cd /root/mirai-agent/frontend/trading
    
    # Проверяем установку зависимостей
    if [ ! -d "node_modules" ]; then
        log "📦 Установка зависимостей..."
        npm install
    fi
    
    # Собираем продакшн версию
    npm run build
    
    log "✅ Frontend собран"
}

# Запуск сервисов
start_services() {
    log "🚀 Запуск сервисов..."
    
    # Создаем сети и директории
    docker network create mirai-ecosystem || true
    mkdir -p /root/mirai-agent/deployment/data/{trading,services,postgres,redis}
    chmod -R 777 /root/mirai-agent/deployment/data
    
    # Останавливаем старые контейнеры
    docker stop mirai-trading-ecosystem mirai-services-ecosystem mirai-nginx-simple mirai-postgres mirai-redis 2>/dev/null || true
    docker rm mirai-trading-ecosystem mirai-services-ecosystem mirai-nginx-simple mirai-postgres mirai-redis 2>/dev/null || true
    
    # Запускаем базы данных
    docker run -d --name mirai-postgres \
        --network mirai-ecosystem \
        -e POSTGRES_DB=mirai_production \
        -e POSTGRES_USER=mirai \
        -e POSTGRES_PASSWORD=mirai_secure_pass_2024 \
        -v /root/mirai-agent/deployment/data/postgres:/var/lib/postgresql/data \
        postgres:15-alpine
    
    docker run -d --name mirai-redis \
        --network mirai-ecosystem \
        -v /root/mirai-agent/deployment/data/redis:/data \
        redis:7-alpine redis-server --appendonly yes --requirepass redis_secure_pass_2024
    
    # Ждем готовности баз
    sleep 20
    
    # Запускаем приложения
    docker run -d --name mirai-trading-ecosystem \
        --network mirai-ecosystem \
        -p 8001:8000 \
        -e SERVICE_TYPE=trading \
        -e DOMAIN=aimirai.online \
        -e DRY_RUN=false \
        -v /root/mirai-agent/deployment/data/trading:/app/state \
        -v /root/mirai-agent/deployment/logs:/app/logs \
        mirai-ecosystem:latest
    
    docker run -d --name mirai-services-ecosystem \
        --network mirai-ecosystem \
        -p 8002:8000 \
        -e SERVICE_TYPE=services \
        -e DOMAIN=aimirai.info \
        -e DRY_RUN=false \
        -v /root/mirai-agent/deployment/data/services:/app/state \
        -v /root/mirai-agent/deployment/logs:/app/logs \
        mirai-ecosystem:latest
    
    # Запускаем nginx
    docker run -d --name mirai-nginx-ecosystem \
        --network host \
        -v /root/mirai-agent/deployment/nginx-working.conf:/etc/nginx/nginx.conf:ro \
        nginx:alpine
    
    log "✅ Сервисы запущены"
}

# Запуск frontend dev server
start_frontend_dev() {
    log "🎯 Запуск frontend dev server..."
    
    cd /root/mirai-agent/frontend/trading
    nohup npm run dev > /root/mirai-agent/deployment/logs/frontend.log 2>&1 &
    
    log "✅ Frontend dev server запущен на порту 3001"
}

# Проверка статуса
check_status() {
    log "🔍 Проверка статуса сервисов..."
    
    sleep 30
    
    # Проверяем контейнеры
    echo "Статус контейнеров:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    # Проверяем API
    echo -e "\nПроверка API:"
    if curl -s http://localhost:8001/healthz >/dev/null; then
        echo "✅ Trading API: работает"
    else
        echo "❌ Trading API: не отвечает"
    fi
    
    if curl -s http://localhost:8002/healthz >/dev/null; then
        echo "✅ Services API: работает"
    else
        echo "❌ Services API: не отвечает"
    fi
    
    # Проверяем frontend
    if curl -s http://localhost:3001 >/dev/null; then
        echo "✅ Frontend: работает"
    else
        echo "❌ Frontend: не отвечает"
    fi
}

# Создание мониторинга
setup_monitoring() {
    log "📊 Настройка мониторинга..."
    
    # Создаем скрипт мониторинга
    cat > /root/mirai-agent/scripts/monitor.sh << 'EOF'
#!/bin/bash

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking services..."
    
    # Проверяем контейнеры
    docker ps --format "{{.Names}}" | grep -E "mirai-.*-ecosystem|mirai-postgres|mirai-redis" | while read container; do
        if docker ps | grep -q $container; then
            echo "✅ $container: running"
        else
            echo "❌ $container: stopped - restarting..."
            docker restart $container
        fi
    done
    
    # Проверяем API endpoints
    for port in 8001 8002 3001; do
        if curl -s http://localhost:$port/healthz >/dev/null 2>&1 || curl -s http://localhost:$port >/dev/null 2>&1; then
            echo "✅ Port $port: responding"
        else
            echo "❌ Port $port: not responding"
        fi
    done
    
    sleep 300  # Проверка каждые 5 минут
done
EOF
    
    chmod +x /root/mirai-agent/scripts/monitor.sh
    
    # Запускаем мониторинг в фоне
    nohup /root/mirai-agent/scripts/monitor.sh > /root/mirai-agent/deployment/logs/monitor.log 2>&1 &
    
    log "✅ Мониторинг настроен"
}

# Основная функция
main() {
    check_requirements
    build_backend
    build_frontend
    start_services
    start_frontend_dev
    setup_monitoring
    check_status
    
    log "🎉 Развертывание завершено!"
    log ""
    log "Доступные URL:"
    log "- Trading Platform: http://aimirai.online (через nginx)"
    log "- Services Platform: http://aimirai.info (через nginx)"
    log "- Trading API: http://localhost:8001"
    log "- Services API: http://localhost:8002"
    log "- Trading Frontend: http://localhost:3001"
    log ""
    log "Логи:"
    log "- Backend: docker logs mirai-trading-ecosystem"
    log "- Frontend: tail -f /root/mirai-agent/deployment/logs/frontend.log"
    log "- Monitor: tail -f /root/mirai-agent/deployment/logs/monitor.log"
}

# Обработка аргументов
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "status")
        check_status
        ;;
    "restart")
        log "🔄 Перезапуск сервисов..."
        start_services
        start_frontend_dev
        check_status
        ;;
    *)
        echo "Использование: $0 [deploy|status|restart]"
        exit 1
        ;;
esac