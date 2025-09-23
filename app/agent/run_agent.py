#!/usr/bin/env python3
"""
Запуск автономного AI-агента Mirai
Основной исполняемый файл
"""

import os
import sys
import asyncio
import argparse
import json
import logging
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from autonomous_agent import MiraiAgent
    from agent_config import AgentConfig, PREDEFINED_OBJECTIVES
    from trading_tools import AdvancedTradingTools
    from safety_system import create_safety_system, create_sandbox
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что все файлы агента находятся в правильных директориях")
    sys.exit(1)

def setup_logging(log_level=logging.INFO):
    """Настройка логирования"""
    log_dir = "/root/mirai-agent/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'{log_dir}/mirai_agent.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def print_banner():
    """Печать баннера"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🤖 MIRAI AGENT 2024                       ║
    ║              Автономный AI-агент для торговли                ║
    ║                                                              ║
    ║  🧠 Powered by OpenAI GPT-4                                  ║
    ║  📊 Advanced Trading Analytics                               ║
    ║  🛡️  Multi-layer Safety System                               ║
    ║  🏖️  Sandbox Mode Enabled                                    ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_requirements():
    """Проверка требований"""
    print("🔍 Проверка требований...")
    
    # Проверка OpenAI API ключа
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY не установлен!")
        print("   Установите переменную окружения:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return False
    else:
        print("✅ OpenAI API ключ найден")
    
    # Проверка зависимостей
    try:
        import openai
        print("✅ OpenAI библиотека доступна")
    except ImportError:
        print("❌ OpenAI библиотека не установлена")
        print("   Установите: pip install openai")
        return False
    
    # Проверка директорий
    required_dirs = [
        "/root/mirai-agent/logs",
        "/root/mirai-agent/state"
    ]
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"📁 Создана директория: {dir_path}")
        else:
            print(f"✅ Директория существует: {dir_path}")
    
    return True

def display_objectives():
    """Отображение доступных целей"""
    print("\\n📋 Доступные цели для агента:")
    print("═" * 60)
    
    for key, objective in PREDEFINED_OBJECTIVES.items():
        print(f"\\n🎯 {key}:")
        print(f"   {objective.strip()}")
    
    print("\\n💡 Или введите свою собственную цель")

def get_user_objective():
    """Получение цели от пользователя"""
    display_objectives()
    
    print("\\n" + "═" * 60)
    choice = input("Выберите цель (введите ключ или 'custom'): ").strip()
    
    if choice in PREDEFINED_OBJECTIVES:
        return PREDEFINED_OBJECTIVES[choice]
    elif choice.lower() == 'custom':
        print("\\nВведите собственную цель для агента:")
        custom_objective = input("> ").strip()
        return custom_objective
    else:
        print(f"❌ Неизвестная цель: {choice}")
        return get_user_objective()

def display_safety_status(safety_system):
    """Отображение статуса безопасности"""
    status = safety_system.get_safety_status()
    
    print("\\n🛡️  Статус системы безопасности:")
    print("═" * 50)
    print(f"🏖️  Режим песочницы: {'ВКЛЮЧЕН' if status['sandboxed'] else 'ОТКЛЮЧЕН'}")
    print(f"📊 Сделок сегодня: {status['daily_limits']['trades_today']}/{status['daily_limits']['max_trades']}")
    print(f"💰 Объем сегодня: ${status['daily_limits']['volume_today']:.2f}/${status['daily_limits']['max_volume']:.2f}")
    print(f"⚠️  Нарушений риска: {status['session_stats']['risk_violations']}")
    
    if status['pending_confirmations'] > 0:
        print(f"⏳ Ожидающих подтверждений: {status['pending_confirmations']}")

async def run_interactive_mode(agent):
    """Интерактивный режим"""
    print("\\n🎮 Интерактивный режим запущен")
    print("Команды:")
    print("  'status' - статус агента")
    print("  'safety' - статус безопасности") 
    print("  'stop' - остановка агента")
    print("  'objective <text>' - новая цель")
    print("  'help' - помощь")
    
    while agent.running:
        try:
            command = input("\\n> ").strip().lower()
            
            if command == 'stop':
                agent.stop_agent()
                print("🛑 Агент остановлен")
                break
            elif command == 'status':
                print(f"📊 Агент {'работает' if agent.running else 'остановлен'}")
                print(f"🎯 Цель: {agent.current_objective}")
                print(f"📋 Задач в очереди: {len(agent.task_queue)}")
            elif command == 'safety':
                display_safety_status(agent.safety_system)
            elif command.startswith('objective '):
                new_objective = command[10:]
                agent.set_objective(new_objective)
                print(f"🎯 Новая цель установлена: {new_objective}")
            elif command == 'help':
                print("📖 Доступные команды:")
                print("  status, safety, stop, objective <text>, help")
            else:
                print("❓ Неизвестная команда. Введите 'help' для справки")
        
        except KeyboardInterrupt:
            print("\\n🛑 Остановка агента...")
            agent.stop_agent()
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")

async def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description="Mirai AI Trading Agent")
    parser.add_argument("--objective", type=str, help="Цель для агента")
    parser.add_argument("--max-iterations", type=int, default=20, help="Максимум итераций")
    parser.add_argument("--interactive", action="store_true", help="Интерактивный режим")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Режим тестирования")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       default="INFO", help="Уровень логирования")
    
    args = parser.parse_args()
    
    # Настройка логирования
    setup_logging(getattr(logging, args.log_level))
    
    # Печать баннера
    print_banner()
    
    # Проверка требований
    if not check_requirements():
        print("\\n❌ Не все требования выполнены. Завершение.")
        return 1
    
    try:
        # Создание конфигурации
        config = AgentConfig(
            dry_run_mode=args.dry_run,
            max_iterations=args.max_iterations
        )
        
        # Создание системы безопасности
        safety_system = create_safety_system({
            "max_position_size": 1000.0,
            "max_daily_trades": 10,
            "real_trading_enabled": False
        })
        
        # Создание агента
        agent = MiraiAgent(
            openai_api_key=config.openai_api_key,
            max_iterations=args.max_iterations
        )
        
        # Добавляем систему безопасности к агенту
        agent.safety_system = safety_system
        agent.sandbox = create_sandbox(safety_system)
        
        # Отображение статуса безопасности
        display_safety_status(safety_system)
        
        # Получение цели
        if args.objective:
            objective = args.objective
        else:
            objective = get_user_objective()
        
        # Установка цели
        agent.set_objective(objective)
        
        print(f"\\n🚀 Запуск агента с целью:")
        print(f"🎯 {objective}")
        print(f"⚙️  Максимум итераций: {args.max_iterations}")
        print(f"🛡️  Режим: {'Тестирование' if args.dry_run else 'Продакшн'}")
        
        # Запуск
        if args.interactive:
            # Создаем задачу для агента
            agent_task = asyncio.create_task(agent.run_agent_loop())
            # Создаем задачу для интерактивного режима
            interactive_task = asyncio.create_task(run_interactive_mode(agent))
            
            # Ждем завершения любой из задач
            done, pending = await asyncio.wait(
                [agent_task, interactive_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Отменяем оставшиеся задачи
            for task in pending:
                task.cancel()
        else:
            # Обычный запуск
            await agent.run_agent_loop()
        
        print("\\n✅ Агент завершил работу успешно")
        return 0
        
    except KeyboardInterrupt:
        print("\\n⏹️  Остановка агента пользователем")
        return 0
    except Exception as e:
        print(f"\\n❌ Критическая ошибка: {e}")
        logging.exception("Критическая ошибка агента")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())