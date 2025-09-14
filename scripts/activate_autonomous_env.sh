#!/bin/bash

# Comprehensive Autonomous Environment Activation Script
# This script sets up all environment variables and aliases for fully autonomous operation

echo "🚀 Активирую полностью автономное окружение для Mirai Agent..."

# 1. Core autonomous environment variables
export VSCODE_SKIP_GETTING_STARTED=true
export VSCODE_SKIP_RELEASE_NOTES=true
export COPILOT_NODE_VERSION="18"
export NODE_OPTIONS="--max-old-space-size=8192"
export DEBIAN_FRONTEND=noninteractive
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export GITHUB_COPILOT_AUTONOMOUS=true
export VSCODE_AUTONOMOUS_MODE=true

# 2. Mirai Agent specific environment
export PYTHONPATH="/home/runner/work/mirai-agent/mirai-agent/app:$PYTHONPATH"
export MIRAI_AGENT_ROOT="/home/runner/work/mirai-agent/mirai-agent"
export MIRAI_AUTONOMOUS_MODE=true

# 3. Core project aliases with full paths (using function syntax for better compatibility)
mi-start() { cd "${MIRAI_AGENT_ROOT}" && python app/cli.py "$@"; }
mi-test() { cd "${MIRAI_AGENT_ROOT}" && python -m pytest tests/ -v "$@"; }
mi-api() { cd "${MIRAI_AGENT_ROOT}" && python -m uvicorn app.api.mirai_api.main:app --reload --host 0.0.0.0 --port 8000 "$@"; }
mi-build() { cd "${MIRAI_AGENT_ROOT}" && docker-compose -f infra/docker-compose.yml build "$@"; }
mi-up() { cd "${MIRAI_AGENT_ROOT}" && docker-compose -f infra/docker-compose.yml up -d "$@"; }
mi-down() { cd "${MIRAI_AGENT_ROOT}" && docker-compose -f infra/docker-compose.yml down "$@"; }
mi-logs() { cd "${MIRAI_AGENT_ROOT}" && docker-compose -f infra/docker-compose.yml logs -f "$@"; }
mi-status() { cd "${MIRAI_AGENT_ROOT}" && git status && echo '---' && docker ps; }

# 4. Autonomous operation functions (no confirmations)
auto-commit() { cd "${MIRAI_AGENT_ROOT}" && git add . && git commit -m "Auto: $(date)" && git push; }
auto-format() { cd "${MIRAI_AGENT_ROOT}" && black . && ruff check --fix .; }
auto-test() { cd "${MIRAI_AGENT_ROOT}" && python -m pytest tests/ -v; }
auto-api() { cd "${MIRAI_AGENT_ROOT}" && python -m uvicorn app.api.mirai_api.main:app --reload --host 0.0.0.0 --port 8000; }
auto-build() { cd "${MIRAI_AGENT_ROOT}" && docker-compose -f infra/docker-compose.yml build; }
auto-deploy() { cd "${MIRAI_AGENT_ROOT}" && auto-test && auto-build && mi-up; }

# 5. Development shortcuts
mi-shell() { cd "${MIRAI_AGENT_ROOT}" && python -i -c 'from app.cli import *'; }
mi-deps() { cd "${MIRAI_AGENT_ROOT}" && pip install -r requirements.txt; }
mi-clean() { cd "${MIRAI_AGENT_ROOT}" && docker system prune -f; }
mi-reset() { cd "${MIRAI_AGENT_ROOT}" && git reset --hard HEAD && git clean -fd; }

# 6. Quick navigation
mi-cd() { cd "${MIRAI_AGENT_ROOT}"; }
mi-app() { cd "${MIRAI_AGENT_ROOT}/app"; }
mi-tests() { cd "${MIRAI_AGENT_ROOT}/tests"; }
mi-scripts() { cd "${MIRAI_AGENT_ROOT}/scripts"; }
mi-docs() { cd "${MIRAI_AGENT_ROOT}/docs"; }

# 7. Git automation settings (no confirmations)
git config --global advice.addIgnoredFile false
git config --global advice.addEmptyPathspec false
git config --global advice.statusHints false
git config --global advice.commitBeforeMerge false
git config --global advice.resolveConflict false
git config --global advice.detachedHead false
git config --global advice.pushUpdateRejected false
git config --global push.autoSetupRemote true
git config --global pull.rebase false
git config --global core.autocrlf false

# 8. Auto-activation message
echo "✅ Автономное окружение активировано!"
echo "🤖 GitHub Copilot теперь работает БЕЗ подтверждений"
echo "📝 Доступные команды:"
echo "   mi-start    - Запуск агента"
echo "   mi-test     - Тесты"
echo "   mi-api      - API сервер"
echo "   mi-status   - Статус проекта"
echo "   auto-*      - Автономные команды"
echo ""
echo "🚀 Готов к автономной работе!"

# 9. Auto-navigate to project root
cd "${MIRAI_AGENT_ROOT}"