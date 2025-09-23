#!/bin/bash

# Mirai Agent - Запуск системы мониторинга
# Этот скрипт запускает полный стек мониторинга: Prometheus, Grafana, AlertManager

set -e

echo "🚀 Запуск системы мониторинга Mirai Agent..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Переход в директорию мониторинга
cd "$(dirname "$0")"
MONITORING_DIR=$(pwd)

log "Директория мониторинга: $MONITORING_DIR"

# Проверка зависимостей
if ! command -v docker &> /dev/null; then
    error "Docker не установлен. Установите Docker и повторите попытку."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose не установлен. Установите Docker Compose и повторите попытку."
    exit 1
fi

# Создание необходимых директорий
log "Создание директорий..."
mkdir -p prometheus grafana alertmanager logs data

# Копирование конфигураций
log "Настройка конфигураций..."
cp prometheus.yml prometheus/
cp alert_rules.yml prometheus/
cp alertmanager.yml alertmanager/

# Проверка портов
log "Проверка доступности портов..."
check_port() {
    if netstat -tuln | grep -q ":$1 "; then
        warning "Порт $1 уже используется"
        return 1
    fi
    return 0
}

PORTS=(9090 9091 9093 3001 8080 9100)
for port in "${PORTS[@]}"; do
    if ! check_port $port; then
        warning "Порт $port занят, возможны конфликты"
    fi
done

# Остановка предыдущих контейнеров
log "Остановка предыдущих контейнеров мониторинга..."
docker-compose -f docker-compose.monitoring.yml down --remove-orphans 2>/dev/null || true

# Очистка старых образов (опционально)
if [[ "$1" == "--clean" ]]; then
    log "Очистка старых образов..."
    docker system prune -f
fi

# Запуск системы мониторинга
log "Запуск контейнеров мониторинга..."
docker-compose -f docker-compose.monitoring.yml up -d

# Ожидание готовности сервисов
log "Ожидание готовности сервисов..."

wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s "$url" > /dev/null 2>&1; then
            log "✅ $name готов"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    error "❌ $name не удалось запустить"
    return 1
}

echo -n "Ожидание Prometheus"
wait_for_service "http://localhost:9091/api/v1/status/config" "Prometheus"

echo -n "Ожидание Grafana"
wait_for_service "http://localhost:3001/api/health" "Grafana"

echo -n "Ожидание AlertManager"
wait_for_service "http://localhost:9093/-/ready" "AlertManager"

# Запуск metrics exporter
log "Запуск Mirai Metrics Exporter..."
python3 metrics_exporter.py &
METRICS_PID=$!
echo $METRICS_PID > logs/metrics_exporter.pid

# Проверка доступности метрик
sleep 5
if curl -s "http://localhost:9090/metrics" > /dev/null; then
    log "✅ Metrics Exporter запущен"
else
    warning "❌ Metrics Exporter может быть недоступен"
fi

# Импорт дашбордов
log "Импорт дашбордов в Grafana..."
sleep 10  # Ждем полной загрузки Grafana

import_dashboard() {
    local file=$1
    local name=$2
    
    if [[ -f "$file" ]]; then
        curl -X POST \
            -H "Content-Type: application/json" \
            -u admin:mirai2024! \
            -d @"$file" \
            "http://localhost:3001/api/dashboards/db" 2>/dev/null
        
        if [[ $? -eq 0 ]]; then
            log "✅ Дашборд $name импортирован"
        else
            warning "❌ Не удалось импортировать дашборд $name"
        fi
    fi
}

import_dashboard "grafana_dashboard_trading.json" "Trading Dashboard"
import_dashboard "grafana_dashboard_ai.json" "AI Performance Dashboard"

# Финальная проверка
log "Финальная проверка системы..."

echo ""
echo -e "${BLUE}🎯 СИСТЕМА МОНИТОРИНГА ЗАПУЩЕНА${NC}"
echo ""
echo -e "${GREEN}📊 Доступные сервисы:${NC}"
echo "  • Prometheus:   http://localhost:9091"
echo "  • Grafana:      http://localhost:3001 (admin/mirai2024!)"
echo "  • AlertManager: http://localhost:9093"
echo "  • Node Exporter: http://localhost:9100"
echo "  • cAdvisor:     http://localhost:8080"
echo ""
echo -e "${GREEN}📈 Основные дашборды:${NC}"
echo "  • Trading Dashboard: P&L, позиции, торговая активность"
echo "  • AI Performance: AI метрики, производительность, uptime"
echo ""
echo -e "${GREEN}🚨 Алерты настроены для:${NC}"
echo "  • Критическая просадка (>10%)"
echo "  • Высокая просадка (>5%)"
echo "  • Низкий винрейт (<45%)"
echo "  • Отсутствие торговли (>2ч)"
echo "  • AI недоступен"
echo "  • Высокое использование ресурсов"
echo ""
echo -e "${YELLOW}📋 Логи:${NC}"
echo "  • Metrics Exporter PID: $METRICS_PID (сохранен в logs/metrics_exporter.pid)"
echo "  • Docker logs: docker-compose -f docker-compose.monitoring.yml logs -f"
echo ""
echo -e "${GREEN}✅ Мониторинг готов к работе!${NC}"

# Создание файла статуса
cat > logs/monitoring_status.json << EOF
{
  "status": "running",
  "started_at": "$(date -Iseconds)",
  "metrics_exporter_pid": $METRICS_PID,
  "services": {
    "prometheus": "http://localhost:9091",
    "grafana": "http://localhost:3001",
    "alertmanager": "http://localhost:9093",
    "node_exporter": "http://localhost:9100",
    "cadvisor": "http://localhost:8080"
  },
  "credentials": {
    "grafana_user": "admin",
    "grafana_password": "mirai2024!"
  }
}
EOF

log "Статус сохранен в logs/monitoring_status.json"