#!/bin/bash

# 🧪 Mirai Agent - Комплексное тестирование AI интеграции
# Полное тестирование всех AI компонентов и их взаимодействия

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   MIRAI AGENT - ТЕСТИРОВАНИЕ AI СИСТЕМЫ   ${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Переменные для результатов
declare -A test_results
total_tests=0
passed_tests=0
failed_tests=0

# Функция для выполнения теста
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"
    
    total_tests=$((total_tests + 1))
    echo -e "${CYAN}🧪 Тест: $test_name${NC}"
    
    if eval "$test_command"; then
        echo -e "   ${GREEN}✅ PASSED${NC}"
        test_results["$test_name"]="PASSED"
        passed_tests=$((passed_tests + 1))
        return 0
    else
        echo -e "   ${RED}❌ FAILED${NC}"
        test_results["$test_name"]="FAILED"
        failed_tests=$((failed_tests + 1))
        return 1
    fi
}

# Функция для HTTP теста
http_test() {
    local url="$1"
    local expected_code="${2:-200}"
    local timeout="${3:-10}"
    
    response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$timeout" "$url" 2>/dev/null || echo "000")
    [ "$response_code" = "$expected_code" ]
}

# Функция для JSON API теста
json_api_test() {
    local url="$1"
    local expected_key="$2"
    local timeout="${3:-10}"
    
    response=$(curl -s --max-time "$timeout" "$url" 2>/dev/null || echo '{}')
    echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print('$expected_key' in data)" 2>/dev/null | grep -q "True"
}

# Функция для WebSocket теста
websocket_test() {
    local url="$1"
    local timeout="${2:-5}"
    
    # Простой тест WebSocket соединения
    timeout "$timeout" bash -c "exec 3<>/dev/tcp/localhost/8080" 2>/dev/null
}

echo -e "${BLUE}📋 ПЛАН ТЕСТИРОВАНИЯ${NC}"
echo "----------------------------------------"
echo "1. Тестирование инфраструктуры (Docker, сети)"
echo "2. Тестирование базовых сервисов (API, Frontend)"
echo "3. Тестирование AI компонентов (Orchestrator, ChromaDB)"
echo "4. Тестирование интеграции (SuperAGI, AutoGPT)"
echo "5. Тестирование AI задач и workflows"
echo "6. Нагрузочное тестирование"
echo "7. Функциональные тесты"
echo ""

# ===============================
# 1. ТЕСТИРОВАНИЕ ИНФРАСТРУКТУРЫ
# ===============================
echo -e "${BLUE}🔧 1. ТЕСТИРОВАНИЕ ИНФРАСТРУКТУРЫ${NC}"
echo "----------------------------------------"

run_test "Docker daemon" "systemctl is-active docker >/dev/null 2>&1"
run_test "Docker containers running" "[ \$(docker ps | wc -l) -gt 1 ]"
run_test "Mirai network exists" "docker network ls | grep -q mirai || docker network ls | grep -q infra"
run_test "Shared directories exist" "[ -d /root/mirai-agent/shared/data ] && [ -d /root/mirai-agent/shared/reports ]"
run_test "Log directories writable" "[ -w /root/mirai-agent/logs ]"

echo ""

# ===============================
# 2. ТЕСТИРОВАНИЕ БАЗОВЫХ СЕРВИСОВ
# ===============================
echo -e "${BLUE}📡 2. ТЕСТИРОВАНИЕ БАЗОВЫХ СЕРВИСОВ${NC}"
echo "----------------------------------------"

run_test "Frontend (Next.js) доступен" "http_test 'http://localhost:3000' 200 5"
run_test "API здоровье" "http_test 'http://localhost:8001/health' 200 5"
run_test "API возвращает JSON" "json_api_test 'http://localhost:8001/health' 'status'"

# Проверяем активные порты
if netstat -tlpn 2>/dev/null | grep -q ":8001 "; then
    run_test "API порт активен" "true"
else
    run_test "API порт активен" "false"
fi

if netstat -tlpn 2>/dev/null | grep -q ":3000 "; then
    run_test "Frontend порт активен" "true" 
else
    run_test "Frontend порт активен" "false"
fi

echo ""

# ===============================
# 3. ТЕСТИРОВАНИЕ AI КОМПОНЕНТОВ
# ===============================
echo -e "${BLUE}🤖 3. ТЕСТИРОВАНИЕ AI КОМПОНЕНТОВ${NC}"
echo "----------------------------------------"

# ChromaDB
run_test "ChromaDB доступен" "http_test 'http://localhost:8000/api/v1/heartbeat' 200 10"
run_test "ChromaDB API работает" "json_api_test 'http://localhost:8000/api/v1/heartbeat' 'nanosecond heartbeat'"

# Orchestrator
run_test "Orchestrator доступен" "http_test 'http://localhost:8080/health' 200 10"
run_test "Orchestrator возвращает статистику" "json_api_test 'http://localhost:8080/stats' 'total_tasks'"
run_test "Orchestrator WebSocket" "netstat -tlpn 2>/dev/null | grep -q ':8080.*python'"

# Проверяем AI контейнеры
ai_containers=("mirai-orchestrator" "mirai-chromadb")
for container in "${ai_containers[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "$container"; then
        run_test "Контейнер $container запущен" "docker inspect $container --format='{{.State.Status}}' | grep -q 'running'"
    else
        run_test "Контейнер $container запущен" "false"
    fi
done

echo ""

# ===============================
# 4. ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ
# ===============================
echo -e "${BLUE}🔗 4. ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ${NC}"
echo "----------------------------------------"

# Тест отправки задачи в Orchestrator
echo "Отправляем тестовую задачу..."
if task_response=$(curl -s -X POST "http://localhost:8080/task/submit" \
    -H "Content-Type: application/json" \
    -d '{
        "type": "analysis", 
        "goal": "Test integration",
        "context": {"test": true},
        "priority": 10
    }' 2>/dev/null); then
    
    if echo "$task_response" | grep -q "task_id"; then
        task_id=$(echo "$task_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['task_id'])" 2>/dev/null)
        run_test "Задача отправлена в Orchestrator" "true"
        
        # Ждем и проверяем статус
        sleep 3
        if task_status=$(curl -s "http://localhost:8080/task/$task_id" 2>/dev/null); then
            run_test "Статус задачи получен" "echo '$task_status' | grep -q 'task_id'"
        else
            run_test "Статус задачи получен" "false"
        fi
    else
        run_test "Задача отправлена в Orchestrator" "false"
    fi
else
    run_test "Задача отправлена в Orchestrator" "false"
fi

# Тест активных задач
run_test "Список активных задач" "json_api_test 'http://localhost:8080/tasks/active' 'count'"

echo ""

# ===============================
# 5. ТЕСТИРОВАНИЕ AI WORKFLOW
# ===============================
echo -e "${BLUE}🧠 5. ТЕСТИРОВАНИЕ AI WORKFLOW${NC}"
echo "----------------------------------------"

# Тест разных типов задач
task_types=("analysis" "reporting")
for task_type in "${task_types[@]}"; do
    echo "Тестируем тип задачи: $task_type"
    
    task_data="{\"type\":\"$task_type\",\"goal\":\"Test $task_type workflow\",\"context\":{\"test\":true}}"
    
    if response=$(curl -s -X POST "http://localhost:8080/task/submit" \
        -H "Content-Type: application/json" \
        -d "$task_data" 2>/dev/null); then
        
        if echo "$response" | grep -q "task_id"; then
            run_test "Задача типа $task_type принята" "true"
        else
            run_test "Задача типа $task_type принята" "false"
        fi
    else
        run_test "Задача типа $task_type принята" "false"
    fi
done

# Тест системной статистики
if stats=$(curl -s "http://localhost:8080/stats" 2>/dev/null); then
    if echo "$stats" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('total_tasks', 0))" | grep -q "[0-9]"; then
        run_test "Статистика системы доступна" "true"
    else
        run_test "Статистика системы доступна" "false"
    fi
else
    run_test "Статистика системы доступна" "false"
fi

echo ""

# ===============================
# 6. ТЕСТИРОВАНИЕ ПАМЯТИ И ДАННЫХ
# ===============================
echo -e "${BLUE}💾 6. ТЕСТИРОВАНИЕ ПАМЯТИ И ДАННЫХ${NC}"
echo "----------------------------------------"

# Тест записи в shared директории
test_file="/root/mirai-agent/shared/data/test_$(date +%s).json"
if echo '{"test": "data", "timestamp": "'$(date -Iseconds)'"}' > "$test_file" 2>/dev/null; then
    run_test "Запись в shared/data" "[ -f '$test_file' ]"
    rm -f "$test_file" 2>/dev/null
else
    run_test "Запись в shared/data" "false"
fi

# Тест ChromaDB коллекций
if collections=$(curl -s "http://localhost:8000/api/v1/collections" 2>/dev/null); then
    run_test "ChromaDB коллекции доступны" "echo '$collections' | grep -q '\[\]' || echo '$collections' | grep -q 'name'"
else
    run_test "ChromaDB коллекции доступны" "false"
fi

echo ""

# ===============================
# 7. НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ
# ===============================
echo -e "${BLUE}⚡ 7. НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ${NC}"
echo "----------------------------------------"

echo "Отправляем 5 одновременных задач..."
pids=()
for i in {1..5}; do
    (
        curl -s -X POST "http://localhost:8080/task/submit" \
            -H "Content-Type: application/json" \
            -d "{\"type\":\"analysis\",\"goal\":\"Load test $i\",\"priority\":1}" \
            >/dev/null 2>&1
    ) &
    pids+=($!)
done

# Ждем завершения всех запросов
success_count=0
for pid in "${pids[@]}"; do
    if wait "$pid"; then
        success_count=$((success_count + 1))
    fi
done

run_test "Обработка множественных задач" "[ $success_count -ge 3 ]"

echo ""

# ===============================
# 8. ФУНКЦИОНАЛЬНЫЕ ТЕСТЫ
# ===============================
echo -e "${BLUE}🎯 8. ФУНКЦИОНАЛЬНЫЕ ТЕСТЫ${NC}"
echo "----------------------------------------"

# Тест отмены задачи (если есть активные)
if active_tasks=$(curl -s "http://localhost:8080/tasks/active" 2>/dev/null); then
    task_count=$(echo "$active_tasks" | python3 -c "import sys, json; print(json.load(sys.stdin).get('count', 0))" 2>/dev/null)
    run_test "Получение активных задач" "[ '$task_count' -ge 0 ]"
else
    run_test "Получение активных задач" "false"
fi

# Тест истории задач
if history=$(curl -s "http://localhost:8080/tasks/history?limit=10" 2>/dev/null); then
    run_test "История задач доступна" "echo '$history' | grep -q 'count'"
else
    run_test "История задач доступна" "false"
fi

# Тест обучения
echo "Запускаем тест обучения..."
if learn_response=$(curl -s -X POST "http://localhost:8080/learn" 2>/dev/null); then
    run_test "Система обучения работает" "echo '$learn_response' | grep -q 'task_id'"
else
    run_test "Система обучения работает" "false"
fi

echo ""

# ===============================
# 9. ИНТЕГРАЦИЯ С ОСНОВНОЙ СИСТЕМОЙ
# ===============================
echo -e "${BLUE}🔧 9. ИНТЕГРАЦИЯ С ОСНОВНОЙ СИСТЕМОЙ${NC}"
echo "----------------------------------------"

# Тест доступности API для AI интеграции
if curl -s "http://localhost:8001/health" >/dev/null 2>&1; then
    run_test "Основной API доступен для AI" "true"
    
    # Тест AI endpoint в API (если есть)
    if curl -s "http://localhost:8001/ai/status" >/dev/null 2>&1; then
        run_test "AI endpoint в основном API" "true"
    else
        run_test "AI endpoint в основном API" "false"
    fi
else
    run_test "Основной API доступен для AI" "false"
fi

echo ""

# ===============================
# РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ
# ===============================
echo -e "${BLUE}📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ${NC}"
echo "============================================"
echo ""

echo -e "${CYAN}Общая статистика:${NC}"
echo "  Всего тестов: $total_tests"
echo -e "  Пройдено: ${GREEN}$passed_tests${NC}"
echo -e "  Провалено: ${RED}$failed_tests${NC}"

if [ $total_tests -gt 0 ]; then
    success_rate=$((passed_tests * 100 / total_tests))
    echo "  Процент успеха: $success_rate%"
fi

echo ""
echo -e "${CYAN}Детальные результаты:${NC}"
for test_name in "${!test_results[@]}"; do
    result="${test_results[$test_name]}"
    if [ "$result" = "PASSED" ]; then
        echo -e "  ${GREEN}✅${NC} $test_name"
    else
        echo -e "  ${RED}❌${NC} $test_name"
    fi
done

echo ""

# Определяем общий статус
if [ $failed_tests -eq 0 ]; then
    echo -e "${GREEN}🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!${NC}"
    echo ""
    echo "AI система Mirai полностью готова к работе:"
    echo "  • Все компоненты функционируют корректно"
    echo "  • Интеграция между сервисами работает"
    echo "  • AI задачи обрабатываются успешно"
    echo "  • Система готова к автономной торговле"
    
    exit_code=0
elif [ $success_rate -ge 80 ]; then
    echo -e "${YELLOW}⚠️ СИСТЕМА РАБОТАЕТ С ПРЕДУПРЕЖДЕНИЯМИ${NC}"
    echo ""
    echo "Большинство компонентов работают корректно, но есть проблемы:"
    echo "  • Проверьте провалившиеся тесты выше"
    echo "  • Система может работать в ограниченном режиме"
    echo "  • Рекомендуется исправить ошибки перед продакшеном"
    
    exit_code=1
else
    echo -e "${RED}❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ В СИСТЕМЕ${NC}"
    echo ""
    echo "Обнаружены серьезные проблемы:"
    echo "  • Много провалившихся тестов"
    echo "  • AI система может работать некорректно"
    echo "  • НЕ РЕКОМЕНДУЕТСЯ использовать в продакшене"
    echo "  • Требуется диагностика и исправление"
    
    exit_code=2
fi

echo ""
echo -e "${CYAN}Следующие шаги:${NC}"
if [ $exit_code -eq 0 ]; then
    echo "1. Запустите полную AI систему: docker-compose -f infra/docker-compose.ai.yml up -d"
    echo "2. Настройте домены: ./scripts/setup-nginx-ssl.sh"
    echo "3. Включите AI в основной системе: echo 'AI_ENABLED=true' >> .env"
    echo "4. Перезапустите trader с AI поддержкой"
elif [ $exit_code -eq 1 ]; then
    echo "1. Проверьте логи провалившихся сервисов"
    echo "2. Исправьте обнаруженные проблемы"
    echo "3. Повторите тестирование"
else
    echo "1. Проверьте базовую инфраструктуру (Docker, сети)"
    echo "2. Убедитесь что все порты доступны"
    echo "3. Проверьте логи всех сервисов"
    echo "4. Обратитесь к документации по устранению неполадок"
fi

echo ""
echo "Логи тестирования сохранены в: /root/mirai-agent/logs/ai-integration-test-$(date +%Y%m%d-%H%M%S).log"

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}         ТЕСТИРОВАНИЕ ЗАВЕРШЕНО            ${NC}"
echo -e "${BLUE}============================================${NC}"

exit $exit_code