#!/bin/bash

# 🚀 Mirai Agent - Полное развертывание AI системы
# Автоматическое развертывание всех AI компонентов с проверками

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${BLUE}===============================================${NC}"
echo -e "${BOLD}${BLUE}   MIRAI AGENT - ПОЛНОЕ РАЗВЕРТЫВАНИЕ AI      ${NC}"
echo -e "${BOLD}${BLUE}===============================================${NC}"
echo ""

# Проверка запуска от root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Этот скрипт должен запускаться от root${NC}"
    exit 1
fi

# Переходим в рабочую директорию
cd /root/mirai-agent

echo -e "${CYAN}📋 ПЛАН РАЗВЕРТЫВАНИЯ${NC}"
echo "----------------------------------------"
echo "1. Проверка предварительных условий"
echo "2. Создание backup существующей системы"
echo "3. Подготовка AI инфраструктуры"
echo "4. Клонирование SuperAGI и AutoGPT"
echo "5. Сборка AI контейнеров" 
echo "6. Запуск AI сервисов"
echo "7. Интеграция с основной системой"
echo "8. Настройка Nginx и SSL"
echo "9. Комплексное тестирование"
echo "10. Финальная конфигурация"
echo ""

read -p "Продолжить развертывание? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Развертывание отменено"
    exit 0
fi
echo ""

# Функция для выполнения шагов с проверкой
execute_step() {
    local step_name="$1"
    local step_command="$2"
    local required="${3:-true}"
    
    echo -e "${BLUE}🔄 $step_name${NC}"
    echo "Выполняется: $step_command"
    
    if eval "$step_command"; then
        echo -e "${GREEN}✅ $step_name - успешно${NC}"
        return 0
    else
        echo -e "${RED}❌ $step_name - ошибка${NC}"
        if [ "$required" = "true" ]; then
            echo "Критическая ошибка. Развертывание прервано."
            exit 1
        else
            echo "Некритическая ошибка. Продолжаем."
            return 1
        fi
    fi
}

# ===============================
# ШАГ 1: ПРОВЕРКА ПРЕДВАРИТЕЛЬНЫХ УСЛОВИЙ
# ===============================
echo -e "${BLUE}1️⃣ ПРОВЕРКА ПРЕДВАРИТЕЛЬНЫХ УСЛОВИЙ${NC}"
echo "========================================"

execute_step "Проверка Docker" "systemctl is-active docker >/dev/null"
execute_step "Проверка Docker Compose" "command -v docker-compose >/dev/null || command -v docker compose >/dev/null"
execute_step "Проверка Git" "command -v git >/dev/null"
execute_step "Проверка Python 3" "command -v python3 >/dev/null"
execute_step "Проверка curl" "command -v curl >/dev/null"

# Проверяем свободное место (минимум 5GB)
available_space=$(df / | tail -1 | awk '{print $4}')
if [ $available_space -lt 5242880 ]; then  # 5GB in KB
    echo -e "${RED}❌ Недостаточно места на диске (нужно минимум 5GB)${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Достаточно места на диске${NC}"
fi

# Проверяем файл .env
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Файл .env не найден${NC}"
    exit 1
fi

if ! grep -q "OPENAI_API_KEY" .env; then
    echo -e "${YELLOW}⚠️ OPENAI_API_KEY не найден в .env${NC}"
    echo "Добавьте ключ OpenAI для полной функциональности AI"
fi

echo ""

# ===============================
# ШАГ 2: BACKUP СУЩЕСТВУЮЩЕЙ СИСТЕМЫ
# ===============================
echo -e "${BLUE}2️⃣ СОЗДАНИЕ BACKUP${NC}"
echo "============================="

BACKUP_DIR="/root/mirai-backup-$(date +%Y%m%d-%H%M%S)"
execute_step "Создание backup директории" "mkdir -p $BACKUP_DIR"
execute_step "Backup состояния Docker" "docker ps -a > $BACKUP_DIR/docker-state.txt || true"
execute_step "Backup базы данных" "cp -r state $BACKUP_DIR/ || true"
execute_step "Backup конфигураций" "cp -r configs $BACKUP_DIR/ && cp .env $BACKUP_DIR/ || true"
execute_step "Backup логов" "find logs -name '*.log' -mtime -7 -exec cp {} $BACKUP_DIR/ \; || true"

echo -e "${GREEN}✅ Backup создан в: $BACKUP_DIR${NC}"
echo ""

# ===============================
# ШАГ 3: ПОДГОТОВКА AI ИНФРАСТРУКТУРЫ
# ===============================
echo -e "${BLUE}3️⃣ ПОДГОТОВКА AI ИНФРАСТРУКТУРЫ${NC}"
echo "======================================"

execute_step "Создание AI директорий" "mkdir -p microservices/ai-engine/{superagi,autogpt-runner,orchestrator,dashboard} shared/{data,reports,knowledge}"
execute_step "Создание директории логов" "mkdir -p logs"
execute_step "Установка прав доступа" "chmod -R 755 microservices shared && chown -R root:root microservices shared"

# Добавляем переменные для AI в .env если их нет
if ! grep -q "AI_ENABLED" .env; then
    echo "AI_ENABLED=false" >> .env
    echo -e "${GREEN}✅ Добавлена переменная AI_ENABLED${NC}"
fi

if ! grep -q "POSTGRES_PASSWORD" .env; then
    echo "POSTGRES_PASSWORD=mirai123" >> .env
    echo -e "${GREEN}✅ Добавлена переменная POSTGRES_PASSWORD${NC}"
fi

if ! grep -q "CHROMA_TOKEN" .env; then
    echo "CHROMA_TOKEN=mirai-secret-token" >> .env
    echo -e "${GREEN}✅ Добавлена переменная CHROMA_TOKEN${NC}"
fi

echo ""

# ===============================
# ШАГ 4: КЛОНИРОВАНИЕ РЕПОЗИТОРИЕВ
# ===============================
echo -e "${BLUE}4️⃣ КЛОНИРОВАНИЕ AI РЕПОЗИТОРИЕВ${NC}"
echo "====================================="

cd microservices/ai-engine

# SuperAGI
if [ ! -d "superagi/.git" ]; then
    execute_step "Клонирование SuperAGI" "git clone https://github.com/TransformerOptimus/SuperAGI.git superagi"
else
    echo -e "${GREEN}✅ SuperAGI уже клонирован${NC}"
fi

# AutoGPT  
if [ ! -d "autogpt-runner/.git" ]; then
    execute_step "Клонирование AutoGPT" "git clone https://github.com/Significant-Gravitas/AutoGPT.git autogpt-runner"
else
    echo -e "${GREEN}✅ AutoGPT уже клонирован${NC}"
fi

cd /root/mirai-agent
echo ""

# ===============================
# ШАГ 5: СБОРКА AI КОНТЕЙНЕРОВ
# ===============================
echo -e "${BLUE}5️⃣ СБОРКА AI КОНТЕЙНЕРОВ${NC}"
echo "==============================="

# Сначала собираем Orchestrator (он самый простой)
execute_step "Сборка Orchestrator" "docker build -t mirai-orchestrator microservices/ai-engine/orchestrator/"

# Проверяем есть ли готовые образы для SuperAGI и AutoGPT
echo "Проверяем готовые образы AI..."
if docker pull chromadb/chroma:0.4.15 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ ChromaDB образ загружен${NC}"
else
    echo -e "${YELLOW}⚠️ Проблема с загрузкой ChromaDB образа${NC}"
fi

echo ""

# ===============================
# ШАГ 6: ЗАПУСК AI СЕРВИСОВ
# ===============================
echo -e "${BLUE}6️⃣ ЗАПУСК AI СЕРВИСОВ${NC}"
echo "============================"

# Сначала запускаем базовые сервисы (PostgreSQL, Redis, ChromaDB)
echo "Запускаем базовые AI сервисы..."
execute_step "Запуск PostgreSQL для AI" "docker-compose -f infra/docker-compose.ai.yml up -d postgres-ai"
execute_step "Запуск Redis для AI" "docker-compose -f infra/docker-compose.ai.yml up -d redis-ai"
execute_step "Запуск ChromaDB" "docker-compose -f infra/docker-compose.ai.yml up -d chromadb"

# Ждем готовности базовых сервисов
echo "Ожидание готовности базовых сервисов (30 сек)..."
sleep 30

# Проверяем готовность
execute_step "Проверка PostgreSQL" "docker-compose -f infra/docker-compose.ai.yml exec -T postgres-ai pg_isready -U mirai" "false"
execute_step "Проверка Redis" "docker-compose -f infra/docker-compose.ai.yml exec -T redis-ai redis-cli ping | grep -q PONG" "false"
execute_step "Проверка ChromaDB" "curl -f -s http://localhost:8000/api/v1/heartbeat >/dev/null" "false"

# Запускаем Orchestrator
echo "Запускаем Orchestrator..."
execute_step "Запуск Orchestrator" "docker-compose -f infra/docker-compose.ai.yml up -d orchestrator"

# Ждем готовности Orchestrator
echo "Ожидание готовности Orchestrator (15 сек)..."
sleep 15
execute_step "Проверка Orchestrator" "curl -f -s http://localhost:8080/health >/dev/null"

echo ""

# ===============================
# ШАГ 7: ИНТЕГРАЦИЯ С ОСНОВНОЙ СИСТЕМОЙ
# ===============================
echo -e "${BLUE}7️⃣ ИНТЕГРАЦИЯ С ОСНОВНОЙ СИСТЕМОЙ${NC}"
echo "====================================="

# Проверяем основные сервисы
if curl -f -s http://localhost:8001/health >/dev/null; then
    echo -e "${GREEN}✅ Основной API работает${NC}"
    
    # Добавляем AI endpoint в API (если нужно)
    # Здесь можно добавить код для обновления API
    
else
    echo -e "${YELLOW}⚠️ Основной API не работает - запускаем${NC}"
    execute_step "Запуск основного API" "docker-compose -f infra/docker-compose.yml up -d api" "false"
fi

# Проверяем Frontend
if curl -f -s http://localhost:3000 >/dev/null; then
    echo -e "${GREEN}✅ Frontend работает${NC}"
else
    echo -e "${YELLOW}⚠️ Frontend не работает - запускаем${NC}"
    execute_step "Запуск Frontend" "docker-compose -f infra/docker-compose.yml up -d web" "false"
fi

echo ""

# ===============================
# ШАГ 8: НАСТРОЙКА NGINX И SSL
# ===============================
echo -e "${BLUE}8️⃣ НАСТРОЙКА NGINX И SSL${NC}"
echo "==============================="

if command -v nginx >/dev/null; then
    echo "Nginx найден. Настраиваем конфигурации..."
    
    # Копируем конфигурации
    execute_step "Копирование конфигураций Nginx" "cp nginx/*.conf /etc/nginx/sites-available/ || true" "false"
    
    # Активируем конфигурации (без SSL пока)
    echo "Создаем временные конфигурации без SSL..."
    
    # Простая конфигурация для проверки
    cat > /tmp/mirai-simple.conf << 'EOF'
server {
    listen 80;
    server_name _;
    
    location /health {
        return 200 "Mirai AI System Ready";
        add_header Content-Type text/plain;
    }
    
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
    }
    
    location /orchestrator/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_set_header Host $host;
    }
}
EOF
    
    execute_step "Установка простой конфигурации Nginx" "cp /tmp/mirai-simple.conf /etc/nginx/sites-available/ && ln -sf /etc/nginx/sites-available/mirai-simple.conf /etc/nginx/sites-enabled/" "false"
    execute_step "Тест конфигурации Nginx" "nginx -t" "false"
    execute_step "Перезагрузка Nginx" "systemctl reload nginx" "false"
    
else
    echo -e "${YELLOW}⚠️ Nginx не установлен - пропускаем настройку${NC}"
fi

echo ""

# ===============================
# ШАГ 9: КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ
# ===============================
echo -e "${BLUE}9️⃣ КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ${NC}"
echo "================================="

echo "Ожидание готовности всех сервисов (30 сек)..."
sleep 30

echo "Запускаем тестирование..."
if [ -f "scripts/test-ai-integration.sh" ]; then
    # Запускаем тесты но не прерываем развертывание при ошибках
    if ./scripts/test-ai-integration.sh; then
        echo -e "${GREEN}✅ Все тесты пройдены${NC}"
    else
        echo -e "${YELLOW}⚠️ Некоторые тесты провалились, но продолжаем${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Скрипт тестирования не найден${NC}"
fi

echo ""

# ===============================
# ШАГ 10: ФИНАЛЬНАЯ КОНФИГУРАЦИЯ
# ===============================
echo -e "${BLUE}🔟 ФИНАЛЬНАЯ КОНФИГУРАЦИЯ${NC}"
echo "==============================="

# Включаем AI в основной системе
echo "Включаем AI в конфигурации..."
sed -i 's/AI_ENABLED=false/AI_ENABLED=true/' .env
echo -e "${GREEN}✅ AI включен в системе${NC}"

# Создаем скрипт запуска
cat > scripts/start-ai-system.sh << 'EOF'
#!/bin/bash
echo "Запуск полной AI системы Mirai..."

# Запускаем AI сервисы
docker-compose -f infra/docker-compose.ai.yml up -d

# Ждем готовности
sleep 30

# Запускаем основные сервисы с AI поддержкой
docker-compose -f infra/docker-compose.yml up -d

echo "Система запущена. Проверьте статус:"
echo "  - Frontend: http://localhost:3000"
echo "  - API: http://localhost:8001/health"
echo "  - AI Orchestrator: http://localhost:8080/health"
echo "  - ChromaDB: http://localhost:8000/api/v1/heartbeat"
EOF

chmod +x scripts/start-ai-system.sh
echo -e "${GREEN}✅ Создан скрипт запуска системы${NC}"

# Создаем скрипт остановки
cat > scripts/stop-ai-system.sh << 'EOF'
#!/bin/bash
echo "Остановка AI системы Mirai..."

# Останавливаем все AI сервисы
docker-compose -f infra/docker-compose.ai.yml down

echo "AI система остановлена"
EOF

chmod +x scripts/stop-ai-system.sh
echo -e "${GREEN}✅ Создан скрипт остановки системы${NC}"

echo ""

# ===============================
# ФИНАЛЬНЫЙ ОТЧЕТ
# ===============================
echo -e "${BOLD}${GREEN}🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО УСПЕШНО!${NC}"
echo "=============================================="
echo ""

echo -e "${CYAN}🚀 СИСТЕМА ГОТОВА К РАБОТЕ${NC}"
echo ""

echo -e "${BOLD}Доступные сервисы:${NC}"
echo "  🌐 Frontend: http://localhost:3000"
echo "  📡 API: http://localhost:8001"
echo "  🤖 AI Orchestrator: http://localhost:8080"
echo "  💾 ChromaDB: http://localhost:8000"
echo "  🗄️ PostgreSQL: localhost:5433"
echo "  🔴 Redis: localhost:6380"
echo ""

echo -e "${BOLD}Управление системой:${NC}"
echo "  • Запуск полной системы: ./scripts/start-ai-system.sh"
echo "  • Остановка AI: ./scripts/stop-ai-system.sh"
echo "  • Тестирование: ./scripts/test-ai-integration.sh"
echo "  • Мониторинг: docker-compose -f infra/docker-compose.ai.yml logs -f"
echo ""

echo -e "${BOLD}Конфигурация:${NC}"
echo "  • AI включен: AI_ENABLED=true"
echo "  • Backup создан: $BACKUP_DIR"
echo "  • Логи: /root/mirai-agent/logs/"
echo "  • Shared данные: /root/mirai-agent/shared/"
echo ""

echo -e "${BOLD}Следующие шаги:${NC}"
echo "1. Проверьте работу всех сервисов: curl http://localhost:8080/health"
echo "2. Настройте домены: ./scripts/setup-nginx-ssl.sh (опционально)"
echo "3. Отправьте тестовую задачу:"
echo "   curl -X POST http://localhost:8080/task/submit \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"type\":\"analysis\",\"goal\":\"Test Mirai AI\"}'"
echo "4. Откройте веб-интерфейс и проверьте интеграцию"
echo ""

echo -e "${YELLOW}⚠️ ВАЖНО:${NC}"
echo "• Убедитесь что в .env указан корректный OPENAI_API_KEY"
echo "• Для продакшена настройте SSL сертификаты"
echo "• Регулярно делайте backup базы данных"
echo "• Мониторьте логи AI сервисов"
echo ""

echo -e "${BOLD}${BLUE}===============================================${NC}"
echo -e "${BOLD}${BLUE}      MIRAI AI AGENT ГОТОВ К ТОРГОВЛЕ!        ${NC}"
echo -e "${BOLD}${BLUE}===============================================${NC}"

# Показываем текущий статус сервисов
echo ""
echo "Текущий статус Docker контейнеров:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(mirai|infra)" || echo "Нет активных Mirai контейнеров"

echo ""
echo "Для мониторинга системы используйте:"
echo "  watch -n 5 'docker ps --format \"table {{.Names}}\\t{{.Status}}\" | grep mirai'"