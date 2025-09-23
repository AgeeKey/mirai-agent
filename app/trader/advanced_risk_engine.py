"""
Mirai Agent - Улучшенный Risk Engine
Продвинутая система управления рисками для автономной торговли
"""
import asyncio
import logging
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Уровни риска"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PositionType(Enum):
    """Типы позиций"""
    LONG = "long"
    SHORT = "short"

@dataclass
class RiskLimits:
    """Лимиты риска"""
    # Дневные лимиты
    max_daily_loss_pct: float = 3.0  # 3% максимальная дневная просадка
    max_daily_trades: int = 50  # Максимум сделок в день
    
    # Позиционные лимиты
    max_position_size_pct: float = 10.0  # 10% от баланса на одну позицию
    max_open_positions: int = 3  # Максимум открытых позиций
    max_correlation_exposure: float = 0.5  # Максимальная корреляционная экспозиция
    
    # Стоп-лоссы
    position_stop_loss_pct: float = 1.0  # 1% стоп-лосс на позицию
    global_stop_loss_pct: float = 5.0  # 5% глобальный стоп-лосс
    
    # Волатильность
    max_volatility_exposure: float = 0.3  # Максимальная экспозиция в волатильные активы
    volatility_threshold: float = 0.02  # 2% дневная волатильность как порог
    
    # Время
    max_position_hold_hours: int = 24  # Максимальное время удержания позиции
    cooldown_after_loss_minutes: int = 30  # Пауза после убыточной сделки

@dataclass
class Position:
    """Структура позиции"""
    id: str
    symbol: str
    position_type: PositionType
    entry_price: float
    current_price: float
    quantity: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    status: str = "open"  # open, closed, liquidated

@dataclass
class RiskMetrics:
    """Метрики риска"""
    current_drawdown_pct: float = 0.0
    daily_pnl: float = 0.0
    total_exposure_pct: float = 0.0
    open_positions_count: int = 0
    avg_position_size_pct: float = 0.0
    portfolio_volatility: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW

class AdvancedRiskEngine:
    """Продвинутый движок управления рисками"""
    
    def __init__(self, initial_balance: float = 10000.0, limits: RiskLimits = None):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.limits = limits or RiskLimits()
        
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.daily_trades_count = 0
        self.daily_pnl = 0.0
        self.last_trade_time = None
        self.emergency_stop_active = False
        
        # База данных для хранения данных
        self.db_path = "/root/mirai-agent/state/mirai.db"
        self.init_database()
        
        logger.info(f"Инициализирован продвинутый Risk Engine с балансом ${initial_balance}")
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Таблица позиций
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id TEXT PRIMARY KEY,
                    symbol TEXT,
                    position_type TEXT,
                    entry_price REAL,
                    current_price REAL,
                    quantity REAL,
                    entry_time TEXT,
                    stop_loss REAL,
                    take_profit REAL,
                    unrealized_pnl REAL,
                    realized_pnl REAL,
                    status TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица метрик риска
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS risk_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    current_drawdown_pct REAL,
                    daily_pnl REAL,
                    total_exposure_pct REAL,
                    open_positions_count INTEGER,
                    portfolio_volatility REAL,
                    risk_level TEXT
                )
            """)
            
            # Таблица лимитов риска
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS risk_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    event_type TEXT,
                    description TEXT,
                    severity TEXT,
                    position_id TEXT,
                    action_taken TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
    
    async def validate_new_position(self, symbol: str, position_type: PositionType, 
                                  entry_price: float, quantity: float, stop_loss: float) -> Tuple[bool, str]:
        """Валидация новой позиции перед открытием"""
        
        # Проверка emergency stop
        if self.emergency_stop_active:
            return False, "Emergency stop активен"
        
        # Проверка количества открытых позиций
        if len(self.positions) >= self.limits.max_open_positions:
            return False, f"Превышен лимит открытых позиций ({self.limits.max_open_positions})"
        
        # Проверка размера позиции
        position_value = entry_price * quantity
        position_size_pct = (position_value / self.current_balance) * 100
        
        if position_size_pct > self.limits.max_position_size_pct:
            return False, f"Размер позиции ({position_size_pct:.1f}%) превышает лимит ({self.limits.max_position_size_pct}%)"
        
        # Проверка дневного лимита потерь
        current_daily_loss_pct = abs(min(0, self.daily_pnl)) / self.current_balance * 100
        if current_daily_loss_pct >= self.limits.max_daily_loss_pct:
            return False, f"Достигнут дневной лимит потерь ({self.limits.max_daily_loss_pct}%)"
        
        # Проверка количества дневных сделок
        if self.daily_trades_count >= self.limits.max_daily_trades:
            return False, f"Превышен лимит дневных сделок ({self.limits.max_daily_trades})"
        
        # Проверка стоп-лосса
        stop_loss_distance = abs(entry_price - stop_loss) / entry_price * 100
        if stop_loss_distance > self.limits.position_stop_loss_pct * 2:  # Максимум в 2 раза больше стандартного
            return False, f"Стоп-лосс слишком далеко ({stop_loss_distance:.1f}%)"
        
        # Проверка общей экспозиции
        total_exposure = await self.calculate_total_exposure()
        new_exposure = total_exposure + position_size_pct
        
        if new_exposure > 90:  # Максимум 90% экспозиции
            return False, f"Общая экспозиция превысит лимит ({new_exposure:.1f}%)"
        
        # Проверка cooldown после убытка
        if await self.check_cooldown():
            return False, "Активен cooldown после убыточной сделки"
        
        # Проверка корреляции (упрощенная)
        correlation_risk = await self.check_correlation_risk(symbol)
        if correlation_risk > self.limits.max_correlation_exposure:
            return False, f"Высокий корреляционный риск ({correlation_risk:.1f})"
        
        return True, "Позиция прошла валидацию"
    
    async def open_position(self, symbol: str, position_type: PositionType, 
                          entry_price: float, quantity: float, stop_loss: float, 
                          take_profit: float) -> Tuple[bool, str]:
        """Открытие новой позиции"""
        
        # Валидация
        is_valid, message = await self.validate_new_position(symbol, position_type, entry_price, quantity, stop_loss)
        if not is_valid:
            await self.log_risk_event("POSITION_REJECTED", message, "WARNING", None)
            return False, message
        
        # Создание позиции
        position_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        position = Position(
            id=position_id,
            symbol=symbol,
            position_type=position_type,
            entry_price=entry_price,
            current_price=entry_price,
            quantity=quantity,
            entry_time=datetime.now(),
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        # Сохранение в память и базу данных
        self.positions[position_id] = position
        await self.save_position_to_db(position)
        
        # Обновление счетчиков
        self.daily_trades_count += 1
        self.last_trade_time = datetime.now()
        
        # Логирование
        await self.log_risk_event("POSITION_OPENED", f"Открыта позиция {symbol} {position_type.value}", "INFO", position_id)
        
        logger.info(f"Открыта позиция: {position_id} - {symbol} {position_type.value} @ ${entry_price}")
        
        return True, position_id
    
    async def close_position(self, position_id: str, exit_price: float, reason: str = "manual") -> Tuple[bool, str]:
        """Закрытие позиции"""
        
        if position_id not in self.positions:
            return False, "Позиция не найдена"
        
        position = self.positions[position_id]
        
        # Расчет P&L
        if position.position_type == PositionType.LONG:
            pnl = (exit_price - position.entry_price) * position.quantity
        else:  # SHORT
            pnl = (position.entry_price - exit_price) * position.quantity
        
        # Обновление позиции
        position.current_price = exit_price
        position.realized_pnl = pnl
        position.status = "closed"
        
        # Обновление баланса и метрик
        self.current_balance += pnl
        self.daily_pnl += pnl
        
        # Перенос в закрытые позиции
        self.closed_positions.append(position)
        del self.positions[position_id]
        
        # Сохранение в базу данных
        await self.save_position_to_db(position)
        
        # Логирование
        pnl_pct = (pnl / (position.entry_price * position.quantity)) * 100
        await self.log_risk_event(
            "POSITION_CLOSED", 
            f"Закрыта позиция {position.symbol} с P&L ${pnl:.2f} ({pnl_pct:.1f}%). Причина: {reason}",
            "INFO",
            position_id
        )
        
        logger.info(f"Закрыта позиция: {position_id} - P&L: ${pnl:.2f} ({pnl_pct:.1f}%)")
        
        # Проверка критических потерь
        if pnl < 0:
            loss_pct = abs(pnl) / self.current_balance * 100
            if loss_pct > 2.0:  # Крупная потеря
                await self.log_risk_event("LARGE_LOSS", f"Крупная потеря: ${abs(pnl):.2f}", "WARNING", position_id)
        
        return True, f"P&L: ${pnl:.2f}"
    
    async def update_positions(self, price_data: Dict[str, float]):
        """Обновление цен и проверка стоп-лоссов/тейк-профитов"""
        
        positions_to_close = []
        
        for position_id, position in self.positions.items():
            if position.symbol in price_data:
                current_price = price_data[position.symbol]
                position.current_price = current_price
                
                # Расчет нереализованного P&L
                if position.position_type == PositionType.LONG:
                    position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
                else:
                    position.unrealized_pnl = (position.entry_price - current_price) * position.quantity
                
                # Проверка стоп-лосса
                should_stop = False
                if position.position_type == PositionType.LONG and current_price <= position.stop_loss:
                    should_stop = True
                elif position.position_type == PositionType.SHORT and current_price >= position.stop_loss:
                    should_stop = True
                
                # Проверка тейк-профита
                should_take_profit = False
                if position.position_type == PositionType.LONG and current_price >= position.take_profit:
                    should_take_profit = True
                elif position.position_type == PositionType.SHORT and current_price <= position.take_profit:
                    should_take_profit = True
                
                # Проверка времени удержания
                hold_time = datetime.now() - position.entry_time
                if hold_time.total_seconds() / 3600 > self.limits.max_position_hold_hours:
                    positions_to_close.append((position_id, current_price, "time_limit"))
                elif should_stop:
                    positions_to_close.append((position_id, current_price, "stop_loss"))
                elif should_take_profit:
                    positions_to_close.append((position_id, current_price, "take_profit"))
        
        # Закрытие позиций
        for position_id, exit_price, reason in positions_to_close:
            await self.close_position(position_id, exit_price, reason)
    
    async def calculate_risk_metrics(self) -> RiskMetrics:
        """Расчет текущих метрик риска"""
        
        metrics = RiskMetrics()
        
        # Текущая просадка
        if self.current_balance < self.initial_balance:
            metrics.current_drawdown_pct = ((self.initial_balance - self.current_balance) / self.initial_balance) * 100
        
        # Дневной P&L
        metrics.daily_pnl = self.daily_pnl
        
        # Общая экспозиция
        metrics.total_exposure_pct = await self.calculate_total_exposure()
        
        # Количество открытых позиций
        metrics.open_positions_count = len(self.positions)
        
        # Средний размер позиции
        if len(self.positions) > 0:
            total_position_value = sum(
                pos.current_price * pos.quantity for pos in self.positions.values()
            )
            metrics.avg_position_size_pct = (total_position_value / len(self.positions) / self.current_balance) * 100
        
        # Волатильность портфеля (упрощенная)
        if len(self.closed_positions) > 5:
            returns = [pos.realized_pnl / (pos.entry_price * pos.quantity) for pos in self.closed_positions[-20:]]
            metrics.portfolio_volatility = np.std(returns) if returns else 0.0
        
        # Винрейт
        if len(self.closed_positions) > 0:
            winning_trades = sum(1 for pos in self.closed_positions if pos.realized_pnl > 0)
            metrics.win_rate = winning_trades / len(self.closed_positions) * 100
        
        # Максимальная просадка
        if len(self.closed_positions) > 0:
            balance_history = [self.initial_balance]
            for pos in self.closed_positions:
                balance_history.append(balance_history[-1] + pos.realized_pnl)
            
            peak = self.initial_balance
            max_dd = 0
            for balance in balance_history:
                if balance > peak:
                    peak = balance
                drawdown = (peak - balance) / peak * 100
                if drawdown > max_dd:
                    max_dd = drawdown
            
            metrics.max_drawdown_pct = max_dd
        
        # Уровень риска
        metrics.risk_level = self.calculate_risk_level(metrics)
        
        return metrics
    
    def calculate_risk_level(self, metrics: RiskMetrics) -> RiskLevel:
        """Определение уровня риска"""
        
        risk_score = 0
        
        # Просадка
        if metrics.current_drawdown_pct > 2.0:
            risk_score += 2
        elif metrics.current_drawdown_pct > 1.0:
            risk_score += 1
        
        # Экспозиция
        if metrics.total_exposure_pct > 80:
            risk_score += 2
        elif metrics.total_exposure_pct > 50:
            risk_score += 1
        
        # Количество позиций
        if metrics.open_positions_count >= self.limits.max_open_positions:
            risk_score += 1
        
        # Волатильность
        if metrics.portfolio_volatility > 0.05:  # 5%
            risk_score += 2
        elif metrics.portfolio_volatility > 0.03:  # 3%
            risk_score += 1
        
        # Винрейт
        if len(self.closed_positions) > 10:
            if metrics.win_rate < 30:
                risk_score += 2
            elif metrics.win_rate < 45:
                risk_score += 1
        
        # Определение уровня
        if risk_score >= 6:
            return RiskLevel.CRITICAL
        elif risk_score >= 4:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def calculate_total_exposure(self) -> float:
        """Расчет общей экспозиции портфеля"""
        if not self.positions:
            return 0.0
        
        total_value = sum(
            pos.current_price * pos.quantity for pos in self.positions.values()
        )
        
        return (total_value / self.current_balance) * 100
    
    async def check_cooldown(self) -> bool:
        """Проверка cooldown после убыточной сделки"""
        if not self.closed_positions:
            return False
        
        last_position = self.closed_positions[-1]
        if last_position.realized_pnl >= 0:  # Последняя сделка была прибыльной
            return False
        
        time_since_last = datetime.now() - last_position.entry_time
        return time_since_last.total_seconds() / 60 < self.limits.cooldown_after_loss_minutes
    
    async def check_correlation_risk(self, symbol: str) -> float:
        """Упрощенная проверка корреляционного риска"""
        # В реальной реализации здесь должен быть анализ корреляции между активами
        # Для простоты возвращаем базовый риск
        
        similar_positions = sum(1 for pos in self.positions.values() if pos.symbol.startswith(symbol[:3]))
        return similar_positions / max(1, len(self.positions))
    
    async def emergency_stop(self, reason: str = "manual"):
        """Экстренная остановка торговли"""
        self.emergency_stop_active = True
        
        # Закрытие всех открытых позиций
        positions_to_close = list(self.positions.keys())
        for position_id in positions_to_close:
            position = self.positions[position_id]
            await self.close_position(position_id, position.current_price, f"emergency_stop: {reason}")
        
        await self.log_risk_event("EMERGENCY_STOP", f"Активирован emergency stop: {reason}", "CRITICAL", None)
        logger.critical(f"EMERGENCY STOP активирован: {reason}")
    
    async def reset_emergency_stop(self):
        """Сброс emergency stop"""
        self.emergency_stop_active = False
        await self.log_risk_event("EMERGENCY_STOP_RESET", "Emergency stop сброшен", "INFO", None)
        logger.info("Emergency stop сброшен")
    
    async def save_position_to_db(self, position: Position):
        """Сохранение позиции в базу данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO positions 
                (id, symbol, position_type, entry_price, current_price, quantity, 
                 entry_time, stop_loss, take_profit, unrealized_pnl, realized_pnl, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                position.id, position.symbol, position.position_type.value,
                position.entry_price, position.current_price, position.quantity,
                position.entry_time.isoformat(), position.stop_loss, position.take_profit,
                position.unrealized_pnl, position.realized_pnl, position.status
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Ошибка сохранения позиции в БД: {e}")
    
    async def log_risk_event(self, event_type: str, description: str, severity: str, position_id: str = None):
        """Логирование события риска"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO risk_events 
                (timestamp, event_type, description, severity, position_id, action_taken)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(), event_type, description, severity, 
                position_id, "logged"
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Ошибка логирования события риска: {e}")
    
    async def get_risk_report(self) -> Dict:
        """Генерация отчета по рискам"""
        metrics = await self.calculate_risk_metrics()
        
        # Конвертируем метрики в сериализуемый формат
        metrics_dict = asdict(metrics)
        metrics_dict['risk_level'] = metrics.risk_level.value  # Enum в строку
        
        return {
            "timestamp": datetime.now().isoformat(),
            "account_balance": self.current_balance,
            "initial_balance": self.initial_balance,
            "total_pnl": self.current_balance - self.initial_balance,
            "daily_pnl": self.daily_pnl,
            "emergency_stop_active": self.emergency_stop_active,
            "limits": asdict(self.limits),
            "metrics": metrics_dict,
            "open_positions": {
                pos_id: {
                    "symbol": pos.symbol,
                    "type": pos.position_type.value,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "hold_time_hours": (datetime.now() - pos.entry_time).total_seconds() / 3600
                } for pos_id, pos in self.positions.items()
            },
            "recent_trades": len(self.closed_positions[-10:]) if self.closed_positions else 0,
            "daily_trades_count": self.daily_trades_count
        }

# Пример использования
async def test_risk_engine():
    """Тестирование Risk Engine"""
    
    # Инициализация
    risk_engine = AdvancedRiskEngine(initial_balance=10000.0)
    
    # Тест открытия позиций с корректными параметрами
    success, message = await risk_engine.open_position(
        symbol="BTCUSDT",
        position_type=PositionType.LONG,
        entry_price=50000.0,
        quantity=0.02,  # Уменьшенное количество (1% от баланса)
        stop_loss=49000.0,
        take_profit=52000.0
    )
    
    print(f"Открытие позиции: {success} - {message}")
    
    if success:
        # Обновление цен
        await risk_engine.update_positions({"BTCUSDT": 51000.0})
        
        # Отчет по рискам
        report = await risk_engine.get_risk_report()
        print(f"Отчет по рискам: {json.dumps(report, indent=2)}")
    
    # Тест превышения лимитов
    print("\n=== Тест превышения лимитов ===")
    
    # Попытка открыть слишком большую позицию
    success2, message2 = await risk_engine.open_position(
        symbol="ETHUSDT",
        position_type=PositionType.LONG,
        entry_price=3000.0,
        quantity=5.0,  # Слишком большое количество
        stop_loss=2900.0,
        take_profit=3200.0
    )
    
    print(f"Большая позиция: {success2} - {message2}")
    
    # Итоговые метрики
    final_metrics = await risk_engine.calculate_risk_metrics()
    print(f"\nИтоговые метрики риска:")
    print(f"- Уровень риска: {final_metrics.risk_level.value}")
    print(f"- Открытых позиций: {final_metrics.open_positions_count}")
    print(f"- Общая экспозиция: {final_metrics.total_exposure_pct:.1f}%")
    print(f"- Дневной P&L: ${final_metrics.daily_pnl:.2f}")

if __name__ == "__main__":
    asyncio.run(test_risk_engine())