# Управление GitHub Actions Secrets и Variables

## 🎯 Обзор

Теперь у вас есть возможность автоматически создавать и управлять GitHub Actions secrets и variables с помощью токена `GH_TOKEN`, который имеет все необходимые права (`repo` + `admin:org`).

## 🔧 Готовые инструменты

### 1. Скрипт управления `manage-secrets.sh`

Создан полнофункциональный скрипт для управления secrets и variables:

```bash
# Помощь
./scripts/manage-secrets.sh

# Создать repository secret
./scripts/manage-secrets.sh create-secret SECRET_NAME "secret-value"

# Создать repository variable
./scripts/manage-secrets.sh create-variable VAR_NAME "variable-value"

# Показать список secrets
./scripts/manage-secrets.sh list-secrets

# Показать список variables
./scripts/manage-secrets.sh list-variables

# Тестовый режим (создает тестовые данные)
./scripts/manage-secrets.sh test
```

### 2. Функциональность

Скрипт автоматически:
- ✅ **Проверяет токен** `GH_TOKEN` 
- ✅ **Получает public key** для шифрования
- ✅ **Шифрует secrets** с помощью PyNaCl
- ✅ **Создает secrets** через GitHub API
- ✅ **Создает variables** через GitHub API
- ✅ **Показывает списки** существующих secrets/variables

## 🚀 Примеры использования

### Создание secrets для разных сервисов

```bash
# OpenAI API Key
./scripts/manage-secrets.sh create-secret OPENAI_API_KEY "sk-your-openai-key"

# Telegram Bot Token
./scripts/manage-secrets.sh create-secret TELEGRAM_BOT_TOKEN "123456:ABC-DEF..."

# SSH ключ для деплоя
./scripts/manage-secrets.sh create-secret SSH_PRIVATE_KEY "$(cat ~/.ssh/id_rsa | base64 -w 0)"

# Database URL
./scripts/manage-secrets.sh create-secret DATABASE_URL "postgresql://user:pass@host:5432/db"
```

### Создание variables для конфигурации

```bash
# Версия приложения
./scripts/manage-secrets.sh create-variable APP_VERSION "1.2.0"

# Среда выполнения
./scripts/manage-secrets.sh create-variable ENVIRONMENT "production"

# Регион для деплоя
./scripts/manage-secrets.sh create-variable DEPLOY_REGION "us-east-1"

# Уровень логирования
./scripts/manage-secrets.sh create-variable LOG_LEVEL "info"
```

## 🔒 Типы secrets и их использование

### 1. Repository Secrets
- Доступны для всех workflows в репозитории
- Идеально для API ключей, токенов, паролей
- Автоматически скрыты в логах

### 2. Repository Variables  
- Доступны для всех workflows в репозитории
- Видны в логах (не секретные данные)
- Идеально для конфигурации

### 3. Environment Secrets (расширение)
```bash
# Создание environment secret (требует доработки скрипта)
curl -X PUT \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/AgeeKey/mirai-agent/environments/production/secrets/SECRET_NAME \
  -d '{"encrypted_value":"encrypted_value","key_id":"key_id"}'
```

### 4. Organization Secrets (для всех репозиториев)
```bash
# Создание organization secret
curl -X PUT \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/orgs/AgeeKey/actions/secrets/SECRET_NAME \
  -d '{"encrypted_value":"encrypted_value","key_id":"key_id","visibility":"all"}'
```

## 🛠 Использование в AI автоматизации

### Python пример для AI

```python
import subprocess
import json

def create_github_secret(name, value):
    """Создать GitHub secret через скрипт"""
    result = subprocess.run([
        '/workspaces/mirai-agent/scripts/manage-secrets.sh',
        'create-secret', name, value
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Secret {name} создан успешно")
        return True
    else:
        print(f"❌ Ошибка создания secret {name}: {result.stderr}")
        return False

def create_github_variable(name, value):
    """Создать GitHub variable через скрипт"""
    result = subprocess.run([
        '/workspaces/mirai-agent/scripts/manage-secrets.sh',
        'create-variable', name, value
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Variable {name} создана успешно")
        return True
    else:
        print(f"❌ Ошибка создания variable {name}: {result.stderr}")
        return False

# Использование
create_github_secret("API_KEY", "secret-value")
create_github_variable("CONFIG_VALUE", "public-value")
```

## 📋 Проверка работоспособности

После настройки токена `GH_TOKEN` в Codespaces secrets:

1. **Перезапустите Codespace** чтобы токен стал доступен
2. **Запустите тест**:
   ```bash
   ./scripts/manage-secrets.sh test
   ```
3. **Проверьте созданные данные**:
   ```bash
   ./scripts/manage-secrets.sh list-secrets
   ./scripts/manage-secrets.sh list-variables
   ```

## 🎉 Результат

Теперь ваш AI может автоматически:
- ✅ Создавать secrets для API ключей
- ✅ Создавать variables для конфигурации  
- ✅ Управлять настройками CI/CD
- ✅ Автоматизировать деплой конфигурации
- ✅ Обновлять секреты при ротации ключей

Все готово для полной автоматизации управления секретами! 🚀