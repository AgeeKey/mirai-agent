"""
Конфигурация автономного AI-агента Mirai
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class AgentConfig:
    """Конфигурация агента"""
    
    # OpenAI настройки
    openai_api_key: str = ""
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 1000
    
    # Ограничения безопасности
    max_iterations: int = 50
    max_position_size: float = 1000.0  # Максимальный размер позиции в USD
    max_daily_trades: int = 10
    dry_run_mode: bool = True  # По умолчанию тестовый режим
    
    # Торговые параметры
    default_symbols: List[str] = None
    risk_tolerance: float = 0.02  # 2% максимальный риск на сделку
    min_confidence: float = 0.7  # Минимальная уверенность для сделки
    
    # Временные ограничения
    trading_hours_start: str = "09:00"
    trading_hours_end: str = "17:00"
    timezone: str = "UTC"
    
    # Пути к файлам
    memory_db_path: str = "/root/mirai-agent/state/agent_memory.db"
    log_file_path: str = "/root/mirai-agent/logs/ai_agent.log"
    
    # API endpoints
    binance_api_url: str = "https://api.binance.com"
    news_api_key: str = ""
    
    def __post_init__(self):
        if self.default_symbols is None:
            self.default_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        
        # Загружаем из переменных окружения
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.news_api_key = os.getenv("NEWS_API_KEY", self.news_api_key)
        
        # Создаем директории если их нет
        os.makedirs(os.path.dirname(self.memory_db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)

# Предустановленные цели для агента
PREDEFINED_OBJECTIVES = {
    "market_analysis": """
    Провести комплексный анализ криптовалютного рынка по основным парам (BTC, ETH, ADA).
    Оценить текущие тренды, волатильность и торговые возможности.
    Предоставить рекомендации по торговой стратегии на ближайшие 24 часа.
    """,
    
    "risk_management": """
    Проанализировать текущий портфель с точки зрения управления рисками.
    Проверить распределение активов, размеры позиций и соответствие стратегии риск-менеджмента.
    Предложить корректировки если необходимо.
    """,
    
    "portfolio_optimization": """
    Оптимизировать портфель для достижения лучшего соотношения риск/доходность.
    Учесть корреляцию между активами, текущие рыночные условия и цели инвестора.
    Предложить конкретные действия по ребалансировке.
    """,
    
    "news_analysis": """
    Проанализировать последние новости криптовалютного рынка.
    Выявить факторы, которые могут повлиять на цены основных активов.
    Оценить влияние новостей на торговую стратегию.
    """,
    
    "automated_trading": """
    Запустить автоматическую торговлю на основе предварительно настроенных стратегий.
    Мониторить рыночные условия и выполнять сделки при выполнении критериев.
    Соблюдать строгие правила риск-менеджмента.
    """
}

# Шаблоны промптов для разных типов задач
PROMPT_TEMPLATES = {
    "task_generation": """
Ты автономный AI-агент для торговой платформы Mirai.

ТЕКУЩАЯ ЦЕЛЬ: {objective}
КОНТЕКСТ: {context}
ПАМЯТЬ: {memory_context}

На основе цели и контекста, создай список из 3-5 конкретных задач.
Каждая задача должна быть четкой и выполнимой.

Доступные инструменты:
- analyze_market_data(symbol): анализ рыночных данных
- calculate_risk_metrics(portfolio, position): расчет рисков  
- execute_trade(symbol, side, quantity): выполнение сделки
- check_portfolio(): проверка портфеля
- news_analysis(): анализ новостей
- technical_analysis(symbol): технический анализ

Ответь в формате JSON:
{{
    "tasks": [
        {{
            "description": "Конкретное описание задачи",
            "priority": 1-5,
            "tool": "название инструмента если нужен",
            "estimated_time": "время выполнения в минутах"
        }}
    ],
    "reasoning": "Обоснование выбора задач"
}}
""",

    "task_execution": """
Ты автономный AI-агент для торговой платформы Mirai.

ТЕКУЩАЯ ЦЕЛЬ: {objective}
ЗАДАЧА: {task_description}
КОНТЕКСТ: {memory_context}

Выполни задачу пошагово. Если нужно использовать инструменты, укажи их.

ВАЖНЫЕ ОГРАНИЧЕНИЯ:
- Всегда используй dry_run=True для торговых операций если не указано иное
- Максимальный риск на сделку: 2%
- Минимальная уверенность для сделки: 70%
- Максимальный размер позиции: $1000

Ответь в формате JSON:
{{
    "action": "описание выполненного действия",
    "tool_used": "название инструмента или null",
    "tool_params": {{"param": "value"}},
    "result": "результат выполнения",
    "confidence": 0.0-1.0,
    "risk_assessment": "оценка рисков",
    "next_steps": "что делать дальше",
    "success": true/false
}}
""",

    "risk_analysis": """
Проанализируй торговую операцию с точки зрения рисков:

ОПЕРАЦИЯ: {operation_details}
РАЗМЕР ПОЗИЦИИ: {position_size}
ПОРТФЕЛЬ: {portfolio_value}
ТЕКУЩИЙ РИСК: {current_risk}

Оцени:
1. Риск в процентах от портфеля
2. Соответствие стратегии риск-менеджмента
3. Рекомендации по корректировке

Ответь в формате JSON с полями: risk_percent, risk_level, recommendation, approved.
"""
}

# Правила безопасности
SAFETY_RULES = {
    "max_position_risk": 0.05,  # 5% максимум от портфеля на позицию
    "max_daily_loss": 0.10,     # 10% максимум потерь в день
    "min_portfolio_cash": 0.20,  # 20% минимум в кеше
    "max_leverage": 1.0,         # Без плеча по умолчанию
    "required_confirmations": [  # Операции требующие подтверждения
        "large_trade",   # Крупные сделки
        "high_risk",     # Высокорисковые операции
        "real_money"     # Реальные деньги (не dry-run)
    ]
}

# Расписание работы агента
AGENT_SCHEDULE = {
    "market_analysis": "*/30 * * * *",    # Каждые 30 минут
    "portfolio_check": "0 */4 * * *",     # Каждые 4 часа
    "risk_assessment": "0 9,17 * * *",    # 9:00 и 17:00
    "news_analysis": "0 8,12,18 * * *",   # 8:00, 12:00, 18:00
    "backup_memory": "0 2 * * *"          # 2:00 каждый день
}