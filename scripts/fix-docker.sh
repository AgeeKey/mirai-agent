#!/bin/bash

# 🔧 Mirai Agent - Исправление Docker проблем
# Комплексное исправление Docker daemon

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}   MIRAI AGENT - ИСПРАВЛЕНИЕ DOCKER   ${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

# 1. Остановка всех Docker процессов
echo -e "${BLUE}🛑 Остановка Docker процессов${NC}"
echo "----------------------------------------"
sudo systemctl stop docker.service docker.socket containerd.service 2>/dev/null || true
sudo pkill dockerd 2>/dev/null || true
sudo pkill containerd 2>/dev/null || true
echo -e "${GREEN}✅${NC} Процессы остановлены"
echo ""

# 2. Очистка проблемных файлов
echo -e "${BLUE}🧹 Очистка проблемных файлов${NC}"
echo "----------------------------------------"

# Удаляем lock файлы
sudo rm -f /var/lib/docker/overlay2/.tmp* 2>/dev/null || true
sudo rm -f /var/lib/docker/network/files/local-kv.db.lock 2>/dev/null || true

# Удаляем поврежденные overlay2 ссылки
echo "Очистка overlay2 ссылок..."
sudo find /var/lib/docker/overlay2 -name "link" -delete 2>/dev/null || true

# Очистка containerd
sudo rm -rf /var/lib/containerd/io.containerd.runtime.v2.task/* 2>/dev/null || true

echo -e "${GREEN}✅${NC} Проблемные файлы очищены"
echo ""

# 3. Проверка конфигурации Docker
echo -e "${BLUE}⚙️ Проверка конфигурации Docker${NC}"
echo "----------------------------------------"

# Создаем правильный daemon.json
sudo mkdir -p /etc/docker
cat << 'EOF' | sudo tee /etc/docker/daemon.json > /dev/null
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "live-restore": true
}
EOF

echo -e "${GREEN}✅${NC} Конфигурация Docker обновлена"
echo ""

# 4. Перезагрузка systemd и запуск containerd
echo -e "${BLUE}🔄 Перезапуск сервисов${NC}"
echo "----------------------------------------"

sudo systemctl daemon-reload
sudo systemctl enable containerd.service
sudo systemctl start containerd.service

# Ждем запуска containerd
sleep 3

if systemctl is-active --quiet containerd; then
    echo -e "${GREEN}✅${NC} containerd запущен"
else
    echo -e "${RED}❌${NC} containerd не запустился"
    sudo journalctl -u containerd.service --lines=10 --no-pager
    exit 1
fi
echo ""

# 5. Запуск Docker
echo -e "${BLUE}🚀 Запуск Docker${NC}"
echo "----------------------------------------"

sudo systemctl enable docker.service docker.socket
sudo systemctl start docker.service

# Ждем запуска Docker
sleep 5

if systemctl is-active --quiet docker; then
    echo -e "${GREEN}✅${NC} Docker daemon запущен"
else
    echo -e "${RED}❌${NC} Docker не запустился"
    echo "Проверяем логи..."
    sudo journalctl -u docker.service --lines=10 --no-pager
    
    # Пробуем альтернативный способ
    echo ""
    echo "Пытаемся запустить вручную..."
    sudo dockerd --debug --storage-driver=overlay2 &
    DOCKER_PID=$!
    sleep 3
    
    if kill -0 $DOCKER_PID 2>/dev/null; then
        echo -e "${YELLOW}⚠️${NC} Docker запущен вручную (PID: $DOCKER_PID)"
        echo "Останавливаем и пробуем через systemctl..."
        sudo kill $DOCKER_PID
        sleep 2
        sudo systemctl start docker
    fi
fi
echo ""

# 6. Тестирование Docker
echo -e "${BLUE}🧪 Тестирование Docker${NC}"
echo "----------------------------------------"

if docker version >/dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Docker client работает"
    
    # Тест простого контейнера
    echo "Тестируем запуск контейнера..."
    if timeout 30 docker run --rm hello-world >/dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} Контейнеры запускаются корректно"
    else
        echo -e "${YELLOW}⚠️${NC} Проблемы с запуском контейнеров"
    fi
    
    # Показываем информацию
    echo ""
    echo "Docker информация:"
    docker info --format "{{.ServerVersion}}" | head -1
    docker info --format "Storage Driver: {{.Driver}}"
    
else
    echo -e "${RED}❌${NC} Docker client не работает"
    exit 1
fi
echo ""

# 7. Очистка системы
echo -e "${BLUE}🧹 Очистка Docker системы${NC}"
echo "----------------------------------------"

# Удаляем неиспользуемые ресурсы
docker system prune -f --volumes 2>/dev/null || true
echo -e "${GREEN}✅${NC} Система очищена"
echo ""

# 8. Проверка состояния Mirai контейнеров
echo -e "${BLUE}📦 Проверка Mirai контейнеров${NC}"
echo "----------------------------------------"

cd /root/mirai-agent

# Проверяем старые контейнеры
echo "Существующие контейнеры:"
docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -E "(mirai|infra)" || echo "Нет Mirai контейнеров"
echo ""

# 9. Финальная проверка
echo -e "${BLUE}✅ ФИНАЛЬНАЯ ПРОВЕРКА${NC}"
echo "----------------------------------------"

services=("docker" "containerd")
all_good=true

for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        echo -e "${GREEN}✅${NC} $service активен"
    else
        echo -e "${RED}❌${NC} $service неактивен"
        all_good=false
    fi
done

if $all_good; then
    echo ""
    echo -e "${GREEN}🎉 Docker полностью исправлен и готов к работе!${NC}"
    echo ""
    echo "Следующие шаги:"
    echo "1. cd /root/mirai-agent"
    echo "2. ./scripts/analyze-current-state.sh (повторная проверка)"
    echo "3. ./scripts/phase1-prepare.sh (начало развертывания AI)"
else
    echo ""
    echo -e "${RED}❌ Остались проблемы с Docker${NC}"
    echo "Обратитесь к системному администратору"
fi

echo ""
echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}      ИСПРАВЛЕНИЕ ЗАВЕРШЕНО           ${NC}"
echo -e "${BLUE}=======================================${NC}"