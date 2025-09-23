#!/bin/bash

# 🚀 Mirai Agent - Quick Start Script
# Автоматически загружает API ключи и запускает автономного агента

set -e

echo "🤖 === MIRAI AUTONOMOUS AGENT - QUICK START ==="
echo "🔑 Загрузка API ключей из .env файла..."

# Загрузка переменных окружения
if [ -f "/root/mirai-agent/.env" ]; then
    export $(cat /root/mirai-agent/.env | grep -v '^#' | xargs)
    echo "✅ Переменные окружения загружены"
else
    echo "❌ Файл .env не найден!"
    exit 1
fi

# Проверка критических API ключей
echo ""
echo "🔍 Проверка API ключей..."

if [ ! -z "$OPENAI_API_KEY" ]; then
    echo "✅ OpenAI API ключ: $(echo $OPENAI_API_KEY | cut -c1-20)..."
else
    echo "❌ OpenAI API ключ не найден!"
    exit 1
fi

if [ ! -z "$BINANCE_API_KEY" ]; then
    echo "✅ Binance API ключ: $(echo $BINANCE_API_KEY | cut -c1-15)..."
else
    echo "⚠️  Binance API ключ не найден (агент будет работать только с анализом)"
fi

if [ ! -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "✅ Telegram бот: $(echo $TELEGRAM_BOT_TOKEN | cut -c1-15)..."
else
    echo "⚠️  Telegram бот не настроен (уведомления отключены)"
fi

echo ""
echo "🛡️  Режим безопасности: SANDBOX_MODE=$AGENT_SANDBOX_MODE"
echo "💰 Максимальная позиция: $AGENT_MAX_POSITION_SIZE USDT"
echo "📉 Максимальная дневная потеря: $AGENT_MAX_DAILY_LOSS USDT"
echo ""

# Переход в директорию агента
cd /root/mirai-agent

# Проверка зависимостей
echo "📦 Проверка зависимостей..."
python3 -c "import openai; print('✅ OpenAI библиотека установлена')" 2>/dev/null || {
    echo "⚠️  Устанавливаю OpenAI библиотеку..."
    pip3 install openai
}

python3 -c "import requests; print('✅ Requests библиотека установлена')" 2>/dev/null || {
    echo "⚠️  Устанавливаю Requests библиотеку..."
    pip3 install requests
}

echo ""
echo "🎯 Выберите режим запуска:"
echo "1. Интерактивный режим (рекомендуется для первого запуска)"
echo "2. Анализ рынка BTC"
echo "3. Мониторинг всего рынка"
echo "4. Фоновый режим (непрерывная работа)"
echo "5. Кастомная цель"
echo ""

read -p "Ваш выбор (1-5): " choice

case $choice in
    1)
        echo "🔄 Запуск интерактивного режима..."
        python3 app/agent/run_agent.py --interactive
        ;;
    2)
        echo "📊 Запуск анализа BTC..."
        python3 app/agent/run_agent.py --objective "Analyze BTC market trends and identify trading opportunities"
        ;;
    3)
        echo "🌐 Запуск мониторинга рынка..."
        python3 app/agent/run_agent.py --objective "Monitor cryptocurrency market trends across top 10 cryptocurrencies"
        ;;
    4)
        echo "🔄 Запуск в фоновом режиме..."
        echo "Логи будут записываться в logs/agent.log"
        nohup python3 app/agent/run_agent.py --objective "Continuous market monitoring and trading" --continuous > logs/agent.log 2>&1 &
        echo "✅ Агент запущен в фоне. PID: $!"
        echo "📋 Для просмотра логов: tail -f logs/agent.log"
        echo "🛑 Для остановки: pkill -f 'run_agent.py'"
        ;;
    5)
        read -p "Введите вашу цель для агента: " custom_objective
        echo "🎯 Запуск с кастомной целью..."
        python3 app/agent/run_agent.py --objective "$custom_objective"
        ;;
    *)
        echo "❌ Неверный выбор! Запуск интерактивного режима..."
        python3 app/agent/run_agent.py --interactive
        ;;
esac

echo ""
echo "🎉 Готово! Агент запущен и работает автономно!"