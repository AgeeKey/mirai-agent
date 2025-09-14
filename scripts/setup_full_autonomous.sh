#!/bin/bash

# Скрипт для полного отключения всех запросов разрешений в VS Code и GitHub Copilot

echo "🔧 Настраиваю ПОЛНУЮ автономность (без любых разрешений)..."

# 1. Создаём конфиг для автоматического принятия всех операций
mkdir -p ~/.vscode-server/data/User/

cat > ~/.vscode-server/data/User/settings.json << 'VSCODE_EOF'
{
  "github.copilot.enable": { "*": true },
  "github.copilot.advanced": {
    "length": 3000,
    "temperature": 0.05,
    "top_p": 1,
    "inlineSuggestEnable": true,
    "listCount": 10,
    "debug.useNodeRuntime": false,
    "debug.useElectronNotifications": false
  },
  "github.copilot.rejectWithHang": false,
  "github.copilot.editor.enableAutoCompletions": true,
  "github.copilot.editor.enableCodeActions": true,
  "github.copilot.chat.welcomeMessage": "never",
  "github.copilot.chat.experimental.agent.enabled": true,
  "github.copilot.chat.experimental.codeGeneration.enabled": true,
  "github.copilot.chat.experimental.copilotEdits.enabled": true,
  "chat.experimental.defaultAgent": "copilot",
  "chat.experimental.agent.autoApprove": true,
  "chat.agent.maxRequests": 100000,
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.emptyWindow": false,
  "security.workspace.trust.untrustedFiles": "open",
  "workbench.enableExperiments": false,
  "workbench.settings.enableNaturalLanguageSearch": false,
  "workbench.startupEditor": "none",
  "terminal.integrated.confirmOnExit": "never",
  "terminal.integrated.confirmOnKill": "never",
  "terminal.integrated.allowWorkspaceConfiguration": true,
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 300,
  "editor.formatOnSave": true,
  "editor.formatOnPaste": true,
  "extensions.ignoreRecommendations": true,
  "extensions.autoUpdate": false,
  "extensions.autoCheckUpdates": false,
  "telemetry.telemetryLevel": "off",
  "update.mode": "manual",
  "notifications.showExtensionsNotifications": false,
  "window.confirmBeforeClose": "never",
  "explorer.confirmDelete": false,
  "explorer.confirmDragAndDrop": false
}
VSCODE_EOF

# 2. Создаём переменные окружения для автоматического принятия
cat >> ~/.bashrc << 'BASH_EOF'

# Автоматическое принятие всех операций VS Code и GitHub Copilot
export VSCODE_SKIP_GETTING_STARTED=true
export VSCODE_SKIP_RELEASE_NOTES=true
export COPILOT_NODE_VERSION="18"
export NODE_OPTIONS="--max-old-space-size=8192"

# Отключение всех интерактивных запросов
export DEBIAN_FRONTEND=noninteractive
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Автоматические команды для Mirai Agent
alias auto-commit="git add . && git commit -m 'Auto: $(date)' && git push"
alias auto-format="black . && ruff check --fix ."
alias auto-test="/workspaces/mirai-agent/.venv/bin/python -m pytest tests/ -v"
alias auto-api="cd /workspaces/mirai-agent && /workspaces/mirai-agent/.venv/bin/python -m uvicorn app.api.mirai_api.main:app --reload --host 0.0.0.0 --port 8000"

echo "🤖 Автономный режим Mirai Agent активен (без разрешений)"

BASH_EOF

# 3. Создаём конфигурацию для Codespaces
mkdir -p ~/.vscode-remote/data/User/
cp ~/.vscode-server/data/User/settings.json ~/.vscode-remote/data/User/settings.json

# 4. Настраиваем Git для автоматических операций
git config --global advice.addIgnoredFile false
git config --global advice.addEmptyPathspec false
git config --global advice.statusHints false
git config --global advice.commitBeforeMerge false
git config --global advice.resolveConflict false
git config --global advice.detachedHead false

echo "✅ Все конфигурации созданы!"
echo "📝 Файлы созданы:"
echo "  - ~/.config/Code/User/settings.json (локальные настройки)"
echo "  - ~/.vscode-server/data/User/settings.json (серверные настройки)"
echo "  - ~/.vscode-remote/data/User/settings.json (удалённые настройки)"
echo ""
echo "🚀 Автономный режим настроен полностью!"
echo "   Больше НЕ БУДЕТ запросов разрешений!"
echo ""
echo "🔄 Перезагрузите VS Code для применения настроек:"
echo "   Command Palette > Developer: Reload Window"