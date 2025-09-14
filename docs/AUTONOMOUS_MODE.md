# Настройки автономного GitHub Copilot агента

## Инструкции для максимальной автономности:

### 1. 🔧 Дополнительные настройки VS Code:

В **Command Palette** (Ctrl+Shift+P) выполните:

```
> Preferences: Open User Settings (JSON)
```

И добавьте эти настройки:

```json
{
  "github.copilot.advanced": {
    "debug.overrideEngine": "codex",
    "debug.testOverrideProxyUrl": "",
    "debug.overrideProxyUrl": "",
    "length": 2000,
    "temperature": 0.1,
    "top_p": 1.0,
    "stops": {
      "*": ["\n\n\n"]
    }
  },
  "github.copilot.editor.enableAutoCompletions": true,
  "github.copilot.editor.enableCodeActions": true,
  "github.copilot.chat.experimental.agent.enabled": true,
  "github.copilot.chat.experimental.codeGeneration.enabled": true,
  "github.copilot.chat.experimental.codeGeneration.instructions": [
    "Write production-ready code",
    "Include proper error handling",
    "Use type hints in Python",
    "Follow best practices",
    "Auto-commit changes when appropriate"
  ],
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.startupPrompt": "never",
  "workbench.enableExperiments": false,
  "telemetry.telemetryLevel": "off"
}
```

### 2. 🤖 Команды для полной автоматизации:

```bash
# Автоматический режим разработки
alias auto-dev="git add . && git commit -m 'Auto-commit by Copilot Agent' && git push"

# Автоматическое тестирование и деплой
alias auto-deploy="pytest tests/ && docker-compose build && docker-compose up -d"

# Автоматический анализ и исправления
alias auto-fix="ruff check --fix . && black . && mypy ."
```

### 3. 🔄 Автоматические действия при старте:

Добавьте в ваш `.bashrc`:

```bash
# Автозапуск при входе в проект
cd /workspaces/mirai-agent
export PYTHONPATH="/workspaces/mirai-agent/app:$PYTHONPATH"

# Автоматическая проверка статуса
echo "🚀 Mirai Agent - автономный режим активен"
echo "📊 Статус проекта:"
git status --short
echo "🐳 Docker статус:"
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### 4. 🎯 GitHub Copilot Chat команды:

Используйте эти команды для автономной работы:

- `@workspace /fix` - автоматически исправить все ошибки
- `@workspace /test` - написать и запустить тесты
- `@workspace /optimize` - оптимизировать код
- `@workspace /deploy` - подготовить к деплою
- `@workspace /commit` - создать осмысленный коммит

### 5. 🔐 Для полного доступа к терминалу:

В настройках Codespaces отключите:
- Terminal confirmation prompts
- Workspace trust prompts  
- Extension recommendation prompts

### 6. ⚡ Быстрые алиасы уже настроены:

- `mi-start` - запуск основного агента
- `mi-test` - запуск тестов
- `mi-api` - запуск API сервера
- `mi-build` - сборка Docker образов
- `mi-up` - запуск всех сервисов
- `mi-logs` - просмотр логов
- `mi-status` - общий статус проекта

### 7. 🎉 Проверка автономного режима:

```bash
# Проверить что всё работает
source ~/.bashrc
mi-status
```

Теперь GitHub Copilot может работать **полностью автономно** без ваших подтверждений! 🚀