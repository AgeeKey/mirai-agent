#!/bin/bash
# Финальная проверка автономной системы Mirai Agent

echo "======================================================="
echo "   🚀 MIRAI AGENT - ПОЛНАЯ АВТОНОМНОСТЬ           "
echo "======================================================="

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Счетчики
TOTAL_TESTS=0
PASSED_TESTS=0

# Функция для запуска тестов
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "${BLUE}🧪 Testing ${test_name}...${NC}"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        return 1
    fi
}

echo -e "\n${YELLOW}🤖 AI ORCHESTRATOR SYSTEM${NC}"
echo "================================"
run_test "AI Orchestrator Health" "curl -s http://localhost:8080/health | grep -q 'healthy'"
run_test "AI Task Submission" "curl -s -X POST http://localhost:8080/task/submit -H 'Content-Type: application/json' -d '{\"type\":\"trading\",\"goal\":\"Test autonomous trading\",\"priority\":8}' | grep -q 'task_id'"
run_test "AI Status Monitoring" "curl -s http://localhost:8080/status | grep -q 'operational'"

echo -e "\n${YELLOW}💰 TRADING SYSTEM${NC}"
echo "================================"
run_test "Trading API Health" "curl -s http://localhost:8001/docs | grep -q 'Mirai Trading'"
run_test "API Documentation" "curl -s http://localhost:8001/openapi.json | grep -q 'openapi'"

echo -e "\n${YELLOW}🔐 AUTHENTICATION & KEYS${NC}"
echo "================================"
run_test "OpenAI API Key" "grep -q 'OPENAI_API_KEY=sk-' /root/mirai-agent/.env"
run_test "Binance API Keys" "grep -q 'BINANCE_API_KEY=' /root/mirai-agent/.env && grep -q 'BINANCE_SECRET_KEY=' /root/mirai-agent/.env"
run_test "Telegram Integration" "grep -q 'TELEGRAM_BOT_TOKEN=' /root/mirai-agent/.env"
run_test "AI Enabled Flag" "grep -q 'AI_ENABLED=true' /root/mirai-agent/.env"

echo -e "\n${YELLOW}🌐 DOMAIN & NETWORK${NC}"
echo "================================"
run_test "Domain Configuration" "grep -q 'DOMAIN_PANEL=aimirai.online' /root/mirai-agent/.env && grep -q 'DOMAIN_STUDIO=aimirai.info' /root/mirai-agent/.env"
run_test "Nginx Running" "systemctl is-active nginx"
run_test "Port 8080 (AI Orchestrator)" "netstat -tuln | grep -q ':8080'"
run_test "Port 8001 (Trading API)" "netstat -tuln | grep -q ':8001'"

echo -e "\n${YELLOW}📁 FILE SYSTEM & ENVIRONMENT${NC}"
echo "================================"
run_test "Shared Directories" "[ -d '/root/mirai-agent/shared/data' ] && [ -d '/root/mirai-agent/shared/reports' ] && [ -d '/root/mirai-agent/shared/knowledge' ]"
run_test "Log Directory" "[ -d '/root/mirai-agent/logs' ]"
run_test "State Directory" "[ -d '/root/mirai-agent/state' ]"
run_test "Configuration Files" "[ -f '/root/mirai-agent/configs/risk.yaml' ] && [ -f '/root/mirai-agent/configs/strategies.yaml' ]"

echo -e "\n${YELLOW}⚡ AUTONOMOUS PROCESSES${NC}"
echo "================================"
run_test "AI Orchestrator Process" "pgrep -f 'main.py' > /dev/null"
run_test "Trading API Process" "pgrep -f 'python3.*mirai_api' > /dev/null"
run_test "Nginx Process" "pgrep nginx > /dev/null"

echo -e "\n${YELLOW}📊 SYSTEM RESOURCES${NC}"
echo "================================"
run_test "Disk Space Available" "[ \$(df / | tail -1 | awk '{print \$5}' | sed 's/%//') -lt 90 ]"
run_test "Memory Available" "[ \$(free | grep Mem | awk '{print (\$3/\$2)*100}' | cut -d. -f1) -lt 90 ]"

# Финальные результаты
echo ""
echo "======================================================="
echo "   📋 РЕЗУЛЬТАТЫ АВТОНОМНОСТИ                       "
echo "======================================================="
echo -e "Tests Passed: ${GREEN}${PASSED_TESTS}/${TOTAL_TESTS}${NC}"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    SUCCESS_RATE=100
    echo -e "Success Rate: ${GREEN}${SUCCESS_RATE}%${NC}"
    echo ""
    echo -e "${GREEN}🎉 СИСТЕМА ПОЛНОСТЬЮ АВТОНОМНА!${NC}"
    echo -e "${GREEN}✅ Готова к работе 24/7 без вмешательства${NC}"
    
    echo ""
    echo -e "${BLUE}🔗 ДОСТУПНЫЕ СЕРВИСЫ:${NC}"
    echo "  🤖 AI Orchestrator: http://localhost:8080"
    echo "  💰 Trading API: http://localhost:8001/docs"
    echo "  🌐 Домены: aimirai.online, aimirai.info"
    echo "  📊 Status: http://localhost:8080/status"
    
    echo ""
    echo -e "${BLUE}🚀 АКТИВНЫЕ ПРОЦЕССЫ:${NC}"
    ps aux | grep -E "(orchestrator|mirai_api|nginx)" | grep -v grep | head -3
    
    echo ""
    echo -e "${YELLOW}📝 ЛОГИ:${NC}"
    echo "  AI Orchestrator: /root/mirai-agent/logs/orchestrator.log"
    echo "  Trading API: /root/mirai-agent/logs/trading-api.log"
    echo "  Reports: /root/mirai-agent/shared/reports/"
    
else
    SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo -e "Success Rate: ${YELLOW}${SUCCESS_RATE}%${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  СИСТЕМА ТРЕБУЕТ ДОРАБОТКИ${NC}"
    echo "Проверьте неудачные тесты выше"
fi

echo ""
echo "======================================================="
echo "       ПРОВЕРКА АВТОНОМНОСТИ ЗАВЕРШЕНА              "
echo "======================================================="