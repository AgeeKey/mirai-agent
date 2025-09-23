#!/bin/bash

# Mirai Performance Optimization Script
# Скрипт оптимизации производительности

set -e

echo "⚡ Оптимизация производительности Mirai Ecosystem"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Получение метрик системы
get_system_metrics() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    local memory_usage=$(free | awk 'FNR==2{printf "%.1f", $3/($3+$4)*100}')
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    
    echo "CPU: ${cpu_usage}%, Memory: ${memory_usage}%, Load: ${load_avg}"
}

# Оптимизация системы
optimize_system() {
    log "🔧 Оптимизация системных параметров..."
    
    # Оптимизация параметров ядра
    cat > /etc/sysctl.d/99-mirai-optimization.conf << 'EOF'
# Mirai Performance Optimization

# Network optimizations
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 16384 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.ipv4.tcp_congestion_control = bbr

# Memory optimizations
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# File system optimizations
fs.file-max = 2097152
EOF

    sysctl -p /etc/sysctl.d/99-mirai-optimization.conf
    
    log "✅ Системные параметры оптимизированы"
}

# Оптимизация Docker
optimize_docker() {
    log "🐳 Оптимизация Docker..."
    
    # Создаем оптимизированную конфигурацию Docker
    cat > /etc/docker/daemon.json << 'EOF'
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "storage-opts": [
        "overlay2.override_kernel_check=true"
    ],
    "experimental": true,
    "metrics-addr": "127.0.0.1:9323"
}
EOF

    # Перезапускаем Docker
    systemctl restart docker
    
    # Очищаем неиспользуемые ресурсы
    docker system prune -f
    
    log "✅ Docker оптимизирован"
}

# Оптимизация базы данных
optimize_database() {
    log "🗄️ Оптимизация базы данных..."
    
    # Если PostgreSQL запущен, оптимизируем
    if docker ps | grep -q postgres; then
        docker exec -it mirai-postgres psql -U mirai -d mirai_production -c "VACUUM ANALYZE;"
        docker exec -it mirai-postgres psql -U mirai -d mirai_production -c "REINDEX DATABASE mirai_production;"
        log "✅ PostgreSQL оптимизирован"
    fi
    
    # Если есть SQLite, оптимизируем
    if [ -f "/root/mirai-agent/state/mirai.db" ]; then
        sqlite3 /root/mirai-agent/state/mirai.db "VACUUM;"
        sqlite3 /root/mirai-agent/state/mirai.db "REINDEX;"
        log "✅ SQLite оптимизирован"
    fi
}

# Оптимизация веб-сервера
optimize_web() {
    log "🌐 Оптимизация веб-сервера..."
    
    # Создаем оптимизированную конфигурацию nginx
    cat > /root/mirai-agent/deployment/nginx-optimized.conf << 'EOF'
events {
    worker_connections 2048;
    use epoll;
    multi_accept on;
}

http {
    # Basic Settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip Settings
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=general:10m rate=30r/s;

    # Main server configuration
    server {
        listen 80;
        server_name localhost;

        # API routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://127.0.0.1:8001;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Caching for API responses
            proxy_cache_valid 200 5m;
            proxy_cache_valid 404 1m;
        }

        # Frontend
        location / {
            limit_req zone=general burst=50 nodelay;
            proxy_pass http://127.0.0.1:3001;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
EOF

    log "✅ Веб-сервер оптимизирован"
}

# Мониторинг процессов
monitor_processes() {
    log "📊 Анализ процессов..."
    
    # Находим процессы с высоким потреблением CPU
    local high_cpu_processes=$(ps aux --sort=-%cpu | head -10)
    echo "Топ процессов по CPU:"
    echo "$high_cpu_processes"
    
    # Находим процессы с высоким потреблением памяти
    local high_mem_processes=$(ps aux --sort=-%mem | head -10)
    echo "Топ процессов по памяти:"
    echo "$high_mem_processes"
    
    # Проверяем зомби-процессы
    local zombie_count=$(ps aux | awk '$8 ~ /^Z/ { count++ } END { print count+0 }')
    if [ $zombie_count -gt 0 ]; then
        log "⚠️ Найдено $zombie_count зомби-процессов"
    fi
}

# Оптимизация приложений
optimize_applications() {
    log "📱 Оптимизация приложений..."
    
    # Перезапускаем приложения с оптимизированными параметрами
    if docker ps | grep -q mirai-ecosystem-api; then
        docker restart mirai-ecosystem-api
        log "API перезапущен"
    fi
    
    # Оптимизация Node.js приложения
    if pgrep -f "node.*trading" > /dev/null; then
        # Устанавливаем переменные окружения для оптимизации
        export NODE_ENV=production
        export UV_THREADPOOL_SIZE=16
        export NODE_OPTIONS="--max-old-space-size=4096"
        log "Node.js оптимизирован"
    fi
}

# Создание отчета
create_performance_report() {
    log "📋 Создание отчета о производительности..."
    
    local report_file="/root/mirai-agent/reports/performance_$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "system_metrics": {
        "cpu_usage": "$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')",
        "memory_usage": "$(free | awk 'FNR==2{printf "%.1f", $3/($3+$4)*100}')",
        "load_average": "$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')",
        "disk_usage": "$(df / | awk 'NR==2 {print $5}')",
        "network_connections": "$(netstat -an | wc -l)"
    },
    "docker_stats": {
        "containers_running": "$(docker ps --format 'table {{.Names}}' | wc -l)",
        "images_count": "$(docker images | wc -l)",
        "volumes_count": "$(docker volume ls | wc -l)"
    },
    "optimizations_applied": [
        "system_parameters",
        "docker_configuration",
        "database_optimization",
        "web_server_optimization"
    ]
}
EOF

    log "✅ Отчет сохранен: $report_file"
}

# Основная функция
main() {
    log "Начинаем оптимизацию производительности..."
    log "Текущие метрики: $(get_system_metrics)"
    
    optimize_system
    optimize_docker
    optimize_database
    optimize_web
    monitor_processes
    optimize_applications
    create_performance_report
    
    log "Метрики после оптимизации: $(get_system_metrics)"
    log "🎉 Оптимизация производительности завершена!"
}

# Запуск
main