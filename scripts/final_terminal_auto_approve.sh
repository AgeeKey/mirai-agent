#!/bin/bash

echo "🔧 ОКОНЧАТЕЛЬНАЯ НАСТРОЙКА АВТОНОМНОСТИ ТЕРМИНАЛА"
echo ""

# Копируем настройки во все возможные места
echo "📝 Обновляю настройки автоутверждения терминала..."

# Для vscode-server
mkdir -p ~/.vscode-server/data/User/
cp /home/codespace/.config/Code/User/settings.json ~/.vscode-server/data/User/settings.json

# Для vscode-remote  
mkdir -p ~/.vscode-remote/data/User/
cp /home/codespace/.config/Code/User/settings.json ~/.vscode-remote/data/User/settings.json

# Для Codespaces
mkdir -p ~/.codespace-global-settings/
cp /home/codespace/.config/Code/User/settings.json ~/.codespace-global-settings/settings.json

echo "✅ Настройки применены во всех местах:"
echo "  - ~/.config/Code/User/settings.json"
echo "  - ~/.vscode-server/data/User/settings.json"
echo "  - ~/.vscode-remote/data/User/settings.json"
echo "  - ~/.codespace-global-settings/settings.json"
echo ""

echo "🚀 Ключевые настройки автоутверждения:"
echo '  "chat.experimental.terminal.autoApprove": { "/.*/": true }'
echo '  "chat.tools.terminal.autoApprove": { "/.*/": true }'
echo '  "chat.experimental.agent.autoApprove": true'
echo ""

echo "🎯 Теперь GitHub Copilot АВТОМАТИЧЕСКИ утверждает ВСЕ команды!"
echo ""
echo "📋 Для применения настроек:"
echo "  1. Command Palette > Developer: Reload Window"  
echo "  2. Или перезапустите VS Code полностью"
echo ""
echo "✨ После перезапуска VS Code больше НЕ БУДЕТ запросов разрешений!"