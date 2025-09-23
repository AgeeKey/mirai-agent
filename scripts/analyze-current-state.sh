#!/bin/bash

# 🔍 Mirai Agent - Анализ текущего состояния системы
# Подробная проверка всех компонентов для безопасного обновления

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}   MIRAI AGENT - АНАЛИЗ СИСТЕМЫ       ${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

# 1. Проверка основных директорий
echo -e "${BLUE}📂 СТРУКТУРА ПРОЕКТА${NC}"
echo "----------------------------------------"
for dir in app web microservices infra state logs reports configs scripts; do
    if [ -d "/root/mirai-agent/$dir" ]; then
        size=$(du -sh "/root/mirai-agent/$dir" 2>/dev/null | cut -f1)
        file_count=$(find "/root/mirai-agent/$dir" -type f | wc -l)
        echo -e "  ${GREEN}✅${NC} $dir (${size}, ${file_count} файлов)"
    else
        echo -e "  ${RED}❌${NC} $dir (отсутствует)"
    fi
done
echo ""

# 2. Проверка Docker состояния
echo -e "${BLUE}🐳 DOCKER СОСТОЯНИЕ${NC}"
echo "----------------------------------------"
if systemctl is-active --quiet docker; then
    echo -e "  ${GREEN}✅${NC} Docker daemon запущен"
    
    # Показываем контейнеры если есть
    if docker ps -a &>/dev/null; then
        echo ""
        echo "Текущие контейнеры:"
        docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -10
    fi
else
    echo -e "  ${RED}❌${NC} Docker daemon остановлен"
    docker_status=$(systemctl show docker -p ActiveState --value)
    echo "     Статус: $docker_status"
fi
echo ""

# 3. Проверка Python пакетов
echo -e "${BLUE}📦 PYTHON ПАКЕТЫ${NC}"
echo "----------------------------------------"
for pkg in app/api app/trader app/agent app/telegram_bot; do
    if [ -f "/root/mirai-agent/$pkg/pyproject.toml" ]; then
        echo -e "  ${GREEN}✅${NC} $pkg"
        # Показываем версию если есть
        if grep -q "version" "/root/mirai-agent/$pkg/pyproject.toml"; then
            version=$(grep "version" "/root/mirai-agent/$pkg/pyproject.toml" | head -1 | cut -d'"' -f2)
            echo "     Версия: $version"
        fi
    else
        echo -e "  ${RED}❌${NC} $pkg (нет pyproject.toml)"
    fi
done
echo ""

# 4. Проверка конфигураций
echo -e "${BLUE}🔧 КОНФИГУРАЦИИ${NC}"
echo "----------------------------------------"
for config in configs/risk.yaml configs/strategies.yaml configs/logging.yaml .env; do
    if [ -f "/root/mirai-agent/$config" ]; then
        size=$(ls -lh "/root/mirai-agent/$config" | awk '{print $5}')
        echo -e "  ${GREEN}✅${NC} $config ($size)"
        
        # Проверяем .env на критичные переменные
        if [[ "$config" == ".env" ]]; then
            echo "     Переменные:"
            if grep -q "OPENAI_API_KEY" "/root/mirai-agent/$config"; then
                echo -e "       ${GREEN}✅${NC} OPENAI_API_KEY"
            else
                echo -e "       ${YELLOW}⚠️${NC} OPENAI_API_KEY отсутствует"
            fi
            
            if grep -q "BINANCE_API_KEY" "/root/mirai-agent/$config"; then
                echo -e "       ${GREEN}✅${NC} BINANCE_API_KEY"
            else
                echo -e "       ${YELLOW}⚠️${NC} BINANCE_API_KEY отсутствует"
            fi
        fi
    else
        echo -e "  ${RED}❌${NC} $config (отсутствует)"
    fi
done
echo ""

# 5. Проверка базы данных
echo -e "${BLUE}💾 БАЗА ДАННЫХ${NC}"
echo "----------------------------------------"
if [ -f "/root/mirai-agent/state/mirai.db" ]; then
    size=$(du -h /root/mirai-agent/state/mirai.db | cut -f1)
    echo -e "  ${GREEN}✅${NC} SQLite database ($size)"
    
    # Проверяем таблицы
    if command -v sqlite3 >/dev/null 2>&1; then
        echo "     Статистика таблиц:"
        sqlite3 /root/mirai-agent/state/mirai.db "
        SELECT 
            'positions' as table_name, 
            COUNT(*) as count
        FROM positions 
        UNION ALL 
        SELECT 
            'orders' as table_name, 
            COUNT(*) as count 
        FROM orders;" 2>/dev/null | while read line; do
            echo "       $line"
        done
    else
        echo -e "       ${YELLOW}⚠️${NC} sqlite3 не установлен для проверки таблиц"
    fi
else
    echo -e "  ${RED}❌${NC} Database не найдена"
fi
echo ""

# 6. Проверка портов
echo -e "${BLUE}🌐 СЕТЕВЫЕ ПОРТЫ${NC}"
echo "----------------------------------------"
echo "Проверка занятых портов Mirai:"
ports=("8001:API" "8002:Trader" "8003:Telegram" "3000:Frontend" "8085:SuperAGI" "8090:AutoGPT" "8080:Orchestrator")

for port_info in "${ports[@]}"; do
    port=$(echo $port_info | cut -d: -f1)
    service=$(echo $port_info | cut -d: -f2)
    
    if netstat -tulpn 2>/dev/null | grep -q ":$port "; then
        process=$(netstat -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d/ -f2 | head -1)
        echo -e "  ${GREEN}✅${NC} $service ($port) - $process"
    else
        echo -e "  ${YELLOW}⚠️${NC} $service ($port) - свободен"
    fi
done
echo ""

# 7. Проверка логов
echo -e "${BLUE}📜 ЛОГИ${NC}"
echo "----------------------------------------"
if [ -d "/root/mirai-agent/logs" ]; then
    log_files=$(find /root/mirai-agent/logs -name "*.log" -type f | wc -l)
    total_size=$(du -sh /root/mirai-agent/logs 2>/dev/null | cut -f1)
    echo -e "  ${GREEN}✅${NC} Директория логов ($total_size, $log_files файлов)"
    
    # Показываем последние логи
    if [ $log_files -gt 0 ]; then
        echo "     Последние 3 лог-файла:"
        find /root/mirai-agent/logs -name "*.log" -type f -printf '%T@ %p\n' | sort -n | tail -3 | while read timestamp filepath; do
            filename=$(basename "$filepath")
            size=$(ls -lh "$filepath" | awk '{print $5}')
            echo "       $filename ($size)"
        done
    fi
else
    echo -e "  ${RED}❌${NC} Директория логов отсутствует"
fi
echo ""

# 8. Проверка свободного места
echo -e "${BLUE}💽 ДИСКОВОЕ ПРОСТРАНСТВО${NC}"
echo "----------------------------------------"
df -h / | grep -v "Filesystem"
echo ""
echo "Размеры основных директорий:"
du -sh /root/mirai-agent/{app,web,microservices,state,logs} 2>/dev/null | sort -h
echo ""

# 9. Проверка системных требований
echo -e "${BLUE}⚙️ СИСТЕМНЫЕ ТРЕБОВАНИЯ${NC}"
echo "----------------------------------------"
echo "RAM:"
free -h | grep "Mem:"
echo ""
echo "CPU:"
nproc
echo ""
echo "Python версия:"
python3 --version
echo ""

# 10. Проверка AI-готовности
echo -e "${BLUE}🤖 AI-ГОТОВНОСТЬ${NC}"
echo "----------------------------------------"

# Проверяем microservices директорию
if [ -d "/root/mirai-agent/microservices" ]; then
    echo -e "  ${GREEN}✅${NC} Директория microservices существует"
    
    # Проверяем структуру для AI
    if [ -d "/root/mirai-agent/microservices/ai-engine" ]; then
        echo -e "  ${GREEN}✅${NC} ai-engine директория существует"
    else
        echo -e "  ${YELLOW}⚠️${NC} ai-engine директория отсутствует (будет создана)"
    fi
else
    echo -e "  ${RED}❌${NC} Директория microservices отсутствует"
fi

# Проверяем shared директорию
if [ -d "/root/mirai-agent/shared" ]; then
    echo -e "  ${GREEN}✅${NC} Shared директория существует"
else
    echo -e "  ${YELLOW}⚠️${NC} Shared директория отсутствует (будет создана)"
fi

echo ""

# 11. Итоговые рекомендации
echo -e "${BLUE}📋 РЕКОМЕНДАЦИИ${NC}"
echo "----------------------------------------"

# Проверяем критичные проблемы
critical_issues=0

if ! systemctl is-active --quiet docker; then
    echo -e "${RED}🔥 КРИТИЧНО:${NC} Docker не запущен - необходимо исправить перед развертыванием AI"
    critical_issues=$((critical_issues + 1))
fi

if [ ! -f "/root/mirai-agent/.env" ]; then
    echo -e "${RED}🔥 КРИТИЧНО:${NC} Файл .env отсутствует"
    critical_issues=$((critical_issues + 1))
elif ! grep -q "OPENAI_API_KEY" "/root/mirai-agent/.env"; then
    echo -e "${YELLOW}⚠️ ВАЖНО:${NC} Добавьте OPENAI_API_KEY в .env для AI функций"
fi

if [ ! -f "/root/mirai-agent/state/mirai.db" ]; then
    echo -e "${YELLOW}⚠️ ВАЖНО:${NC} База данных отсутствует - будет создана при первом запуске"
fi

# Проверяем свободное место (минимум 2GB)
available_space=$(df / | tail -1 | awk '{print $4}')
if [ $available_space -lt 2097152 ]; then  # 2GB in KB
    echo -e "${RED}🔥 КРИТИЧНО:${NC} Недостаточно места на диске (нужно минимум 2GB)"
    critical_issues=$((critical_issues + 1))
fi

if [ $critical_issues -eq 0 ]; then
    echo -e "${GREEN}✅ Система готова для развертывания AI компонентов${NC}"
    echo ""
    echo "Следующие шаги:"
    echo "1. ./scripts/backup-before-upgrade.sh"
    echo "2. ./scripts/fix-docker.sh (если Docker не работает)"
    echo "3. ./scripts/phase1-prepare.sh"
else
    echo -e "${RED}❌ Обнаружено $critical_issues критических проблем${NC}"
    echo "Исправьте их перед продолжением."
fi

echo ""
echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}         АНАЛИЗ ЗАВЕРШЕН              ${NC}"
echo -e "${BLUE}=======================================${NC}"