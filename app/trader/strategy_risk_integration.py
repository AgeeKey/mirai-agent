"""
Mirai Agent - Strategy Risk Integration
Интеграция торговых стратегий с системой управления рисками
"""
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import sys
import os

# Добавляем пути для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Импорты стратегий и риск-менеджмента
try:
    from ..strategies.technical.base_strategy import BaseTradingStrategy, TradingSignal, StrategyParams
    from .advanced_risk_engine import AdvancedRiskEngine, PositionType, RiskLimits, RiskLevel
    from .ai_safety_layers import AISafetySystem
except ImportError:
    try:
        from strategies.technical.base_strategy import BaseTradingStrategy, TradingSignal, StrategyParams
        from advanced_risk_engine import AdvancedRiskEngine, PositionType, RiskLimits, RiskLevel
        from ai_safety_layers import AISafetySystem
    except ImportError:
        # Fallback для standalone запуска
        import sys
        import os
        sys.path.append('/root/mirai-agent/app/strategies/technical')
        from base_strategy import BaseTradingStrategy, TradingSignal, StrategyParams
        from advanced_risk_engine import AdvancedRiskEngine, PositionType, RiskLimits, RiskLevel
        from ai_safety_layers import AISafetySystem

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StrategyConfig:
    """Конфигурация стратегии с риск-менеджментом"""
    strategy_name: str
    symbol: str
    timeframe: str = "1h"
    risk_per_trade_pct: float = 1.0  # 1% риска на сделку
    min_confidence: float = 0.65  # Минимальная уверенность 65%
    max_leverage: float = 3.0  # Максимальное плечо
    enabled: bool = True

class StrategyRiskManager:
    """Менеджер стратегий с интегрированным риск-менеджментом"""
    
    def __init__(self, initial_balance: float = 10000.0):
        # Инициализация компонентов
        self.risk_engine = AdvancedRiskEngine(initial_balance)
        self.safety_system = AISafetySystem()
        self.strategies: Dict[str, BaseTradingStrategy] = {}
        self.strategy_configs: Dict[str, StrategyConfig] = {}
        
        # Состояние
        self.active = True
        self.performance_metrics = {}
        
        logger.info("Инициализирован StrategyRiskManager")
    
    def add_strategy(self, strategy_name: str, config: StrategyConfig):
        """Добавление новой стратегии"""
        
        # Создание стратегии с правильными параметрами
        strategy_params = StrategyParams(
            ma_fast_period=10,
            ma_slow_period=30,
            rsi_period=14,
            rsi_oversold=30.0,
            rsi_overbought=70.0,
            macd_fast=12,
            macd_slow=26,
            macd_signal=9,
            stop_loss_pct=1.0,
            take_profit_pct=2.0,
            max_position_size=1000.0,
            min_confidence=config.min_confidence,
            strong_signal_threshold=80.0
        )
        
        # Инициализация стратегии только с параметрами
        strategy = BaseTradingStrategy(params=strategy_params)
        
        # Сохранение
        self.strategies[strategy_name] = strategy
        self.strategy_configs[strategy_name] = config
        
        logger.info(f"Добавлена стратегия: {strategy_name} для {config.symbol}")
    
    async def process_market_data(self, symbol: str, price_data: Dict) -> Dict:
        """Обработка рыночных данных и генерация сигналов"""
        
        if not self.active:
            return {"status": "inactive", "signals": []}
        
        signals = []
        
        # Обновление позиций в risk engine
        current_prices = {symbol: price_data.get('close', 0)}
        await self.risk_engine.update_positions(current_prices)
        
        # Проверка стратегий для данного символа
        for strategy_name, strategy in self.strategies.items():
            config = self.strategy_configs[strategy_name]
            
            if config.symbol == symbol and config.enabled:
                try:
                    # Генерация сигнала
                    signal = await self.generate_strategy_signal(strategy_name, price_data)
                    
                    if signal:
                        # Валидация через риск-менеджмент
                        validated_signal = await self.validate_signal_with_risk_management(
                            strategy_name, signal, price_data
                        )
                        
                        if validated_signal:
                            # AI Safety validation before accepting signal
                            account_status = {
                                'balance': self.risk_engine.current_balance,
                                'daily_pnl': self.risk_engine.daily_pnl
                            }
                            risk_metrics = asdict(await self.risk_engine.calculate_risk_metrics())
                            approved, safety_check = await self.safety_system.validate_trade_execution(
                                validated_signal,
                                { 'volatility': price_data.get('volatility', 0.02) },
                                account_status,
                                risk_metrics
                            )
                            if approved:
                                signals.append(validated_signal)
                            else:
                                logger.info(f"Сигнал отклонен AI Safety: {safety_check.reasoning if safety_check else 'no details'}")
                
                except Exception as e:
                    logger.error(f"Ошибка обработки стратегии {strategy_name}: {e}")
        
        # Исправляем сериализацию риск-метрик
        risk_metrics = await self.risk_engine.calculate_risk_metrics()
        risk_metrics_dict = asdict(risk_metrics)
        risk_metrics_dict['risk_level'] = risk_metrics.risk_level.value  # Enum в строку
        
        return {
            "status": "active",
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "signals": signals,
            "risk_metrics": risk_metrics_dict
        }
    
    async def generate_strategy_signal(self, strategy_name: str, price_data: Dict) -> Optional[Dict]:
        """Генерация сигнала от стратегии"""
        
        strategy = self.strategies[strategy_name]
        config = self.strategy_configs[strategy_name]
        
        # Подготовка данных для стратегии в формате DataFrame
        import pandas as pd
        import numpy as np
        
        # Создаем простые данные для тестирования с трендом
        base_price = price_data.get('close', 50000)
        data_size = 100
        
        # Генерируем исторические данные с небольшим трендом
        np.random.seed(42)
        trend = np.cumsum(np.random.randn(data_size) * 0.001)
        noise = np.random.randn(data_size) * 0.01
        
        prices = base_price * (1 + trend + noise)
        
        sample_data = pd.DataFrame({
            'open': prices * (1 + np.random.randn(data_size) * 0.001),
            'high': prices * (1 + np.abs(np.random.randn(data_size)) * 0.002),
            'low': prices * (1 - np.abs(np.random.randn(data_size)) * 0.002),
            'close': prices,
            'volume': np.random.randint(1000, 10000, data_size)
        })
        
        try:
            # Анализ стратегией (используем analyze_market)
            signal = await strategy.analyze_market(config.symbol, sample_data)
            
            if signal and signal.confidence >= config.min_confidence:
                return {
                    "strategy_name": strategy_name,
                    "symbol": config.symbol,
                    "signal_type": signal.signal_type.value,  # Enum в строку
                    "confidence": signal.confidence,
                    "entry_price": signal.entry_price,
                    "stop_loss": signal.stop_loss,
                    "take_profit": signal.take_profit,
                    "reasoning": signal.reasoning,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Ошибка генерации сигнала: {e}")
            return None
        
        return None
    
    async def validate_signal_with_risk_management(self, strategy_name: str, signal: Dict, price_data: Dict) -> Optional[Dict]:
        """Валидация сигнала через систему риск-менеджмента"""
        
        config = self.strategy_configs[strategy_name]
        
        # Расчет размера позиции на основе риска
        position_size = await self.calculate_position_size(
            signal['entry_price'],
            signal['stop_loss'],
            config.risk_per_trade_pct
        )
        
        if position_size <= 0:
            logger.warning(f"Некорректный размер позиции для сигнала {strategy_name}")
            return None
        
        # Определение типа позиции
        position_type = PositionType.LONG if signal['signal_type'] == 'buy' else PositionType.SHORT
        
        # Валидация через risk engine
        is_valid, validation_message = await self.risk_engine.validate_new_position(
            symbol=config.symbol,
            position_type=position_type,
            entry_price=signal['entry_price'],
            quantity=position_size,
            stop_loss=signal['stop_loss']
        )
        
        if not is_valid:
            logger.info(f"Сигнал {strategy_name} отклонен риск-менеджментом: {validation_message}")
            return None
        
        # Добавление информации о размере позиции
        validated_signal = signal.copy()
        validated_signal.update({
            "position_size": position_size,
            "position_type": position_type.value,
            "risk_validation": "passed",
            "validation_message": validation_message
        })
        
        return validated_signal
    
    async def calculate_position_size(self, entry_price: float, stop_loss: float, risk_pct: float) -> float:
        """Расчет размера позиции на основе риска"""
        
        if entry_price <= 0 or stop_loss <= 0:
            return 0
        
        # Риск на сделку в долларах
        risk_amount = self.risk_engine.current_balance * (risk_pct / 100)
        
        # Расстояние до стоп-лосса
        stop_distance = abs(entry_price - stop_loss)
        
        if stop_distance <= 0:
            return 0
        
        # Размер позиции = Риск / Расстояние до стоп-лосса
        position_size = risk_amount / stop_distance
        
        # Ограничение максимальным размером позиции
        max_position_value = self.risk_engine.current_balance * (self.risk_engine.limits.max_position_size_pct / 100)
        max_position_size = max_position_value / entry_price
        
        return min(position_size, max_position_size)
    
    async def execute_signal(self, validated_signal: Dict) -> Tuple[bool, str]:
        """Исполнение валидированного сигнала"""
        
        if not self.active:
            return False, "StrategyRiskManager неактивен"
        
        # Определение типа позиции
        position_type = PositionType.LONG if validated_signal['signal_type'] == 'buy' else PositionType.SHORT
        
        # Открытие позиции через risk engine
        success, message = await self.risk_engine.open_position(
            symbol=validated_signal['symbol'],
            position_type=position_type,
            entry_price=validated_signal['entry_price'],
            quantity=validated_signal['position_size'],
            stop_loss=validated_signal['stop_loss'],
            take_profit=validated_signal['take_profit']
        )
        
        if success:
            # Обновление метрик стратегии
            strategy_name = validated_signal['strategy_name']
            if strategy_name not in self.performance_metrics:
                self.performance_metrics[strategy_name] = {
                    "total_signals": 0,
                    "executed_signals": 0,
                    "total_pnl": 0,
                    "win_rate": 0
                }
            
            self.performance_metrics[strategy_name]["total_signals"] += 1
            self.performance_metrics[strategy_name]["executed_signals"] += 1
            
            logger.info(f"Исполнен сигнал стратегии {strategy_name}: {message}")
        
        return success, message
    
    async def emergency_stop_all(self, reason: str = "manual"):
        """Экстренная остановка всех стратегий"""
        
        self.active = False
        await self.risk_engine.emergency_stop(reason)
        
        logger.critical(f"Emergency stop всех стратегий: {reason}")
    
    async def resume_trading(self):
        """Возобновление торговли"""
        
        await self.risk_engine.reset_emergency_stop()
        self.active = True
        
        logger.info("Торговля возобновлена")
    
    async def get_comprehensive_report(self) -> Dict:
        """Получение комплексного отчета"""
        
        # Базовый отчет по рискам
        risk_report = await self.risk_engine.get_risk_report()
        
        # Метрики стратегий
        strategy_metrics = {}
        for strategy_name, config in self.strategy_configs.items():
            strategy_metrics[strategy_name] = {
                "config": {
                    "symbol": config.symbol,
                    "timeframe": config.timeframe,
                    "risk_per_trade_pct": config.risk_per_trade_pct,
                    "min_confidence": config.min_confidence,
                    "enabled": config.enabled
                },
                "performance": self.performance_metrics.get(strategy_name, {})
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system_status": {
                "active": self.active,
                "emergency_stop": self.risk_engine.emergency_stop_active,
                "strategies_count": len(self.strategies),
                "active_strategies": sum(1 for c in self.strategy_configs.values() if c.enabled)
            },
            "risk_management": risk_report,
            "strategies": strategy_metrics
        }

# Пример использования и тестирования
async def test_strategy_risk_integration():
    """Тестирование интеграции стратегий и риск-менеджмента"""
    
    # Инициализация
    manager = StrategyRiskManager(initial_balance=10000.0)
    
    # Добавление стратегии
    config = StrategyConfig(
        strategy_name="btc_technical",
        symbol="BTCUSDT",
        timeframe="1h",
        risk_per_trade_pct=1.0,
        min_confidence=0.65
    )
    
    manager.add_strategy("btc_technical", config)
    
    # Симуляция рыночных данных
    market_data = {
        'open': 50000,
        'high': 51000,
        'low': 49000,
        'close': 50500,
        'volume': 1000
    }
    
    # Обработка данных
    result = await manager.process_market_data("BTCUSDT", market_data)
    print(f"Результат обработки: {json.dumps(result, indent=2)}")
    
    # Исполнение сигналов (если есть)
    for signal in result.get('signals', []):
        success, message = await manager.execute_signal(signal)
        print(f"Исполнение сигнала: {success} - {message}")
    
    # Комплексный отчет
    report = await manager.get_comprehensive_report()
    print(f"Комплексный отчет: {json.dumps(report, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_strategy_risk_integration())
