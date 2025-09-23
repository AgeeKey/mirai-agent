# Настройка GitHub Token для управления Actions Secrets и Variables

## 🎯 Цель
Настроить GitHub Personal Access Token с правильными разрешениями для автоматического управления GitHub Actions secrets и variables через API.

## 🔑 Необходимые разрешения

### Fine-grained Personal Access Token (рекомендуется)

#### Repository permissions:
- **Secrets**: `Read and write` ✅ - для создания/обновления/удаления repository secrets
- **Variables**: `Read and write` ✅ - для создания/обновления/удаления repository variables  
- **Environments**: `Read and write` ✅ - для управления environment secrets
- **Metadata**: `Read` ✅ - базовый доступ к репозиторию
- **Actions**: `Read and write` ✅ - для управления workflows

#### Organization permissions (опционально):
- **Secrets**: `Read and write` ✅ - для organization-level secrets
- **Variables**: `Read and write` ✅ - для organization-level variables

### Classic Personal Access Token (альтернатива)
Если используете классический токен, выберите следующие scopes:
- `repo` - полный доступ к приватным репозиториям
- `admin:org` - для управления organization secrets/variables

## 📋 Пошаговая инструкция

### 1. Создание Fine-grained Token
1. Перейдите в настройки: https://github.com/settings/tokens?type=beta
2. Нажмите **"Generate new token"** → **"Fine-grained personal access token"**
3. Заполните форму:
   - **Token name**: `mirai-agent-actions-token`
   - **Expiration**: 90 дней (рекомендуется)
   - **Repository access**: Select repositories → `AgeeKey/mirai-agent`

### 2. Настройка Repository permissions
```
Account permissions:
✅ Secrets: Read and write
✅ Variables: Read and write  
✅ Environments: Read and write
✅ Metadata: Read
✅ Actions: Read and write
```

### 3. Настройка Organization permissions (если нужно)
```
Organization permissions:
✅ Secrets: Read and write
✅ Variables: Read and write
```

### 4. Сохранение токена
1. Нажмите **"Generate token"**
2. **ВАЖНО**: Скопируйте токен немедленно (он больше не будет показан)
3. Сохраните токен в безопасном месте

## 🎯 Рекомендации по выбору токена

### ✅ Рекомендуется: Classic token `GH_TOKEN`

**Используйте `GH_TOKEN` для управления Actions secrets/variables потому что:**
- ✅ **Уже готов к работе** - имеет scope `repo` + `admin:org`
- ✅ **Простота использования** - один токен для всех операций
- ✅ **Полные права** - может управлять и repository, и organization secrets
- ✅ **Совместимость** - работает со всеми GitHub API

### 🔧 Альтернатива: Fine-grained token `CODEX`

**Используйте `CODEX` если:**
- ✅ **Хотите минимальные права** - только для конкретных операций
- ✅ **Безопасность** - ограничен только репозиторием `mirai-agent`
- ❗ **Требует настройки** - нужно проверить/добавить разрешения

### 📋 Практические рекомендации

1. **Для AI автоматизации**: используйте `GH_TOKEN` (проще и надежнее)
2. **Для production**: рассмотрите `CODEX` с минимальными правами
3. **Для разработки**: `GH_TOKEN` для быстрого старта

## 🔧 Использование токена

### Добавление в Codespaces Secrets
1. Перейдите в репозиторий: `AgeeKey/mirai-agent`
2. Settings → Secrets and variables → Codespaces
3. Добавьте secret:
   - **Name**: `CODEX` (уже существует)
   - **Value**: ваш токен `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

> **Примечание**: У вас уже есть токен `CODEX` в Codespaces secrets. Проверьте его разрешения и обновите если необходимо.

### Проверка и обновление существующих токенов

#### У вас есть два токена в Codespaces secrets:

1. **`CODEX`** - ваш Fine-grained token
2. **`GH_TOKEN`** - ваш Classic token с правами `repo` и `admin:org`

**Classic token `GH_TOKEN`** уже должен работать для управления secrets/variables, если у него есть правильные scopes:
- ✅ `repo` - полный доступ к приватным репозиториям  
- ✅ `admin:org` - для управления organization secrets/variables

#### Какой токен использовать:

**Для Actions secrets/variables рекомендуется `GH_TOKEN`** (Classic token), так как:
- У него уже есть все необходимые права (`repo` + `admin:org`)
- Classic tokens проще в использовании для API
- Не требует настройки отдельных разрешений

**Для Fine-grained токена `CODEX`** нужно проверить разрешения:

Если ваш токен `CODEX` не работает с API secrets/variables, нужно:

1. **Найти токен в GitHub Settings:**
   - https://github.com/settings/tokens
   - Найдите токен с именем, которое использовали для `CODEX`

2. **Проверить разрешения:**
   - Убедитесь что у токена есть все необходимые Repository permissions
   - Если это Fine-grained token - проверьте что он применяется к репозиторию `mirai-agent`

3. **Обновить разрешения:**
   - Если нужно - добавьте недостающие разрешения
   - Или создайте новый токен с правильными разрешениями

4. **Обновить secret в Codespaces:**
   - Settings → Secrets and variables → Codespaces → Update `CODEX`

### Использование в коде

#### Вариант 1: Classic token GH_TOKEN (рекомендуется)
```bash
# Repository secret
curl -X PUT \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/AgeeKey/mirai-agent/actions/secrets/SECRET_NAME \
  -d '{"encrypted_value":"encrypted_value","key_id":"key_id"}'

# Repository variable  
curl -X POST \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/AgeeKey/mirai-agent/actions/variables \
  -d '{"name":"VARIABLE_NAME","value":"variable_value"}'
```

#### Вариант 2: Fine-grained token CODEX
```bash
# Repository secret
curl -X PUT \
  -H "Authorization: Bearer $CODEX" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/AgeeKey/mirai-agent/actions/secrets/SECRET_NAME \
  -d '{"encrypted_value":"encrypted_value","key_id":"key_id"}'

# Repository variable  
curl -X POST \
  -H "Authorization: Bearer $CODEX" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/AgeeKey/mirai-agent/actions/variables \
  -d '{"name":"VARIABLE_NAME","value":"variable_value"}'
```

## 🔒 Безопасность

1. **Минимальные разрешения**: Предоставляйте только необходимые разрешения
2. **Срок действия**: Устанавливайте разумный срок действия токена (90 дней)
3. **Ротация**: Регулярно обновляйте токены
4. **Хранение**: Используйте Codespaces Secrets, не храните в коде

## 🧪 Проверка разрешений

Для проверки что токены работают:

#### Проверка Classic token GH_TOKEN:
```bash
# Список repository secrets
curl -H "Authorization: Bearer $GH_TOKEN" \
     -H "Accept: application/vnd.github+json" \
     https://api.github.com/repos/AgeeKey/mirai-agent/actions/secrets

# Список repository variables
curl -H "Authorization: Bearer $GH_TOKEN" \
     -H "Accept: application/vnd.github+json" \
     https://api.github.com/repos/AgeeKey/mirai-agent/actions/variables
```

#### Проверка Fine-grained token CODEX:
```bash
# Список repository secrets
curl -H "Authorization: Bearer $CODEX" \
     -H "Accept: application/vnd.github+json" \
     https://api.github.com/repos/AgeeKey/mirai-agent/actions/secrets

# Список repository variables
curl -H "Authorization: Bearer $CODEX" \
     -H "Accept: application/vnd.github+json" \
     https://api.github.com/repos/AgeeKey/mirai-agent/actions/variables
```

## ❗ Распространенные ошибки

1. **403 Forbidden**: Недостаточно разрешений - проверьте Repository permissions
2. **404 Not Found**: Неправильный репозиторий или токен не имеет доступа
3. **401 Unauthorized**: Неверный токен или истек срок действия

## 📚 Документация
- [GitHub REST API - Actions Secrets](https://docs.github.com/en/rest/actions/secrets)
- [GitHub REST API - Actions Variables](https://docs.github.com/en/rest/actions/variables)
- [Fine-grained Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token)