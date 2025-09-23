#!/bin/bash

# 🤖 Mirai Autonomous Agent - Quick Setup Script
# Автоматизация ручных задач настройки

set -e

echo "🤖 === MIRAI AUTONOMOUS AGENT SETUP ==="
echo "🔧 Автоматическая настройка компонентов..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода с цветом
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Проверка и создание необходимых директорий
print_info "Создание необходимых директорий..."
mkdir -p /root/mirai-agent/logs
mkdir -p /root/mirai-agent/state  
mkdir -p /root/mirai-agent/reports
print_status "Директории созданы"

# Проверка Python зависимостей
print_info "Проверка Python зависимостей..."

check_python_package() {
    if python3 -c "import $1" 2>/dev/null; then
        print_status "$1 уже установлен"
        return 0
    else
        print_warning "$1 не найден, устанавливаю..."
        pip3 install $2
        return $?
    fi
}

# Установка основных зависимостей
check_python_package "openai" "openai"
check_python_package "requests" "requests"
check_python_package "pandas" "pandas"
check_python_package "numpy" "numpy"

# Проверка дополнительных торговых зависимостей
print_info "Установка торговых зависимостей..."
pip3 install yfinance binance-connector python-binance 2>/dev/null || true

# Проверка OpenAI API ключа
print_info "Проверка настройки OpenAI API..."
if [ -z "$OPENAI_API_KEY" ]; then
    print_warning "OpenAI API ключ не настроен!"
    echo ""
    echo "🔑 Для настройки API ключа выполните:"
    echo "   export OPENAI_API_KEY='your-openai-api-key-here'"
    echo ""
    echo "📖 Получить ключ: https://platform.openai.com/api-keys"
    echo ""
    read -p "Хотите ввести API ключ сейчас? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Введите ваш OpenAI API ключ: " api_key
        export OPENAI_API_KEY="$api_key"
        echo "export OPENAI_API_KEY='$api_key'" >> ~/.bashrc
        print_status "OpenAI API ключ настроен"
    else
        print_warning "Настройте API ключ позже!"
    fi
else
    print_status "OpenAI API ключ найден"
fi

# Проверка Binance API (опционально)
print_info "Проверка настройки Binance API..."
if [ -z "$BINANCE_API_KEY" ]; then
    print_warning "Binance API ключи не настроены (опционально)"
    echo ""
    echo "🏦 Для реальной торговли настройте Binance API:"
    echo "   export BINANCE_API_KEY='your-binance-api-key'"
    echo "   export BINANCE_API_SECRET='your-binance-secret'"
    echo "   export BINANCE_TESTNET='true'  # Для тестовой сети"
    echo ""
    read -p "Хотите настроить Binance API сейчас? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Введите Binance API Key: " binance_key
        read -p "Введите Binance API Secret: " binance_secret
        read -p "Использовать testnet? (y/n): " -n 1 -r testnet
        echo
        
        export BINANCE_API_KEY="$binance_key"
        export BINANCE_API_SECRET="$binance_secret"
        echo "export BINANCE_API_KEY='$binance_key'" >> ~/.bashrc
        echo "export BINANCE_API_SECRET='$binance_secret'" >> ~/.bashrc
        
        if [[ $testnet =~ ^[Yy]$ ]]; then
            export BINANCE_TESTNET='true'
            echo "export BINANCE_TESTNET='true'" >> ~/.bashrc
            print_status "Binance API настроен (testnet режим)"
        else
            print_status "Binance API настроен (live режим)"
        fi
    fi
else
    print_status "Binance API ключи найдены"
fi

# Создание базы данных SQLite
print_info "Инициализация базы данных..."
cd /root/mirai-agent
python3 -c "
import sqlite3
import os

db_path = 'state/mirai.db'
if not os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Создание таблицы памяти агента
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            task_type TEXT,
            content TEXT,
            result TEXT,
            embedding TEXT
        )
    ''')
    
    # Создание таблицы решений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trading_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            symbol TEXT,
            action TEXT,
            amount REAL,
            price REAL,
            reasoning TEXT,
            executed BOOLEAN DEFAULT FALSE
        )
    ''')
    
    conn.commit()
    conn.close()
    print('✅ База данных создана')
else:
    print('✅ База данных уже существует')
"
print_status "База данных инициализирована"

# Настройка прав доступа
print_info "Настройка прав доступа..."
chmod +x /root/mirai-agent/app/agent/run_agent.py
chmod +x /root/mirai-agent/scripts/setup_autonomous_agent.sh
print_status "Права доступа настроены"

# Проверка функциональности
print_info "Тестирование системы..."
cd /root/mirai-agent

# Тест импорта основных модулей
python3 -c "
try:
    import sys
    sys.path.insert(0, 'app/agent')
    from autonomous_agent import MiraiAgent
    from agent_config import AgentConfig
    from trading_tools import AdvancedTradingTools
    from safety_system import AgentSafetySystem
    print('✅ Все модули агента загружены успешно')
except Exception as e:
    print(f'❌ Ошибка импорта: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    print_status "Тестирование прошло успешно"
else
    print_error "Ошибка при тестировании системы"
    exit 1
fi

# Создание example конфигурации
print_info "Создание примера конфигурации..."
cat > /root/mirai-agent/.env.example << EOF
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Binance API Configuration  
BINANCE_API_KEY=your-binance-api-key
BINANCE_API_SECRET=your-binance-secret
BINANCE_TESTNET=true

# Agent Configuration
AGENT_SANDBOX_MODE=true
AGENT_MAX_POSITION_SIZE=100.0
AGENT_MAX_DAILY_LOSS=50.0
AGENT_RISK_TOLERANCE=MEDIUM

# Database Configuration (for production)
DATABASE_URL=sqlite:///state/mirai.db
# DATABASE_URL=postgresql://user:password@localhost/mirai_agent

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/agent.log
EOF

print_status "Пример конфигурации создан (.env.example)"

# Финальная информация
echo ""
echo "🎉 === НАСТРОЙКА ЗАВЕРШЕНА ==="
echo ""
print_status "Автономный AI-агент готов к запуску!"
echo ""
echo "📋 Что было настроено:"
echo "   ✅ Python зависимости установлены"
echo "   ✅ Структура директорий создана"
echo "   ✅ База данных инициализирована" 
echo "   ✅ Права доступа настроены"
echo "   ✅ Система протестирована"
echo ""
echo "🚀 Команды для запуска:"
echo "   Интерактивный режим: python3 app/agent/run_agent.py --interactive"
echo "   Анализ рынка:       python3 app/agent/run_agent.py --objective 'analyze BTC trends'"
echo "   Фоновый режим:      nohup python3 app/agent/run_agent.py --continuous &"
echo ""
echo "📖 Документация: docs/AUTONOMOUS_AGENT_SETUP.md"
echo ""

# Проверка критических компонентов
if [ -z "$OPENAI_API_KEY" ]; then
    print_warning "ВНИМАНИЕ: OpenAI API ключ не настроен!"
    echo "   Настройте перед запуском: export OPENAI_API_KEY='your-key'"
fi

if [ -z "$BINANCE_API_KEY" ]; then
    print_info "Binance API не настроен - агент будет работать только с анализом"
fi

echo ""
print_info "Агент готов к работе! 🤖✨"