# CI/CD Troubleshooting Guide

## 🚨 Проблемы и решения

### Основные причины поломок CI:

1. **Устаревшие версии GitHub Actions**
   - ❌ `actions/setup-python@v4` 
   - ✅ `actions/setup-python@v5`

2. **Неправильные зависимости**
   - ❌ `flake8` (устарел)
   - ✅ `ruff` (современный линтер)

3. **Неконсистентные версии Python**
   - ❌ Разные версии в разных workflow
   - ✅ Только Python 3.12 везде

4. **Проблемы с установкой пакетов**
   - ❌ `pip install -e app/api[dev]` без `cd`
   - ✅ `cd app/api && pip install -e .[dev]`

## 🛠️ Быстрые исправления

### Перед каждым PR запускай локально:

```bash
# 1. Проверь код
cd /workspaces/mirai-agent
ruff check app/ --output-format=github
black --check app/
mypy app/ --ignore-missing-imports --no-strict-optional

# 2. Исправь автоматически
ruff check app/ --fix
black app/

# 3. Запусти тесты
pytest -q
cd app/api && pytest -v tests/
cd ../trader && pytest -v tests/
```

### Если CI все равно ломается:

1. **Проверь логи GitHub Actions** - там будет точная ошибка
2. **Синхронизируй локально:**
   ```bash
   git pull origin main
   pip install -r requirements.txt --upgrade
   ```
3. **Протестируй именно те команды, которые выполняются в CI**

## 📋 Чеклист для Copilot Agent

Когда Copilot Agent создает PR, проверь:

- [ ] Все CI workflows используют Python 3.12
- [ ] Нет конфликтов в requirements.txt
- [ ] Новый код проходит `ruff check` и `black --check`
- [ ] Тесты проходят локально
- [ ] Не добавлены deprecated зависимости

## 🔄 Автоматические исправления

Эти команды можно запускать автоматически:

```bash
# Исправить форматирование
black app/
ruff check app/ --fix

# Обновить зависимости 
pip install -r requirements.txt --upgrade

# Запустить все тесты
pytest && cd app/api && pytest && cd ../trader && pytest
```

## 🚀 Результат

После этих исправлений CI должен:
- ✅ Проходить все 3 workflow (main CI, CI API, CI Trader)
- ✅ Использовать современные инструменты (ruff, black, mypy)
- ✅ Работать стабильно на Python 3.12
- ✅ Автоматически исправлять простые ошибки форматирования

Если что-то сломается - запусти команды из раздела "Быстрые исправления" и создай новый коммит.
