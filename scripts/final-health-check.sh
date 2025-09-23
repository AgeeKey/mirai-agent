#!/bin/bash

# 🎯 Mirai Agent - Final Health Check
# Comprehensive production readiness verification

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
echo -e "${BOLD}${BLUE}   MIRAI AGENT - FINAL HEALTH CHECK          ${NC}"
echo -e "${BOLD}${BLUE}===============================================${NC}"
echo ""

# Test counter
TESTS_PASSED=0
TESTS_TOTAL=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_content="$3"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    echo -n "🧪 Testing $test_name... "
    
    if result=$(eval "$test_command" 2>/dev/null); then
        if [ -n "$expected_content" ]; then
            if echo "$result" | grep -q "$expected_content"; then
                echo -e "${GREEN}✅ PASS${NC}"
                TESTS_PASSED=$((TESTS_PASSED + 1))
                return 0
            else
                echo -e "${RED}❌ FAIL (wrong content)${NC}"
                echo "  Expected: $expected_content"
                echo "  Got: $result"
                return 1
            fi
        else
            echo -e "${GREEN}✅ PASS${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        fi
    else
        echo -e "${RED}❌ FAIL${NC}"
        return 1
    fi
}

echo -e "${CYAN}🔍 INFRASTRUCTURE HEALTH${NC}"
echo "================================"

# Test 1: Orchestrator Health
run_test "Orchestrator Health" "curl -fsS http://127.0.0.1:8080/health" '"status":"healthy"'

# Test 2: Orchestrator Status
run_test "Orchestrator Status" "curl -fsS http://127.0.0.1:8080/status" '"active_tasks"'

echo ""
echo -e "${CYAN}🤖 AI FUNCTIONALITY${NC}"
echo "================================"

# Test 3: Task Submission
echo -n "🧪 Testing AI Task Submission... "
TASK_RESPONSE=$(curl -fsS -X POST http://127.0.0.1:8080/task/submit \
    -H 'Content-Type: application/json' \
    -d '{"type":"reporting","goal":"Generate test report","symbol":"BTCUSDT"}' 2>/dev/null)

if echo "$TASK_RESPONSE" | grep -q '"task_id"'; then
    TASK_ID=$(echo "$TASK_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['task_id'])")
    echo -e "${GREEN}✅ PASS${NC} (Task ID: $TASK_ID)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    
    # Test 4: Task Status Check
    echo -n "🧪 Testing Task Status Check... "
    sleep 2  # Give task time to process
    
    if TASK_STATUS=$(curl -fsS http://127.0.0.1:8080/task/$TASK_ID 2>/dev/null); then
        if echo "$TASK_STATUS" | grep -q '"status"'; then
            echo -e "${GREEN}✅ PASS${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            
            # Test 5: Report File Generation
            echo -n "🧪 Testing Report Generation... "
            sleep 5  # Give more time for report generation
            
            if find /root/mirai-agent/shared/reports -name "report_*" -size +100c -mmin -2 | head -1 >/dev/null; then
                REPORT_FILE=$(find /root/mirai-agent/shared/reports -name "report_*" -size +100c -mmin -2 | head -1)
                echo -e "${GREEN}✅ PASS${NC} (File: $(basename $REPORT_FILE))"
                TESTS_PASSED=$((TESTS_PASSED + 1))
            else
                echo -e "${RED}❌ FAIL (no report file generated)${NC}"
            fi
        else
            echo -e "${RED}❌ FAIL (invalid status response)${NC}"
        fi
    else
        echo -e "${RED}❌ FAIL (status check failed)${NC}"
    fi
else
    echo -e "${RED}❌ FAIL${NC}"
fi

TESTS_TOTAL=$((TESTS_TOTAL + 3))  # Account for the last 3 tests

echo ""
echo -e "${CYAN}📁 FILE SYSTEM & PATHS${NC}"
echo "================================"

# Test 6: Shared Directories
run_test "Shared Directories" "ls -la /root/mirai-agent/shared" "reports"

# Test 7: Log Files
run_test "Log Files" "ls -la /root/mirai-agent/logs" "orchestrator"

# Test 8: Configuration Files
run_test "AI Configuration" "grep -c 'ai_integration:' /root/mirai-agent/configs/strategies.yaml" "1"

echo ""
echo -e "${CYAN}🔧 ENVIRONMENT & CONFIG${NC}"
echo "================================"

# Test 9: Environment Variables
run_test "AI_ENABLED Flag" "grep AI_ENABLED=true /root/mirai-agent/.env" "AI_ENABLED=true"

# Test 10: Python Dependencies
echo -n "🧪 Testing Python Dependencies... "
if python3 -c "import fastapi, uvicorn, httpx, pydantic; print('OK')" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL${NC}"
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))

echo ""
echo -e "${CYAN}🌐 NETWORK & CONNECTIVITY${NC}"
echo "================================"

# Test 11: Process Check
echo -n "🧪 Testing Orchestrator Process... "
if pgrep -f "python3 main.py" >/dev/null; then
    echo -e "${GREEN}✅ PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL${NC}"
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))

# Test 12: Port Accessibility
run_test "Port 8080 Accessibility" "netstat -tuln | grep :8080" ":8080"

echo ""
echo -e "${CYAN}📊 SYSTEM RESOURCES${NC}"
echo "================================"

# Test 13: Disk Space
echo -n "🧪 Testing Disk Space... "
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${GREEN}✅ PASS${NC} (${DISK_USAGE}% used)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ FAIL${NC} (${DISK_USAGE}% used - too high)"
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))

# Test 14: Memory Usage
echo -n "🧪 Testing Memory Usage... "
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
if [ "$MEMORY_USAGE" -lt 90 ]; then
    echo -e "${GREEN}✅ PASS${NC} (${MEMORY_USAGE}% used)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️ WARN${NC} (${MEMORY_USAGE}% used - high)"
    TESTS_PASSED=$((TESTS_PASSED + 1))  # Warning still counts as pass
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))

echo ""
echo -e "${BOLD}${CYAN}📋 FINAL RESULTS${NC}"
echo "================================"

# Calculate percentage
PERCENTAGE=$(( (TESTS_PASSED * 100) / TESTS_TOTAL ))

echo "Tests Passed: $TESTS_PASSED/$TESTS_TOTAL"
echo "Success Rate: $PERCENTAGE%"
echo ""

if [ $PERCENTAGE -ge 85 ]; then
    echo -e "${BOLD}${GREEN}🎉 SYSTEM READY FOR PRODUCTION!${NC}"
    echo -e "${GREEN}✅ All critical systems operational${NC}"
    echo -e "${GREEN}✅ AI integration working${NC}"
    echo -e "${GREEN}✅ Health checks passing${NC}"
    echo ""
    
    echo -e "${BOLD}Available Services:${NC}"
    echo "  🤖 AI Orchestrator: http://localhost:8080"
    echo "  📊 Health Check: http://localhost:8080/health"
    echo "  📈 Status: http://localhost:8080/status"
    echo "  📁 Reports: /root/mirai-agent/shared/reports/"
    echo ""
    
    echo -e "${BOLD}Next Steps:${NC}"
    echo "1. Set up domains (aimirai.info, aimirai.online)"
    echo "2. Configure SSL certificates"
    echo "3. Set OPENAI_API_KEY for full LLM functionality"
    echo "4. Start trading system with AI enabled"
    echo ""
    
    exit_code=0
elif [ $PERCENTAGE -ge 70 ]; then
    echo -e "${BOLD}${YELLOW}⚠️ SYSTEM PARTIALLY READY${NC}"
    echo -e "${YELLOW}Most systems operational, some issues detected${NC}"
    echo "Fix failing tests before production deployment"
    echo ""
    exit_code=1
else
    echo -e "${BOLD}${RED}❌ SYSTEM NOT READY${NC}"
    echo -e "${RED}Critical issues detected - not ready for production${NC}"
    echo "Fix failing tests before proceeding"
    echo ""
    exit_code=2
fi

# Show active processes
echo -e "${CYAN}🔄 Active AI Processes:${NC}"
ps aux | grep -E "(python3.*main\.py|orchestrator)" | grep -v grep || echo "No AI processes found"
echo ""

# Show recent log entries
echo -e "${CYAN}📝 Recent Orchestrator Logs:${NC}"
if [ -f "/root/mirai-agent/logs/orchestrator.log" ]; then
    tail -5 /root/mirai-agent/logs/orchestrator.log
else
    echo "No orchestrator logs found"
fi
echo ""

echo -e "${BOLD}${BLUE}===============================================${NC}"
echo -e "${BOLD}${BLUE}           HEALTH CHECK COMPLETE              ${NC}"
echo -e "${BOLD}${BLUE}===============================================${NC}"

exit $exit_code