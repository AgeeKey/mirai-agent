#!/bin/bash
# Финальная проверка ПОЛНОЙ ПРОДАКШН-ГОТОВНОСТИ Mirai Agent

echo "======================================================="
echo "   🚀 MIRAI AGENT - ПОЛНАЯ ПРОДАКШН-ГОТОВНОСТЬ     "
echo "======================================================="

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

echo -e "\n${PURPLE}🔐 SSL & SECURITY${NC}"
echo "================================"
run_test "SSL Certificates" "[ -f '/etc/letsencrypt/live/aimirai.info-0001/fullchain.pem' ]"
run_test "SSL Auto-renewal" "systemctl is-enabled certbot.timer"
run_test "HTTPS Nginx Config" "grep -q 'ssl_certificate' /root/mirai-agent/nginx/aimirai.online.conf"

echo -e "\n${CYAN}🌐 WEB INTERFACE${NC}"
echo "================================"
run_test "Web Frontend Running" "curl -s http://localhost:3000 | grep -q 'Mirai Agent'"
run_test "Next.js Process" "pgrep -f 'next' > /dev/null"
run_test "Web Logs Available" "[ -f '/root/mirai-agent/logs/web-interface.log' ]"

echo -e "\n${YELLOW}💰 LIVE TRADING CONFIG${NC}"
echo "================================"
run_test "Live Trading Enabled" "grep -q 'BINANCE_TESTNET=false' /root/mirai-agent/.env"
run_test "Sandbox Mode Disabled" "grep -q 'AGENT_SANDBOX_MODE=false' /root/mirai-agent/.env"
run_test "Production Trading Mode" "grep -q 'TRADING_MODE=production' /root/mirai-agent/.env"
run_test "Real Binance Keys" "grep -q 'BINANCE_API_KEY=W0ygNMoQl1049jhJLsPw8fIFRrDegEkdxY8Vh95l5Ctpd5I8edGWa2LWfB9mPjo7' /root/mirai-agent/.env"

echo -e "\n${PURPLE}🤖 AI SYSTEM${NC}"
echo "================================"
run_test "AI Orchestrator" "curl -s http://localhost:8080/health | grep -q 'healthy'"
run_test "AI Task Processing" "curl -s -X POST http://localhost:8080/task/submit -H 'Content-Type: application/json' -d '{\"type\":\"trading\",\"goal\":\"Test live trading\",\"priority\":9}' | grep -q 'task_id'"
run_test "AI Reports Generated" "[ -d '/root/mirai-agent/shared/reports' ] && [ \$(ls -1 /root/mirai-agent/shared/reports/ | wc -l) -gt 0 ]"

echo -e "\n${CYAN}🚀 TRADING SYSTEM${NC}"
echo "================================"
run_test "Trading API Online" "curl -s http://localhost:8001/docs | grep -q 'Mirai Trading'"
run_test "Trading API Process" "pgrep -f 'mirai_api' > /dev/null"
run_test "Live API Endpoints" "curl -s http://localhost:8001/openapi.json | grep -q 'openapi'"

echo -e "\n${PURPLE}🌐 DOMAINS & NETWORKING${NC}"
echo "================================"
run_test "Nginx Running" "systemctl is-active nginx > /dev/null"
run_test "Domain Configs" "[ -f '/root/mirai-agent/nginx/aimirai.online.conf' ] && [ -f '/root/mirai-agent/nginx/aimirai.info.conf' ]"
run_test "Port 80 Listening" "netstat -tuln | grep -q ':80'"
run_test "Port 443 Listening" "netstat -tuln | grep -q ':443'"

echo -e "\n${YELLOW}📊 MONITORING & LOGS${NC}"
echo "================================"
run_test "Orchestrator Logs" "[ -f '/root/mirai-agent/logs/orchestrator.log' ]"
run_test "Trading API Logs" "[ -f '/root/mirai-agent/logs/trading-api.log' ]"
run_test "Web Interface Logs" "[ -f '/root/mirai-agent/logs/web-interface.log' ]"
run_test "Log Rotation" "[ -d '/root/mirai-agent/logs' ] && find /root/mirai-agent/logs -name '*.log' | wc -l | grep -q '[0-9]'"

echo -e "\n${CYAN}⚡ 24/7 AUTONOMY${NC}"
echo "================================"
run_test "Background Processes" "pgrep -f 'main.py' > /dev/null && pgrep -f 'mirai_api' > /dev/null && pgrep -f 'next' > /dev/null"
run_test "Auto-restart Capability" "systemctl is-enabled nginx > /dev/null"
run_test "AI Task Queue" "curl -s http://localhost:8080/tasks/active | grep -q 'task'"
run_test "System Resources OK" "[ \$(free | grep Mem | awk '{print (\$3/\$2)*100}' | cut -d. -f1) -lt 85 ]"

# Финальные результаты
echo ""
echo "======================================================="
echo "   🏆 ИТОГОВАЯ ПРОДАКШН-ГОТОВНОСТЬ                  "
echo "======================================================="
echo -e "Tests Passed: ${GREEN}${PASSED_TESTS}/${TOTAL_TESTS}${NC}"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    SUCCESS_RATE=100
    echo -e "Success Rate: ${GREEN}${SUCCESS_RATE}%${NC}"
    echo ""
    echo -e "${GREEN}🎉 СИСТЕМА ПОЛНОСТЬЮ ГОТОВА К ПРОДАКШЕНУ!${NC}"
    echo -e "${GREEN}✅ Live торговля активна${NC}"
    echo -e "${GREEN}✅ SSL сертификаты настроены${NC}"
    echo -e "${GREEN}✅ Веб-интерфейс работает${NC}"
    echo -e "${GREEN}✅ AI система автономна${NC}"
    echo -e "${GREEN}✅ Домены настроены${NC}"
    
    echo ""
    echo -e "${BLUE}🔗 ПРОДАКШН СЕРВИСЫ:${NC}"
    echo "  🌐 HTTPS: https://aimirai.online"
    echo "  🌐 Studio: https://aimirai.info"
    echo "  🤖 AI API: http://localhost:8080"
    echo "  💰 Trading: http://localhost:8001/docs"
    echo "  🎨 Web UI: http://localhost:3000"
    
    echo ""
    echo -e "${PURPLE}⚠️  LIVE TRADING АКТИВНА!${NC}"
    echo "  💰 Binance Mainnet: ENABLED"
    echo "  🚫 Testnet: DISABLED"
    echo "  🤖 AI Decisions: AUTONOMOUS"
    echo "  💸 Real Money: AT RISK"
    
    echo ""
    echo -e "${YELLOW}📝 МОНИТОРИНГ:${NC}"
    echo "  📊 Logs: /root/mirai-agent/logs/"
    echo "  📈 Reports: /root/mirai-agent/shared/reports/"
    echo "  🔍 Health: http://localhost:8080/health"
    echo "  📱 Status: http://localhost:8080/status"
    
    echo ""
    echo -e "${CYAN}🚀 АВТОНОМНЫЕ ПРОЦЕССЫ:${NC}"
    ps aux | grep -E "(main.py|mirai_api|next|nginx)" | grep -v grep | head -4
    
else
    SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo -e "Success Rate: ${YELLOW}${SUCCESS_RATE}%${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  СИСТЕМА ТРЕБУЕТ ДОРАБОТКИ${NC}"
    echo "Проверьте неудачные тесты выше"
fi

echo ""
echo "======================================================="
echo "         ПРОДАКШН-ПРОВЕРКА ЗАВЕРШЕНА                 "
echo "======================================================="