"""
Mirai Agent - AI Safety Rules Extension (Day 5)
Расширенная система безопасности AI с правилами для экономических событий
"""
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import sqlite3
import sys
import os

# Добавляем пути для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventSeverity(Enum):
    """Серьезность экономического события"""
    LOW = "low"           # Малое влияние
    MEDIUM = "medium"     # Среднее влияние  
    HIGH = "high"         # Высокое влияние
    CRITICAL = "critical" # Критическое влияние

class EventCategory(Enum):
    """Категории экономических событий"""
    MONETARY_POLICY = "monetary_policy"  # Денежная политика
    INFLATION = "inflation"              # Инфляция
    EMPLOYMENT = "employment"            # Занятость
    GDP = "gdp"                         # ВВП
    TRADE = "trade"                     # Торговля
    GEOPOLITICAL = "geopolitical"       # Геополитика
    MARKET_STRUCTURE = "market_structure" # Структура рынка
    CRYPTO_SPECIFIC = "crypto_specific"  # Крипто-специфичные

class SafetyAction(Enum):
    """Действия системы безопасности"""
    MONITOR = "monitor"           # Только мониторинг
    REDUCE_EXPOSURE = "reduce"    # Снижение экспозиции
    HALT_TRADING = "halt"         # Остановка торговли
    EMERGENCY_EXIT = "emergency"  # Экстренный выход
    BLACKOUT = "blackout"         # Полная блокировка

@dataclass
class EconomicEvent:
    """Экономическое событие"""
    name: str
    category: EventCategory
    severity: EventSeverity
    scheduled_time: datetime
    actual_time: Optional[datetime] = None
    description: str = ""
    impact_currencies: List[str] = None
    volatility_factor: float = 1.0
    duration_hours: int = 4  # Длительность влияния
    
    def __post_init__(self):
        if self.impact_currencies is None:
            self.impact_currencies = ["ALL"]

@dataclass
class SafetyRule:
    """Правило безопасности"""
    name: str
    description: str
    event_patterns: List[str]  # Паттерны названий событий
    categories: List[EventCategory]
    severity_threshold: EventSeverity
    action: SafetyAction
    lead_time_hours: float = 1.0  # За сколько часов до события активировать
    duration_hours: float = 4.0   # Сколько часов действует после события
    conditions: Dict[str, Any] = None  # Дополнительные условия
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = {}

class EconomicCalendar:
    """Календарь экономических событий"""
    
    def __init__(self):
        self.events: Dict[str, EconomicEvent] = {}
        self.db_path = "/root/mirai-agent/state/mirai.db"
        self._init_database()
        
        # Предустановленные критические события
        self._load_critical_events()
    
    def _init_database(self):
        """Инициализация таблиц для экономических событий"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS economic_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    scheduled_time TEXT NOT NULL,
                    actual_time TEXT,
                    description TEXT,
                    impact_currencies TEXT,
                    volatility_factor REAL DEFAULT 1.0,
                    duration_hours INTEGER DEFAULT 4,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS safety_activations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name TEXT NOT NULL,
                    event_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    activated_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    reason TEXT,
                    active BOOLEAN DEFAULT 1
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Ошибка инициализации БД календаря: {e}")
    
    def _load_critical_events(self):
        """Загрузка критических событий"""
        critical_events = [
            # Federal Reserve (США)
            EconomicEvent(
                name="FOMC Interest Rate Decision",
                category=EventCategory.MONETARY_POLICY,
                severity=EventSeverity.CRITICAL,
                scheduled_time=datetime(2024, 3, 20, 19, 0),  # 2:00 PM ET
                description="Federal Reserve interest rate decision",
                impact_currencies=["USD", "USDT", "USDC"],
                volatility_factor=3.0,
                duration_hours=6
            ),
            
            EconomicEvent(
                name="FOMC Press Conference",
                category=EventCategory.MONETARY_POLICY,
                severity=EventSeverity.CRITICAL,
                scheduled_time=datetime(2024, 3, 20, 19, 30),  # 2:30 PM ET
                description="Jerome Powell press conference",
                impact_currencies=["USD", "USDT"],
                volatility_factor=2.5,
                duration_hours=4
            ),
            
            # Inflation Data (США)
            EconomicEvent(
                name="US CPI",
                category=EventCategory.INFLATION,
                severity=EventSeverity.HIGH,
                scheduled_time=datetime(2024, 3, 12, 13, 30),  # 8:30 AM ET
                description="Consumer Price Index",
                impact_currencies=["USD", "USDT"],
                volatility_factor=2.0,
                duration_hours=3
            ),
            
            EconomicEvent(
                name="US Core CPI",
                category=EventCategory.INFLATION,
                severity=EventSeverity.HIGH,
                scheduled_time=datetime(2024, 3, 12, 13, 30),
                description="Core Consumer Price Index (ex food & energy)",
                impact_currencies=["USD", "USDT"],
                volatility_factor=2.2,
                duration_hours=3
            ),
            
            EconomicEvent(
                name="US PPI",
                category=EventCategory.INFLATION,
                severity=EventSeverity.MEDIUM,
                scheduled_time=datetime(2024, 3, 14, 13, 30),
                description="Producer Price Index",
                impact_currencies=["USD"],
                volatility_factor=1.5,
                duration_hours=2
            ),
            
            # Employment (США)
            EconomicEvent(
                name="US Non-Farm Payrolls",
                category=EventCategory.EMPLOYMENT,
                severity=EventSeverity.HIGH,
                scheduled_time=datetime(2024, 3, 8, 13, 30),
                description="Monthly job creation data",
                impact_currencies=["USD", "USDT"],
                volatility_factor=2.0,
                duration_hours=4
            ),
            
            EconomicEvent(
                name="US Unemployment Rate",
                category=EventCategory.EMPLOYMENT,
                severity=EventSeverity.MEDIUM,
                scheduled_time=datetime(2024, 3, 8, 13, 30),
                description="Monthly unemployment percentage",
                impact_currencies=["USD"],
                volatility_factor=1.3,
                duration_hours=2
            ),
            
            # European Central Bank
            EconomicEvent(
                name="ECB Interest Rate Decision",
                category=EventCategory.MONETARY_POLICY,
                severity=EventSeverity.HIGH,
                scheduled_time=datetime(2024, 3, 7, 13, 45),
                description="European Central Bank rate decision",
                impact_currencies=["EUR", "USDT"],
                volatility_factor=2.0,
                duration_hours=4
            ),
            
            # Crypto-specific events
            EconomicEvent(
                name="Bitcoin ETF Decision",
                category=EventCategory.CRYPTO_SPECIFIC,
                severity=EventSeverity.HIGH,
                scheduled_time=datetime(2024, 3, 15, 21, 0),
                description="SEC Bitcoin ETF approval/rejection",
                impact_currencies=["BTC", "ETH", "USDT"],
                volatility_factor=3.0,
                duration_hours=8
            ),
            
            EconomicEvent(
                name="CFTC Crypto Regulation",
                category=EventCategory.CRYPTO_SPECIFIC,
                severity=EventSeverity.MEDIUM,
                scheduled_time=datetime(2024, 3, 18, 15, 0),
                description="CFTC cryptocurrency regulation announcement",
                impact_currencies=["BTC", "ETH", "ALL"],
                volatility_factor=1.8,
                duration_hours=6
            )
        ]
        
        for event in critical_events:
            self.events[event.name] = event
    
    async def add_event(self, event: EconomicEvent):
        """Добавление события в календарь"""
        self.events[event.name] = event
        
        # Сохранение в БД
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO economic_events 
                (name, category, severity, scheduled_time, description, 
                 impact_currencies, volatility_factor, duration_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.name,
                event.category.value,
                event.severity.value,
                event.scheduled_time.isoformat(),
                event.description,
                json.dumps(event.impact_currencies),
                event.volatility_factor,
                event.duration_hours
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Добавлено событие: {event.name}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения события: {e}")
    
    async def get_upcoming_events(self, hours_ahead: int = 24) -> List[EconomicEvent]:
        """Получение предстоящих событий"""
        now = datetime.now()
        future_time = now + timedelta(hours=hours_ahead)
        
        upcoming = []
        for event in self.events.values():
            if now <= event.scheduled_time <= future_time:
                upcoming.append(event)
        
        return sorted(upcoming, key=lambda e: e.scheduled_time)
    
    async def get_active_events(self) -> List[EconomicEvent]:
        """Получение текущих активных событий"""
        now = datetime.now()
        active = []
        
        for event in self.events.values():
            event_end = event.scheduled_time + timedelta(hours=event.duration_hours)
            if event.scheduled_time <= now <= event_end:
                active.append(event)
        
        return active

class AISafetyRulesEngine:
    """Расширенный движок правил безопасности AI"""
    
    def __init__(self):
        self.rules: Dict[str, SafetyRule] = {}
        self.calendar = EconomicCalendar()
        self.active_restrictions: Dict[str, Dict] = {}
        self.db_path = "/root/mirai-agent/state/mirai.db"
        
        # Загрузка предустановленных правил
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Загрузка правил безопасности по умолчанию"""
        
        # Правило 1: FOMC блэкаут
        fomc_rule = SafetyRule(
            name="FOMC_BLACKOUT",
            description="Полная остановка торговли во время решений FOMC",
            event_patterns=["FOMC", "Federal Reserve", "Interest Rate Decision"],
            categories=[EventCategory.MONETARY_POLICY],
            severity_threshold=EventSeverity.HIGH,
            action=SafetyAction.BLACKOUT,
            lead_time_hours=2.0,
            duration_hours=6.0,
            conditions={
                "min_volatility_factor": 2.0,
                "affected_pairs": ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
            }
        )
        
        # Правило 2: CPI осторожность
        cpi_rule = SafetyRule(
            name="CPI_CAUTION",
            description="Снижение экспозиции во время публикации CPI",
            event_patterns=["CPI", "Consumer Price", "Inflation"],
            categories=[EventCategory.INFLATION],
            severity_threshold=EventSeverity.MEDIUM,
            action=SafetyAction.REDUCE_EXPOSURE,
            lead_time_hours=1.0,
            duration_hours=3.0,
            conditions={
                "max_position_reduction": 0.5,
                "min_confidence_boost": 20
            }
        )
        
        # Правило 3: NFP halt
        nfp_rule = SafetyRule(
            name="NFP_HALT",
            description="Остановка торговли во время Non-Farm Payrolls",
            event_patterns=["Non-Farm Payrolls", "NFP", "Employment"],
            categories=[EventCategory.EMPLOYMENT],
            severity_threshold=EventSeverity.HIGH,
            action=SafetyAction.HALT_TRADING,
            lead_time_hours=0.5,
            duration_hours=4.0,
            conditions={
                "resume_delay_minutes": 30
            }
        )
        
        # Правило 4: Крипто-регуляции
        crypto_reg_rule = SafetyRule(
            name="CRYPTO_REGULATION_EMERGENCY",
            description="Экстренный выход при крипто-регуляциях",
            event_patterns=["ETF", "SEC", "CFTC", "Regulation", "Ban"],
            categories=[EventCategory.CRYPTO_SPECIFIC],
            severity_threshold=EventSeverity.MEDIUM,
            action=SafetyAction.EMERGENCY_EXIT,
            lead_time_hours=0.25,  # 15 минут
            duration_hours=8.0,
            conditions={
                "max_slippage": 0.02,
                "exit_chunks": 5
            }
        )
        
        # Правило 5: Геополитические события
        geopolitical_rule = SafetyRule(
            name="GEOPOLITICAL_MONITOR",
            description="Мониторинг геополитических событий",
            event_patterns=["War", "Sanctions", "Trade War", "Election"],
            categories=[EventCategory.GEOPOLITICAL],
            severity_threshold=EventSeverity.LOW,
            action=SafetyAction.MONITOR,
            lead_time_hours=6.0,
            duration_hours=12.0,
            conditions={
                "alert_threshold": 0.05  # 5% изменение волатильности
            }
        )
        
        rules = [fomc_rule, cpi_rule, nfp_rule, crypto_reg_rule, geopolitical_rule]
        
        for rule in rules:
            self.rules[rule.name] = rule
            logger.info(f"Загружено правило: {rule.name}")
    
    async def evaluate_current_restrictions(self) -> Dict[str, Any]:
        """Оценка текущих ограничений"""
        
        restrictions = {
            "timestamp": datetime.now().isoformat(),
            "active_rules": [],
            "severity_level": "LOW",
            "recommended_actions": [],
            "affected_symbols": set(),
            "restrictions_summary": {}
        }
        
        # Получаем предстоящие и активные события
        upcoming_events = await self.calendar.get_upcoming_events(6)  # 6 часов вперед
        active_events = await self.calendar.get_active_events()
        
        all_relevant_events = upcoming_events + active_events
        
        # Проверяем каждое правило
        for rule_name, rule in self.rules.items():
            triggered_events = []
            
            for event in all_relevant_events:
                if self._event_matches_rule(event, rule):
                    # Проверяем временные рамки
                    now = datetime.now()
                    lead_time = timedelta(hours=rule.lead_time_hours)
                    duration = timedelta(hours=rule.duration_hours)
                    
                    activation_time = event.scheduled_time - lead_time
                    expiration_time = event.scheduled_time + duration
                    
                    if activation_time <= now <= expiration_time:
                        triggered_events.append(event)
            
            if triggered_events:
                # Правило активировано
                rule_data = {
                    "rule_name": rule_name,
                    "action": rule.action.value,
                    "triggered_by": [e.name for e in triggered_events],
                    "severity": max([e.severity.value for e in triggered_events]),
                    "expires_at": max([
                        e.scheduled_time + timedelta(hours=rule.duration_hours) 
                        for e in triggered_events
                    ]).isoformat()
                }
                
                restrictions["active_rules"].append(rule_data)
                
                # Обновляем общий уровень серьезности
                if rule.action in [SafetyAction.BLACKOUT, SafetyAction.EMERGENCY_EXIT]:
                    restrictions["severity_level"] = "CRITICAL"
                elif rule.action in [SafetyAction.HALT_TRADING] and restrictions["severity_level"] != "CRITICAL":
                    restrictions["severity_level"] = "HIGH"
                elif rule.action == SafetyAction.REDUCE_EXPOSURE and restrictions["severity_level"] == "LOW":
                    restrictions["severity_level"] = "MEDIUM"
                
                # Добавляем рекомендуемые действия
                self._add_action_recommendations(restrictions, rule, triggered_events)
                
                # Сохраняем активацию в БД
                await self._save_rule_activation(rule, triggered_events)
        
        # Конвертируем set в list для JSON
        restrictions["affected_symbols"] = list(restrictions["affected_symbols"])
        
        return restrictions
    
    def _event_matches_rule(self, event: EconomicEvent, rule: SafetyRule) -> bool:
        """Проверка соответствия события правилу"""
        
        # Проверяем категорию
        if event.category not in rule.categories:
            return False
        
        # Проверяем серьезность
        severity_order = {
            EventSeverity.LOW: 1,
            EventSeverity.MEDIUM: 2, 
            EventSeverity.HIGH: 3,
            EventSeverity.CRITICAL: 4
        }
        
        if severity_order[event.severity] < severity_order[rule.severity_threshold]:
            return False
        
        # Проверяем паттерны названий
        for pattern in rule.event_patterns:
            if pattern.lower() in event.name.lower():
                return True
        
        return False
    
    def _add_action_recommendations(self, restrictions: Dict, rule: SafetyRule, events: List[EconomicEvent]):
        """Добавление рекомендаций по действиям"""
        
        if rule.action == SafetyAction.BLACKOUT:
            restrictions["recommended_actions"].extend([
                "Полная остановка торговли",
                "Закрытие всех открытых позиций",
                "Отмена всех pending ордеров",
                "Активация emergency mode"
            ])
            
        elif rule.action == SafetyAction.EMERGENCY_EXIT:
            restrictions["recommended_actions"].extend([
                "Экстренное закрытие позиций",
                "Немедленная продажа рискованных активов",
                "Переход в stablecoin"
            ])
            
        elif rule.action == SafetyAction.HALT_TRADING:
            restrictions["recommended_actions"].extend([
                "Остановка размещения новых ордеров",
                "Мониторинг существующих позиций",
                "Готовность к быстрому реагированию"
            ])
            
        elif rule.action == SafetyAction.REDUCE_EXPOSURE:
            restrictions["recommended_actions"].extend([
                f"Снижение размера позиций на {rule.conditions.get('max_position_reduction', 0.3)*100}%",
                f"Увеличение min_confidence на {rule.conditions.get('min_confidence_boost', 10)} пунктов",
                "Ужесточение стоп-лоссов"
            ])
            
        elif rule.action == SafetyAction.MONITOR:
            restrictions["recommended_actions"].extend([
                "Усиленный мониторинг рынка",
                "Готовность к быстрым изменениям стратегии",
                "Анализ волатильности в реальном времени"
            ])
        
        # Добавляем символы, затронутые событиями
        for event in events:
            if "ALL" in event.impact_currencies:
                restrictions["affected_symbols"].update(["BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT"])
            else:
                for currency in event.impact_currencies:
                    if currency != "USD":
                        restrictions["affected_symbols"].add(f"{currency}USDT")
    
    async def _save_rule_activation(self, rule: SafetyRule, events: List[EconomicEvent]):
        """Сохранение активации правила в БД"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for event in events:
                now = datetime.now()
                expires_at = event.scheduled_time + timedelta(hours=rule.duration_hours)
                
                cursor.execute("""
                    INSERT INTO safety_activations 
                    (rule_name, event_name, action, activated_at, expires_at, reason)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    rule.name,
                    event.name,
                    rule.action.value,
                    now.isoformat(),
                    expires_at.isoformat(),
                    f"Event: {event.name} triggered rule: {rule.name}"
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Ошибка сохранения активации правила: {e}")
    
    async def add_custom_rule(self, rule: SafetyRule):
        """Добавление пользовательского правила"""
        self.rules[rule.name] = rule
        logger.info(f"Добавлено пользовательское правило: {rule.name}")
    
    async def get_safety_report(self) -> Dict:
        """Получение отчета по безопасности"""
        
        current_restrictions = await self.evaluate_current_restrictions()
        upcoming_events = await self.calendar.get_upcoming_events(48)  # 48 часов
        
        return {
            "timestamp": datetime.now().isoformat(),
            "current_restrictions": current_restrictions,
            "upcoming_events": [
                {
                    "name": e.name,
                    "category": e.category.value,
                    "severity": e.severity.value,
                    "scheduled_time": e.scheduled_time.isoformat(),
                    "impact_currencies": e.impact_currencies,
                    "volatility_factor": e.volatility_factor
                } for e in upcoming_events
            ],
            "total_rules": len(self.rules),
            "active_rules_count": len(current_restrictions["active_rules"]),
            "safety_status": self._calculate_safety_status(current_restrictions)
        }
    
    def _calculate_safety_status(self, restrictions: Dict) -> str:
        """Расчет общего статуса безопасности"""
        
        if restrictions["severity_level"] == "CRITICAL":
            return "DANGER - Критические ограничения активны"
        elif restrictions["severity_level"] == "HIGH":
            return "WARNING - Высокий уровень ограничений"
        elif restrictions["severity_level"] == "MEDIUM":
            return "CAUTION - Умеренные ограничения"
        else:
            return "SAFE - Ограничения отсутствуют"

# Тестирование системы безопасности
async def test_ai_safety_rules():
    """Тестирование расширенной системы безопасности"""
    
    print("=== Тестирование AI Safety Rules Engine ===\n")
    
    # Инициализация движка
    safety_engine = AISafetyRulesEngine()
    
    # Добавление тестового события близко к текущему времени
    test_event = EconomicEvent(
        name="Test FOMC Decision",
        category=EventCategory.MONETARY_POLICY,
        severity=EventSeverity.CRITICAL,
        scheduled_time=datetime.now() + timedelta(minutes=30),
        description="Test Federal Reserve decision for safety testing",
        impact_currencies=["USD", "USDT"],
        volatility_factor=2.5,
        duration_hours=4
    )
    
    await safety_engine.calendar.add_event(test_event)
    
    # Оценка текущих ограничений
    print("=== Текущие ограничения безопасности ===")
    restrictions = await safety_engine.evaluate_current_restrictions()
    print(json.dumps(restrictions, indent=2, ensure_ascii=False, default=str))
    
    # Полный отчет по безопасности
    print("\n=== Отчет по безопасности ===")
    safety_report = await safety_engine.get_safety_report()
    print(json.dumps(safety_report, indent=2, ensure_ascii=False, default=str))
    
    # Тестирование пользовательского правила
    custom_rule = SafetyRule(
        name="CUSTOM_TEST_RULE",
        description="Test custom safety rule",
        event_patterns=["Test"],
        categories=[EventCategory.MONETARY_POLICY],
        severity_threshold=EventSeverity.HIGH,
        action=SafetyAction.HALT_TRADING,
        lead_time_hours=0.1,
        duration_hours=1.0
    )
    
    await safety_engine.add_custom_rule(custom_rule)
    
    # Повторная оценка с новым правилом
    print("\n=== Ограничения после добавления пользовательского правила ===")
    updated_restrictions = await safety_engine.evaluate_current_restrictions()
    print(json.dumps(updated_restrictions, indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__":
    asyncio.run(test_ai_safety_rules())