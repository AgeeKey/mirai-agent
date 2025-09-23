"""
Автономный AI-агент для торговой платформы Mirai
Основан на архитектуре BabyAGI с OpenAI GPT-4
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncio
from dataclasses import dataclass
import sqlite3

# Добавляем путь для импорта модулей Mirai
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import openai
except ImportError:
    print("OpenAI не установлен. Установите: pip install openai")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/mirai-agent/logs/ai_agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('MiraiAgent')

@dataclass
class Task:
    """Задача для выполнения агентом"""
    id: str
    description: str
    priority: int = 1
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[str] = None
    created_at: str = ""
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

class MiraiMemory:
    """Простая система памяти для агента"""
    
    def __init__(self, db_path: str = "/root/mirai-agent/state/agent_memory.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных памяти"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    importance REAL DEFAULT 0.5,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    reasoning TEXT,
                    confidence REAL,
                    result TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("База данных памяти инициализирована")
        except Exception as e:
            logger.error(f"Ошибка инициализации памяти: {e}")
    
    def store_memory(self, memory_type: str, content: str, metadata: Dict = None, importance: float = 0.5):
        """Сохранение воспоминания"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO memories (type, content, metadata, importance)
                VALUES (?, ?, ?, ?)
            ''', (memory_type, content, json.dumps(metadata or {}), importance))
            
            conn.commit()
            conn.close()
            logger.info(f"Сохранено воспоминание типа {memory_type}")
        except Exception as e:
            logger.error(f"Ошибка сохранения памяти: {e}")
    
    def retrieve_memories(self, memory_type: str = None, limit: int = 10) -> List[Dict]:
        """Получение воспоминаний"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if memory_type:
                cursor.execute('''
                    SELECT content, metadata, importance, timestamp 
                    FROM memories 
                    WHERE type = ? 
                    ORDER BY importance DESC, timestamp DESC 
                    LIMIT ?
                ''', (memory_type, limit))
            else:
                cursor.execute('''
                    SELECT content, metadata, importance, timestamp 
                    FROM memories 
                    ORDER BY importance DESC, timestamp DESC 
                    LIMIT ?
                ''', (limit,))
            
            memories = []
            for row in cursor.fetchall():
                memories.append({
                    'content': row[0],
                    'metadata': json.loads(row[1]),
                    'importance': row[2],
                    'timestamp': row[3]
                })
            
            conn.close()
            return memories
        except Exception as e:
            logger.error(f"Ошибка получения памяти: {e}")
            return []

class TradingTools:
    """Инструменты для торговой деятельности агента"""
    
    @staticmethod
    def analyze_market_data(symbol: str) -> Dict[str, Any]:
        """Анализ рыночных данных"""
        # Здесь должен быть реальный анализ через Binance API
        # Пока возвращаем мок данные
        import random
        
        price = random.uniform(40000, 60000)
        change_24h = random.uniform(-5, 5)
        volume = random.uniform(1000000, 5000000)
        
        return {
            "symbol": symbol,
            "price": price,
            "change_24h": change_24h,
            "volume": volume,
            "trend": "bullish" if change_24h > 0 else "bearish",
            "volatility": abs(change_24h),
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def calculate_risk_metrics(portfolio_value: float, position_size: float) -> Dict[str, Any]:
        """Расчет метрик риска"""
        risk_percentage = (position_size / portfolio_value) * 100
        
        return {
            "position_risk_percent": risk_percentage,
            "risk_level": "low" if risk_percentage < 2 else "medium" if risk_percentage < 5 else "high",
            "max_loss": position_size * 0.02,  # 2% stop-loss
            "recommendation": "reduce" if risk_percentage > 5 else "acceptable"
        }
    
    @staticmethod
    def execute_trade(symbol: str, side: str, quantity: float, dry_run: bool = True) -> Dict[str, Any]:
        """Выполнение торговой операции"""
        if dry_run:
            logger.info(f"DRY RUN: {side} {quantity} {symbol}")
            return {
                "status": "dry_run_success",
                "order_id": f"dry_run_{int(time.time())}",
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "message": "Операция выполнена в режиме тестирования"
            }
        else:
            # Здесь должна быть реальная интеграция с Binance
            logger.warning("Реальная торговля не реализована в демо версии")
            return {
                "status": "not_implemented",
                "message": "Реальная торговля требует настройки Binance API"
            }

class MiraiAgent:
    """Основной класс автономного AI-агента"""
    
    def __init__(self, openai_api_key: str = None, max_iterations: int = 10):
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API ключ не найден. Установите OPENAI_API_KEY")
        
        # Инициализация OpenAI клиента
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
        
        self.memory = MiraiMemory()
        self.tools = TradingTools()
        self.max_iterations = max_iterations
        self.task_queue: List[Task] = []
        self.current_objective = ""
        self.running = False
        
        logger.info("Mirai Agent инициализирован")
    
    def set_objective(self, objective: str):
        """Установка основной цели"""
        self.current_objective = objective
        logger.info(f"Новая цель: {objective}")
        
        # Сохраняем цель в память
        self.memory.store_memory(
            "objective", 
            objective, 
            {"set_at": datetime.now().isoformat()},
            importance=1.0
        )
    
    def generate_tasks(self, context: str) -> List[Task]:
        """Генерация новых задач на основе контекста"""
        try:
            # Получаем релевантные воспоминания
            memories = self.memory.retrieve_memories(limit=5)
            memory_context = "\\n".join([m['content'] for m in memories])
            
            prompt = f"""
Ты автономный AI-агент для торговой платформы Mirai.

ТЕКУЩАЯ ЦЕЛЬ: {self.current_objective}

КОНТЕКСТ: {context}

ПАМЯТЬ (последние действия):
{memory_context}

На основе цели и контекста, создай список из 3-5 конкретных задач для достижения цели.
Каждая задача должна быть четкой и выполнимой.

Доступные инструменты:
- analyze_market_data(symbol): анализ рыночных данных
- calculate_risk_metrics(portfolio, position): расчет рисков
- execute_trade(symbol, side, quantity): выполнение сделки
- check_portfolio(): проверка портфеля
- news_analysis(): анализ новостей

Ответь в формате JSON:
{{
    "tasks": [
        {{
            "description": "Конкретное описание задачи",
            "priority": 1-5,
            "tool": "название инструмента если нужен"
        }}
    ],
    "reasoning": "Обоснование выбора задач"
}}
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            result = json.loads(response.choices[0].message.content)
            
            tasks = []
            for i, task_data in enumerate(result.get("tasks", [])):
                task = Task(
                    id=f"task_{int(time.time())}_{i}",
                    description=task_data["description"],
                    priority=task_data.get("priority", 1)
                )
                tasks.append(task)
            
            logger.info(f"Сгенерировано {len(tasks)} задач: {result.get('reasoning', '')}")
            return tasks
            
        except Exception as e:
            logger.error(f"Ошибка генерации задач: {e}")
            return []
    
    def execute_task(self, task: Task) -> str:
        """Выполнение конкретной задачи"""
        try:
            task.status = "in_progress"
            
            # Получаем контекст из памяти
            memories = self.memory.retrieve_memories(limit=3)
            memory_context = "\\n".join([m['content'] for m in memories])
            
            prompt = f"""
Ты автономный AI-агент для торговой платформы Mirai.

ТЕКУЩАЯ ЦЕЛЬ: {self.current_objective}
ЗАДАЧА ДЛЯ ВЫПОЛНЕНИЯ: {task.description}

КОНТЕКСТ ИЗ ПАМЯТИ:
{memory_context}

Выполни задачу пошагово. Если нужно использовать инструменты, укажи их.

Доступные инструменты:
- analyze_market_data(symbol): анализ рыночных данных для символа
- calculate_risk_metrics(portfolio_value, position_size): расчет рисков
- execute_trade(symbol, side, quantity, dry_run=True): выполнение сделки
- check_portfolio(): проверка текущего портфеля

Ответь в формате JSON:
{{
    "action": "описание выполненного действия",
    "tool_used": "название инструмента или null",
    "tool_params": {{"param": "value"}},
    "result": "результат выполнения",
    "next_steps": "что делать дальше",
    "success": true/false
}}
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Выполнение инструментов если указаны
            tool_result = None
            if result.get("tool_used"):
                tool_result = self._execute_tool(
                    result["tool_used"], 
                    result.get("tool_params", {})
                )
            
            # Обновление результата с учетом выполнения инструмента
            if tool_result:
                result["tool_result"] = tool_result
            
            task.result = json.dumps(result)
            task.status = "completed" if result.get("success") else "failed"
            task.completed_at = datetime.now().isoformat()
            
            # Сохраняем результат в память
            self.memory.store_memory(
                "task_execution",
                f"Задача: {task.description} | Результат: {result['result']}",
                {"task_id": task.id, "success": result.get("success")},
                importance=0.8 if result.get("success") else 0.3
            )
            
            logger.info(f"Задача выполнена: {task.description} -> {result['result']}")
            return result["result"]
            
        except Exception as e:
            task.status = "failed"
            task.result = f"Ошибка: {str(e)}"
            logger.error(f"Ошибка выполнения задачи {task.description}: {e}")
            return f"Ошибка: {str(e)}"
    
    def _execute_tool(self, tool_name: str, params: Dict) -> Any:
        """Выполнение конкретного инструмента"""
        try:
            if tool_name == "analyze_market_data":
                return self.tools.analyze_market_data(params.get("symbol", "BTCUSDT"))
            elif tool_name == "calculate_risk_metrics":
                return self.tools.calculate_risk_metrics(
                    params.get("portfolio_value", 10000),
                    params.get("position_size", 1000)
                )
            elif tool_name == "execute_trade":
                return self.tools.execute_trade(
                    params.get("symbol", "BTCUSDT"),
                    params.get("side", "BUY"),
                    params.get("quantity", 0.01),
                    params.get("dry_run", True)
                )
            elif tool_name == "check_portfolio":
                # Мок данные портфеля
                return {
                    "total_value": 10000.0,
                    "positions": [
                        {"symbol": "BTCUSDT", "quantity": 0.2, "value": 8000},
                        {"symbol": "ETHUSDT", "quantity": 2.0, "value": 2000}
                    ],
                    "cash": 0.0
                }
            else:
                logger.warning(f"Неизвестный инструмент: {tool_name}")
                return None
        except Exception as e:
            logger.error(f"Ошибка выполнения инструмента {tool_name}: {e}")
            return None
    
    def prioritize_tasks(self):
        """Приоритизация задач в очереди"""
        self.task_queue.sort(key=lambda t: (t.priority, t.created_at), reverse=True)
    
    async def run_agent_loop(self):
        """Основной цикл работы агента"""
        self.running = True
        iteration = 0
        
        logger.info("🚀 Запуск автономного агента Mirai")
        
        while self.running and iteration < self.max_iterations:
            try:
                iteration += 1
                logger.info(f"🔄 Итерация {iteration}/{self.max_iterations}")
                
                # 1. Если нет задач, генерируем новые
                if not self.task_queue:
                    if self.current_objective:
                        context = f"Итерация {iteration}. Нужно продолжить работу над целью."
                        new_tasks = self.generate_tasks(context)
                        self.task_queue.extend(new_tasks)
                    else:
                        logger.warning("Нет цели и задач. Останавливаем агента.")
                        break
                
                # 2. Приоритизация задач
                self.prioritize_tasks()
                
                # 3. Выполнение следующей задачи
                if self.task_queue:
                    current_task = self.task_queue.pop(0)
                    logger.info(f"📋 Выполняю задачу: {current_task.description}")
                    
                    result = self.execute_task(current_task)
                    
                    # 4. Анализ результата и генерация новых задач если нужно
                    if "продолжить" in result.lower() or "дальше" in result.lower():
                        context = f"Завершена задача: {current_task.description}. Результат: {result}"
                        new_tasks = self.generate_tasks(context)
                        self.task_queue.extend(new_tasks)
                
                # Небольшая пауза между итерациями
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Ошибка в цикле агента: {e}")
                await asyncio.sleep(5)
        
        logger.info("🏁 Агент завершил работу")
        self.running = False
    
    def stop_agent(self):
        """Остановка агента"""
        self.running = False
        logger.info("🛑 Получен сигнал остановки агента")

# Основная функция для запуска агента
async def main():
    """Главная функция запуска"""
    try:
        # Проверяем наличие API ключа
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY не установлен!")
            print("Установите переменную окружения:")
            print("export OPENAI_API_KEY='your-api-key'")
            return
        
        # Создаем агента
        agent = MiraiAgent(api_key, max_iterations=20)
        
        # Устанавливаем цель
        objective = """
        Проанализировать криптовалютный рынок BTC/USDT и ETH/USDT, 
        оценить риски текущего портфеля, 
        и предложить оптимальную торговую стратегию на основе анализа.
        Приоритет - безопасность и управление рисками.
        """
        
        agent.set_objective(objective)
        
        print("🤖 Автономный агент Mirai готов к работе!")
        print(f"🎯 Цель: {objective}")
        print("🚀 Запуск...")
        
        # Запускаем агента
        await agent.run_agent_loop()
        
    except KeyboardInterrupt:
        print("\\n⏹️  Остановка агента пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())