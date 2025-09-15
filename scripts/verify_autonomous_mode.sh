#!/bin/bash

# Autonomous Mode Verification Script
# This script tests all autonomous features to ensure they work without prompts

echo "🔍 Проверка автономного режима GitHub Copilot..."
echo ""

# Test 1: Environment Variables
echo "1. 🌍 Проверка переменных окружения:"
# Use environment variable if set, otherwise use relative path from this script's location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTIVATE_AUTONOMOUS_ENV_PATH="${ACTIVATE_AUTONOMOUS_ENV_PATH:-$SCRIPT_DIR/activate_autonomous_env.sh}"
source "$ACTIVATE_AUTONOMOUS_ENV_PATH" >/dev/null 2>&1

echo "   MIRAI_AUTONOMOUS_MODE: ${MIRAI_AUTONOMOUS_MODE:-❌ НЕ УСТАНОВЛЕНА}"
echo "   GITHUB_COPILOT_AUTONOMOUS: ${GITHUB_COPILOT_AUTONOMOUS:-❌ НЕ УСТАНОВЛЕНА}"
echo "   VSCODE_AUTONOMOUS_MODE: ${VSCODE_AUTONOMOUS_MODE:-❌ НЕ УСТАНОВЛЕНА}"
echo ""

# Test 2: VS Code Configuration Files
echo "2. 📁 Проверка файлов конфигурации VS Code:"
config_files=(
    "~/.vscode-server/data/User/settings.json"
    "~/.vscode-remote/data/User/settings.json" 
    "~/.config/Code/User/settings.json"
    "/home/runner/work/mirai-agent/mirai-agent/.vscode/settings.json"
)

for file in "${config_files[@]}"; do
    expanded_file=$(eval echo "$file")
    if [ -f "$expanded_file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file - НЕ НАЙДЕН"
    fi
done
echo ""

# Test 3: Command Functions
echo "3. ⚡ Проверка автономных команд:"
commands=("mi-status" "mi-test" "auto-commit" "auto-format" "mi-cd")

for cmd in "${commands[@]}"; do
    if type "$cmd" >/dev/null 2>&1; then
        echo "   ✅ $cmd - доступна"
    else
        echo "   ❌ $cmd - НЕ НАЙДЕНА"
    fi
done
echo ""

# Test 4: Git Configuration
echo "4. 🔧 Проверка настроек Git (без подтверждений):"
git_settings=(
    "advice.statusHints"
    "advice.commitBeforeMerge"
    "push.autoSetupRemote"
    "advice.addIgnoredFile"
)

for setting in "${git_settings[@]}"; do
    value=$(git config --global --get "$setting" 2>/dev/null || echo "не установлено")
    echo "   $setting: $value"
done
echo ""

# Test 5: VS Code Settings Check
echo "5. ⚙️ Проверка ключевых настроек VS Code:"
vscode_settings_file="/home/runner/work/mirai-agent/mirai-agent/.vscode/settings.json"

if [ -f "$vscode_settings_file" ]; then
    critical_settings=(
        "chat.experimental.agent.autoApprove"
        "chat.agent.maxRequests"
        "security.workspace.trust.enabled"
        "terminal.integrated.confirmOnExit"
        "window.confirmBeforeClose"
    )
    
    for setting in "${critical_settings[@]}"; do
        if grep -q "\"$setting\"" "$vscode_settings_file"; then
            echo "   ✅ $setting - настроен"
        else
            echo "   ❌ $setting - НЕ НАЙДЕН"
        fi
    done
else
    echo "   ❌ Файл настроек VS Code не найден"
fi
echo ""

# Test 6: Functional Test
echo "6. 🧪 Функциональный тест:"
cd /home/runner/work/mirai-agent/mirai-agent

echo "   Тестирование mi-status..."
if mi-status >/dev/null 2>&1; then
    echo "   ✅ mi-status работает"
else
    echo "   ❌ mi-status НЕ РАБОТАЕТ"
fi

echo "   Тестирование auto-format (dry run)..."
if type auto-format >/dev/null 2>&1; then
    echo "   ✅ auto-format команда доступна"
else
    echo "   ❌ auto-format НЕ ДОСТУПНА"
fi
echo ""

# Summary
echo "🎯 РЕЗЮМЕ АВТОНОМНОГО РЕЖИМА:"
echo ""

all_good=true

# Check critical components
if [ "${MIRAI_AUTONOMOUS_MODE}" = "true" ] && [ "${GITHUB_COPILOT_AUTONOMOUS}" = "true" ]; then
    echo "✅ Переменные окружения настроены правильно"
else
    echo "❌ Переменные окружения НЕ настроены"
    all_good=false
fi

if [ -f "$vscode_settings_file" ] && grep -q "chat.experimental.agent.autoApprove" "$vscode_settings_file"; then
    echo "✅ Настройки VS Code применены"
else
    echo "❌ Настройки VS Code НЕ применены"
    all_good=false
fi

if type mi-status >/dev/null 2>&1; then
    echo "✅ Автономные команды работают"
else
    echo "❌ Автономные команды НЕ работают"
    all_good=false
fi

echo ""
if [ "$all_good" = true ]; then
    echo "🚀 АВТОНОМНЫЙ РЕЖИМ ПОЛНОСТЬЮ АКТИВЕН!"
    echo "🤖 GitHub Copilot готов к работе БЕЗ подтверждений"
    echo ""
    echo "📋 Доступные команды:"
    echo "   mi-status, mi-test, mi-api, mi-start"
    echo "   auto-commit, auto-format, auto-test"
    echo "   mi-cd, mi-app, mi-tests, mi-scripts"
    echo ""
    echo "🎯 Используйте команды без каких-либо подтверждений!"
else
    echo "⚠️  АВТОНОМНЫЙ РЕЖИМ НЕ ПОЛНОСТЬЮ НАСТРОЕН"
    echo ""
    echo "🔧 Для исправления выполните:"
    echo "   cd /home/runner/work/mirai-agent/mirai-agent"
    echo "   ./scripts/setup_full_autonomous.sh"
    echo "   source scripts/activate_autonomous_env.sh"
fi

echo ""
echo "📄 Подробная документация: docs/AUTONOMOUS_MODE.md"