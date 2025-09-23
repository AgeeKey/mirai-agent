#!/bin/bash

echo "🤖 Настройка МИНИМАЛЬНОЙ автономии Mirai Agent..."

# Создание директории
mkdir -p /root/.vscode-server/data/Machine

# Создание единственной ключевой настройки
cat > /root/.vscode-server/data/Machine/settings.json << 'EOJSON'
{
  "chat.tools.autoApprove": true
}
EOJSON

echo "✅ Автономная настройка применена:"
echo "   - chat.tools.autoApprove: true"
echo ""
echo "🔹 Что это даёт:"
echo "   ✅ Любые команды терминала (включая rm -rf /)"
echo "   ✅ Любое редактирование файлов (.env, settings.json)"
echo "   ✅ Любые веб-запросы и сервисные вызовы"
echo "   ✅ Полная автономия БЕЗ ОГРАНИЧЕНИЙ"
echo ""
echo "🎉 Mirai Agent полностью автономен!"
