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
