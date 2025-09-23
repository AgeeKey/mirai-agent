#!/bin/bash

# Mirai Monitoring System
# Система мониторинга с автоматическими алертами

set -e

echo "📊 Развертывание системы мониторинга Mirai"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Установка Prometheus
setup_prometheus() {
    log "🔥 Настройка Prometheus..."
    
    mkdir -p /root/mirai-agent/monitoring/{prometheus,grafana,alertmanager}
    
    # Конфигурация Prometheus
    cat > /root/mirai-agent/monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'mirai-ecosystem'
    static_configs:
      - targets: ['localhost:8001', 'localhost:8002']
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'mirai-system'
    static_configs:
      - targets: ['localhost:9100']
    
  - job_name: 'mirai-nginx'
    static_configs:
      - targets: ['localhost:9113']

  - job_name: 'mirai-postgres'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'mirai-redis'
    static_configs:
      - targets: ['localhost:9121']
EOF

    # Правила алертов
    cat > /root/mirai-agent/monitoring/prometheus/alert_rules.yml << 'EOF'
groups:
  - name: mirai_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Высокий уровень ошибок в API"
          description: "{{ $labels.job }} имеет {{ $value }} ошибок в секунду"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Высокое время ответа API"
          description: "95% квантиль времени ответа: {{ $value }}s"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Сервис недоступен"
          description: "{{ $labels.job }} недоступен"

      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Высокая загрузка CPU"
          description: "CPU загружен на {{ $value }}%"

      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Высокое использование памяти"
          description: "Память используется на {{ $value }}%"

      - alert: DiskSpaceLow
        expr: (1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100 > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Мало места на диске"
          description: "Диск заполнен на {{ $value }}%"
EOF

    log "✅ Prometheus настроен"
}

# Настройка Alertmanager
setup_alertmanager() {
    log "🚨 Настройка Alertmanager..."
    
    cat > /root/mirai-agent/monitoring/alertmanager/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@aimirai.online'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:8001/api/alerts'
        send_resolved: true

  - name: 'telegram'
    webhook_configs:
      - url: 'http://localhost:8001/api/telegram/alert'
        send_resolved: true
EOF

    log "✅ Alertmanager настроен"
}

# Настройка Grafana
setup_grafana() {
    log "📈 Настройка Grafana..."
    
    # Datasources
    cat > /root/mirai-agent/monitoring/grafana/datasources.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    isDefault: true
    access: proxy
EOF

    # Dashboard конфигурация
    cat > /root/mirai-agent/monitoring/grafana/dashboard.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Mirai Ecosystem Dashboard",
    "tags": ["mirai"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "API Requests Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "System Resources",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "CPU Usage %"
          },
          {
            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
            "legendFormat": "Memory Usage %"
          }
        ],
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "5s"
  }
}
EOF

    log "✅ Grafana настроен"
}

# Docker Compose для мониторинга
create_monitoring_compose() {
    log "🐳 Создание Docker Compose для мониторинга..."
    
    cat > /root/mirai-agent/monitoring/docker-compose.monitoring.yml << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: mirai-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:latest
    container_name: mirai-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager:/etc/alertmanager
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: mirai-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: mirai-node-exporter
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|host|etc)($$|/)'
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    restart: unless-stopped

  nginx-exporter:
    image: nginx/nginx-prometheus-exporter:latest
    container_name: mirai-nginx-exporter
    command:
      - '-nginx.scrape-uri=http://nginx:8080/nginx_status'
    ports:
      - "9113:9113"
    restart: unless-stopped

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: mirai-postgres-exporter
    environment:
      - DATA_SOURCE_NAME=postgresql://mirai:password@postgres:5432/mirai_production?sslmode=disable
    ports:
      - "9187:9187"
    restart: unless-stopped

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: mirai-redis-exporter
    environment:
      - REDIS_ADDR=redis://redis:6379
    ports:
      - "9121:9121"
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:

networks:
  default:
    external:
      name: mirai-ecosystem
EOF

    log "✅ Docker Compose для мониторинга создан"
}

# Скрипт для запуска мониторинга
create_monitoring_script() {
    log "🚀 Создание скрипта запуска мониторинга..."
    
    cat > /root/mirai-agent/scripts/start-monitoring.sh << 'EOF'
#!/bin/bash

echo "🚀 Запуск системы мониторинга Mirai"

# Переходим в директорию мониторинга
cd /root/mirai-agent/monitoring

# Запускаем мониторинг
docker-compose -f docker-compose.monitoring.yml up -d

# Ждем запуска сервисов
echo "Ждем запуска сервисов..."
sleep 30

# Проверяем статус
check_service() {
    local service=$1
    local port=$2
    
    if curl -s http://localhost:$port > /dev/null; then
        echo "✅ $service работает"
    else
        echo "❌ $service не отвечает"
    fi
}

echo "Проверка сервисов мониторинга:"
check_service "Prometheus" "9090"
check_service "Grafana" "3000"
check_service "Alertmanager" "9093"
check_service "Node Exporter" "9100"

echo ""
echo "🎉 Мониторинг запущен!"
echo "Grafana: http://localhost:3000 (admin/admin123)"
echo "Prometheus: http://localhost:9090"
echo "Alertmanager: http://localhost:9093"
EOF

    chmod +x /root/mirai-agent/scripts/start-monitoring.sh
    
    log "✅ Скрипт запуска создан"
}

# Обновление API для метрик
add_metrics_to_api() {
    log "📊 Добавление метрик в API..."
    
    cat > /root/mirai-agent/monitoring_middleware.py << 'EOF'
import time
import asyncio
from datetime import datetime
from typing import Dict, List
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import psutil

# Метрики Prometheus
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active connections')
SYSTEM_CPU = Gauge('system_cpu_percent', 'CPU usage percentage')
SYSTEM_MEMORY = Gauge('system_memory_percent', 'Memory usage percentage')
SYSTEM_DISK = Gauge('system_disk_percent', 'Disk usage percentage')

class MonitoringMiddleware:
    def __init__(self, app):
        self.app = app
        # Запускаем фоновую задачу для сбора системных метрик
        asyncio.create_task(self.collect_system_metrics())
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Увеличиваем счетчик активных соединений
        ACTIVE_CONNECTIONS.inc()
        
        start_time = time.time()
        request = Request(scope, receive)
        
        # Обработка запроса
        response_sent = False
        
        async def send_wrapper(message):
            nonlocal response_sent
            if message["type"] == "http.response.start":
                response_sent = True
                status_code = message["status"]
                
                # Записываем метрики
                duration = time.time() - start_time
                REQUEST_DURATION.observe(duration)
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status=status_code
                ).inc()
                
                ACTIVE_CONNECTIONS.dec()
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
    
    async def collect_system_metrics(self):
        """Собираем системные метрики каждые 15 секунд"""
        while True:
            try:
                # CPU
                cpu_percent = psutil.cpu_percent(interval=1)
                SYSTEM_CPU.set(cpu_percent)
                
                # Memory
                memory = psutil.virtual_memory()
                SYSTEM_MEMORY.set(memory.percent)
                
                # Disk
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                SYSTEM_DISK.set(disk_percent)
                
            except Exception as e:
                print(f"Ошибка сбора метрик: {e}")
            
            await asyncio.sleep(15)

# Функция для добавления метрик в FastAPI
def add_metrics_endpoint(app):
    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    
    @app.post("/api/alerts")
    async def receive_alert(alert_data: dict):
        """Endpoint для получения алертов от Alertmanager"""
        print(f"Получен алерт: {alert_data}")
        # Здесь можно добавить логику отправки в Telegram или другие каналы
        return {"status": "received"}

# Health check с детальной информацией
def add_health_check(app):
    @app.get("/health/detailed")
    async def detailed_health():
        try:
            # Проверяем системные ресурсы
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Проверяем подключение к базе данных
            # (добавить проверку когда будет БД)
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": (disk.used / disk.total) * 100,
                    "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                },
                "services": {
                    "api": "healthy",
                    "database": "checking...",  # будет обновлено
                    "redis": "checking..."      # будет обновлено
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
EOF

    log "✅ Middleware для метрик создан"
}

# Основная функция
main() {
    log "Развертывание системы мониторинга..."
    
    setup_prometheus
    setup_alertmanager
    setup_grafana
    create_monitoring_compose
    create_monitoring_script
    add_metrics_to_api
    
    log "🎉 Система мониторинга готова!"
    log ""
    log "Следующие шаги:"
    log "1. Запустите мониторинг: /root/mirai-agent/scripts/start-monitoring.sh"
    log "2. Обновите API для добавления метрик"
    log "3. Настройте алерты в Telegram"
    log "4. Доступ к Grafana: http://localhost:3000 (admin/admin123)"
}

# Запуск
main