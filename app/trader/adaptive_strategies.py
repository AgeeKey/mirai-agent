"""
Mirai Agent - Adaptive Trading Strategies (Day 3)
Самоадаптирующиеся алгоритмы под изменения рыночных условий
"""
import asyncio
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import sys
import os

# Добавляем пути для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Импорты стратегий и риск-менеджмента
try:
    from ..strategies.technical.base_strategy import BaseTradingStrategy, TradingSignal, StrategyParams
    from .advanced_risk_engine import AdvancedRiskEngine, PositionType, RiskLimits, RiskLevel
    from .strategy_risk_integration import StrategyRiskManager
except ImportError:
    try:
        from strategies.technical.base_strategy import BaseTradingStrategy, TradingSignal, StrategyParams
        from advanced_risk_engine import AdvancedRiskEngine, PositionType, RiskLimits, RiskLevel
        from strategy_risk_integration import StrategyRiskManager
    except ImportError:
        # Fallback для standalone запуска
        import sys
        import os
        sys.path.append('/root/mirai-agent/app/strategies/technical')
        sys.path.append('/root/mirai-agent/app/trader')
        from base_strategy import BaseTradingStrategy, TradingSignal, StrategyParams
        from advanced_risk_engine import AdvancedRiskEngine, PositionType, RiskLimits, RiskLevel
        from strategy_risk_integration import StrategyRiskManager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    """Расширенные рыночные режимы"""
    BULL_TREND = "bull_trend"
    BEAR_TREND = "bear_trend"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"
    CONSOLIDATION = "consolidation"

class AdaptationSpeed(Enum):
    """Скорость адаптации"""
    SLOW = "slow"      # Консервативная адаптация
    MEDIUM = "medium"  # Умеренная адаптация
    FAST = "fast"      # Быстрая адаптация
    REACTIVE = "reactive"  # Реактивная адаптация

@dataclass
class MarketConditions:
    """Текущие рыночные условия"""
    regime: MarketRegime
    volatility: float
    trend_strength: float
    volume_ratio: float
    price_momentum: float
    rsi_level: float
    support_resistance_distance: float
    correlation_breakdown: bool
    news_sentiment: float = 0.0  # -1 до 1
    fear_greed_index: float = 50.0  # 0-100

@dataclass
class AdaptationRecord:
    """Запись об адаптации стратегии"""
    timestamp: datetime
    old_params: StrategyParams
    new_params: StrategyParams
    market_conditions: MarketConditions
    performance_metrics: Dict
    adaptation_reason: str
    confidence: float

class MarketRegimeDetector:
    """Продвинутый детектор рыночных режимов"""
    
    def __init__(self):
        self.historical_regimes = []
        self.regime_persistence_threshold = 5  # минут
        
    async def detect_regime(self, market_data: Dict, historical_data: List[Dict]) -> MarketConditions:
        """Определение текущего рыночного режима"""
        
        if len(historical_data) < 50:
            # Недостаточно данных для точного анализа
            return MarketConditions(
                regime=MarketRegime.SIDEWAYS,
                volatility=0.02,
                trend_strength=0.5,
                volume_ratio=1.0,
                price_momentum=0.0,
                rsi_level=50.0,
                support_resistance_distance=0.02,
                correlation_breakdown=False
            )
        
        # Извлечение данных
        prices = np.array([d['close'] for d in historical_data[-50:]])
        volumes = np.array([d['volume'] for d in historical_data[-50:]])
        
        # Расчет метрик
        volatility = self._calculate_volatility(prices)
        trend_strength = self._calculate_trend_strength(prices)
        volume_ratio = self._calculate_volume_ratio(volumes)
        momentum = self._calculate_momentum(prices)
        rsi = self._calculate_rsi(prices)
        sr_distance = self._calculate_support_resistance_distance(prices)
        
        # Определение режима
        regime = self._classify_regime(volatility, trend_strength, momentum, rsi)
        
        # Проверка корреляционного пробоя
        correlation_breakdown = self._detect_correlation_breakdown(historical_data)
        
        return MarketConditions(
            regime=regime,
            volatility=volatility,
            trend_strength=trend_strength,
            volume_ratio=volume_ratio,
            price_momentum=momentum,
            rsi_level=rsi,
            support_resistance_distance=sr_distance,
            correlation_breakdown=correlation_breakdown
        )
    
    def _calculate_volatility(self, prices: np.ndarray) -> float:
        """Расчет волатильности"""
        if len(prices) < 2:
            return 0.02
        
        returns = np.diff(prices) / prices[:-1]
        return np.std(returns) * np.sqrt(24)  # Дневная волатильность
    
    def _calculate_trend_strength(self, prices: np.ndarray) -> float:
        """Расчет силы тренда"""
        if len(prices) < 20:
            return 0.5
        
        # EMA тренд
        ema_short = self._ema(prices, 10)
        ema_long = self._ema(prices, 30)
        
        trend_direction = 1 if ema_short[-1] > ema_long[-1] else -1
        trend_magnitude = abs(ema_short[-1] - ema_long[-1]) / ema_long[-1]
        
        return min(1.0, trend_magnitude * 10) * trend_direction
    
    def _calculate_volume_ratio(self, volumes: np.ndarray) -> float:
        """Расчет соотношения объемов"""
        if len(volumes) < 10:
            return 1.0
        
        recent_avg = np.mean(volumes[-5:])
        historical_avg = np.mean(volumes[-20:-5])
        
        return recent_avg / max(historical_avg, 1.0)
    
    def _calculate_momentum(self, prices: np.ndarray) -> float:
        """Расчет моментума"""
        if len(prices) < 10:
            return 0.0
        
        short_change = (prices[-1] - prices[-5]) / prices[-5]
        long_change = (prices[-1] - prices[-20]) / prices[-20]
        
        return (short_change + long_change) / 2
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Расчет RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_support_resistance_distance(self, prices: np.ndarray) -> float:
        """Расчет расстояния до уровней поддержки/сопротивления"""
        if len(prices) < 20:
            return 0.02
        
        current_price = prices[-1]
        recent_prices = prices[-20:]
        
        # Найти локальные максимумы и минимумы
        resistance = np.max(recent_prices)
        support = np.min(recent_prices)
        
        # Расстояние до ближайшего уровня
        distance_to_resistance = abs(resistance - current_price) / current_price
        distance_to_support = abs(current_price - support) / current_price
        
        return min(distance_to_resistance, distance_to_support)
    
    def _detect_correlation_breakdown(self, historical_data: List[Dict]) -> bool:
        """Определение пробоя корреляций"""
        # Упрощенная логика - можно расширить
        if len(historical_data) < 30:
            return False
        
        # Анализ необычных движений объема
        volumes = [d['volume'] for d in historical_data[-30:]]
        recent_volume = np.mean(volumes[-5:])
        normal_volume = np.mean(volumes[-30:-5])
        
        return recent_volume > normal_volume * 2.0
    
    def _classify_regime(self, volatility: float, trend_strength: float, 
                        momentum: float, rsi: float) -> MarketRegime:
        """Классификация рыночного режима"""
        
        # Высокая волатильность
        if volatility > 0.05:
            return MarketRegime.HIGH_VOLATILITY
        
        # Низкая волатильность
        if volatility < 0.01:
            return MarketRegime.LOW_VOLATILITY
        
        # Сильный тренд
        if abs(trend_strength) > 0.7:
            if trend_strength > 0:
                return MarketRegime.BULL_TREND
            else:
                return MarketRegime.BEAR_TREND
        
        # Разворот
        if (rsi > 80 and momentum < 0) or (rsi < 20 and momentum > 0):
            return MarketRegime.REVERSAL
        
        # Пробой
        if abs(momentum) > 0.03 and volatility > 0.03:
            return MarketRegime.BREAKOUT
        
        # Консолидация
        if abs(trend_strength) < 0.2 and volatility < 0.02:
            return MarketRegime.CONSOLIDATION
        
        # По умолчанию - боковик
        return MarketRegime.SIDEWAYS
    
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Экспоненциальная скользящая средняя"""
        alpha = 2.0 / (period + 1)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        
        return ema

class PerformanceAnalyzer:
    """Анализатор производительности стратегий"""
    
    def __init__(self):
        self.performance_history = {}
        self.db_path = "/root/mirai-agent/state/mirai.db"
        self._init_database()
    
    def _init_database(self):
        """Инициализация таблиц для анализа производительности"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Таблица истории торгов (если не существует)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    symbol TEXT,
                    strategy_name TEXT,
                    entry_price REAL,
                    exit_price REAL,
                    quantity REAL,
                    pnl REAL,
                    duration_minutes INTEGER,
                    market_regime TEXT,
                    volatility REAL,
                    confidence REAL,
                    adaptation_version INTEGER DEFAULT 1
                )
            """)
            
            # Таблица адаптаций стратегий
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_adaptations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    strategy_name TEXT,
                    old_params TEXT,
                    new_params TEXT,
                    market_conditions TEXT,
                    performance_before TEXT,
                    performance_after TEXT,
                    adaptation_reason TEXT,
                    confidence REAL
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
    
    async def analyze_strategy_performance(self, strategy_name: str, 
                                         lookback_hours: int = 48) -> Dict:
        """Анализ производительности стратегии за период"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Пробуем получить данные из таблицы trades
            since_time = (datetime.now() - timedelta(hours=lookback_hours)).isoformat()
            
            cursor.execute("""
                SELECT * FROM trades 
                WHERE strategy_name = ? AND timestamp > ?
                ORDER BY timestamp DESC
            """, (strategy_name, since_time))
            
            trade_records = cursor.fetchall()
            
            # Если нет данных в trades, используем risk_events как fallback
            if not trade_records:
                logger.info(f"Нет данных в таблице trades для {strategy_name}, используем risk_events")
                cursor.execute("""
                    SELECT timestamp, description, severity, position_id 
                    FROM risk_events 
                    WHERE timestamp > ? AND description LIKE ?
                    ORDER BY timestamp DESC
                """, (since_time, f'%{strategy_name}%'))
                
                risk_events = cursor.fetchall()
                conn.close()
                
                return self._analyze_from_risk_events(risk_events, strategy_name)
            
            conn.close()
            
            # Анализ торговых данных
            return self._analyze_trading_performance(trade_records, strategy_name)
            
        except Exception as e:
            logger.error(f"Ошибка анализа производительности: {e}")
            return self._default_performance_metrics(strategy_name)
    
    def _analyze_trading_performance(self, trade_records: List, strategy_name: str) -> Dict:
        """Анализ производительности на основе торговых записей"""
        
        if not trade_records:
            return self._default_performance_metrics(strategy_name)
        
        # Извлечение метрик
        pnls = [record[7] for record in trade_records if record[7] is not None]  # pnl
        durations = [record[8] for record in trade_records if record[8] is not None]  # duration
        confidences = [record[11] for record in trade_records if record[11] is not None]  # confidence
        
        # Основные метрики
        total_trades = len(trade_records)
        winning_trades = len([pnl for pnl in pnls if pnl > 0])
        losing_trades = len([pnl for pnl in pnls if pnl < 0])
        
        win_rate = winning_trades / max(total_trades, 1) * 100
        total_pnl = sum(pnls) if pnls else 0
        avg_pnl = total_pnl / max(total_trades, 1)
        avg_duration = np.mean(durations) if durations else 0
        avg_confidence = np.mean(confidences) if confidences else 50
        
        # Расчет Sharpe ratio (упрощенный)
        if len(pnls) > 1:
            sharpe_ratio = np.mean(pnls) / max(np.std(pnls), 0.001)
        else:
            sharpe_ratio = 0.0
        
        # Максимальная просадка
        cumulative_pnl = np.cumsum(pnls) if pnls else [0]
        running_max = np.maximum.accumulate(cumulative_pnl)
        drawdowns = running_max - cumulative_pnl
        max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
        
        return {
            "strategy_name": strategy_name,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_pnl_per_trade": avg_pnl,
            "avg_trade_duration_minutes": avg_duration,
            "avg_confidence": avg_confidence,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "recent_performance_score": self._calculate_performance_score(
                win_rate, sharpe_ratio, avg_confidence
            )
        }
    
    def _analyze_from_risk_events(self, risk_events: List, strategy_name: str) -> Dict:
        """Анализ на основе событий риска (fallback)"""
        
        total_events = len(risk_events)
        critical_events = len([e for e in risk_events if e[2] == 'CRITICAL'])
        warning_events = len([e for e in risk_events if e[2] == 'WARNING'])
        
        # Простая оценка на основе событий
        if total_events == 0:
            performance_score = 70  # Нейтральный уровень
        else:
            # Чем меньше критических событий, тем лучше
            critical_ratio = critical_events / total_events
            warning_ratio = warning_events / total_events
            performance_score = max(0, 100 - critical_ratio * 50 - warning_ratio * 25)
        
        return {
            "strategy_name": strategy_name,
            "total_trades": 0,
            "win_rate": 50.0,  # Нейтральное значение
            "total_pnl": 0.0,
            "avg_pnl_per_trade": 0.0,
            "avg_trade_duration_minutes": 0.0,
            "avg_confidence": 50.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "recent_performance_score": performance_score,
            "fallback_source": "risk_events",
            "total_risk_events": total_events,
            "critical_events": critical_events,
            "warning_events": warning_events
        }
    
    def _default_performance_metrics(self, strategy_name: str) -> Dict:
        """Метрики по умолчанию при отсутствии данных"""
        return {
            "strategy_name": strategy_name,
            "total_trades": 0,
            "win_rate": 50.0,
            "total_pnl": 0.0,
            "avg_pnl_per_trade": 0.0,
            "avg_trade_duration_minutes": 0.0,
            "avg_confidence": 50.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "recent_performance_score": 50.0,
            "data_source": "default"
        }
    
    def _calculate_performance_score(self, win_rate: float, sharpe_ratio: float, 
                                   avg_confidence: float) -> float:
        """Расчет общего скора производительности"""
        
        # Нормализация компонентов
        win_rate_score = min(100, win_rate)
        sharpe_score = min(100, max(0, (sharpe_ratio + 2) * 25))  # -2 до 2 -> 0 до 100
        confidence_score = avg_confidence
        
        # Взвешенная сумма
        performance_score = (
            win_rate_score * 0.4 +
            sharpe_score * 0.3 +
            confidence_score * 0.3
        )
        
        return min(100, max(0, performance_score))

class AdaptiveStrategyManager:
    """Главный менеджер адаптивных стратегий"""
    
    def __init__(self, adaptation_speed: AdaptationSpeed = AdaptationSpeed.MEDIUM):
        self.adaptation_speed = adaptation_speed
        self.regime_detector = MarketRegimeDetector()
        self.performance_analyzer = PerformanceAnalyzer()
        self.strategy_manager = StrategyRiskManager()
        
        # История адаптаций
        self.adaptation_history: List[AdaptationRecord] = []
        self.last_adaptation_time = {}
        
        # Настройки адаптации
        self.adaptation_thresholds = {
            AdaptationSpeed.SLOW: {
                "performance_threshold": 40.0,
                "min_adaptation_interval_hours": 12,
                "adaptation_strength": 0.2
            },
            AdaptationSpeed.MEDIUM: {
                "performance_threshold": 45.0,
                "min_adaptation_interval_hours": 6,
                "adaptation_strength": 0.4
            },
            AdaptationSpeed.FAST: {
                "performance_threshold": 50.0,
                "min_adaptation_interval_hours": 2,
                "adaptation_strength": 0.6
            },
            AdaptationSpeed.REACTIVE: {
                "performance_threshold": 55.0,
                "min_adaptation_interval_hours": 0.5,
                "adaptation_strength": 0.8
            }
        }
        
        logger.info(f"Инициализирован AdaptiveStrategyManager со скоростью {adaptation_speed.value}")
    
    async def run_adaptation_cycle(self, market_data: Dict, historical_data: List[Dict]) -> Dict:
        """Основной цикл адаптации стратегий"""
        
        adaptation_results = {
            "timestamp": datetime.now().isoformat(),
            "market_conditions": None,
            "strategies_analyzed": 0,
            "adaptations_made": 0,
            "adaptation_details": []
        }
        
        try:
            # Определение текущих рыночных условий
            market_conditions = await self.regime_detector.detect_regime(market_data, historical_data)
            adaptation_results["market_conditions"] = asdict(market_conditions)
            
            # Анализ каждой стратегии
            for strategy_name in self.strategy_manager.strategies.keys():
                adaptation_results["strategies_analyzed"] += 1
                
                # Проверка необходимости адаптации
                should_adapt, adaptation_reason = await self._should_adapt_strategy(
                    strategy_name, market_conditions
                )
                
                if should_adapt:
                    # Выполнение адаптации
                    adaptation_result = await self._adapt_strategy(
                        strategy_name, market_conditions, adaptation_reason
                    )
                    
                    if adaptation_result["success"]:
                        adaptation_results["adaptations_made"] += 1
                        adaptation_results["adaptation_details"].append(adaptation_result)
            
            logger.info(f"Цикл адаптации завершен: {adaptation_results['adaptations_made']} адаптаций")
            
        except Exception as e:
            logger.error(f"Ошибка в цикле адаптации: {e}")
            adaptation_results["error"] = str(e)
        
        return adaptation_results
    
    async def _should_adapt_strategy(self, strategy_name: str, 
                                   market_conditions: MarketConditions) -> Tuple[bool, str]:
        """Определение необходимости адаптации стратегии"""
        
        # Проверка интервала с последней адаптации
        if strategy_name in self.last_adaptation_time:
            time_since_last = datetime.now() - self.last_adaptation_time[strategy_name]
            min_interval = timedelta(
                hours=self.adaptation_thresholds[self.adaptation_speed]["min_adaptation_interval_hours"]
            )
            
            if time_since_last < min_interval:
                return False, "Слишком рано для адаптации"
        
        # Анализ производительности
        performance = await self.performance_analyzer.analyze_strategy_performance(strategy_name)
        performance_threshold = self.adaptation_thresholds[self.adaptation_speed]["performance_threshold"]
        
        if performance["recent_performance_score"] < performance_threshold:
            return True, f"Низкая производительность: {performance['recent_performance_score']:.1f}"
        
        # Проверка изменения режима рынка
        if market_conditions.regime in [MarketRegime.HIGH_VOLATILITY, MarketRegime.BREAKOUT]:
            return True, f"Критический режим рынка: {market_conditions.regime.value}"
        
        # Проверка корреляционного пробоя
        if market_conditions.correlation_breakdown:
            return True, "Пробой корреляций"
        
        # Проверка экстремальных условий
        if market_conditions.volatility > 0.08 or market_conditions.rsi_level > 85 or market_conditions.rsi_level < 15:
            return True, "Экстремальные рыночные условия"
        
        return False, "Адаптация не требуется"
    
    async def _adapt_strategy(self, strategy_name: str, market_conditions: MarketConditions, 
                            adaptation_reason: str) -> Dict:
        """Адаптация конкретной стратегии"""
        
        try:
            # Получение текущих параметров
            current_strategy = self.strategy_manager.strategies[strategy_name]
            old_params = current_strategy.params
            
            # Создание новых параметров на основе рыночных условий
            new_params = await self._calculate_adapted_parameters(old_params, market_conditions)
            
            # Оценка производительности до адаптации
            performance_before = await self.performance_analyzer.analyze_strategy_performance(strategy_name)
            
            # Применение новых параметров
            current_strategy.params = new_params
            
            # Запись адаптации
            adaptation_record = AdaptationRecord(
                timestamp=datetime.now(),
                old_params=old_params,
                new_params=new_params,
                market_conditions=market_conditions,
                performance_metrics=performance_before,
                adaptation_reason=adaptation_reason,
                confidence=self._calculate_adaptation_confidence(market_conditions)
            )
            
            self.adaptation_history.append(adaptation_record)
            self.last_adaptation_time[strategy_name] = datetime.now()
            
            # Сохранение в базу данных
            await self._save_adaptation_record(adaptation_record, strategy_name)
            
            logger.info(f"Адаптирована стратегия {strategy_name}: {adaptation_reason}")
            
            return {
                "success": True,
                "strategy_name": strategy_name,
                "adaptation_reason": adaptation_reason,
                "parameters_changed": self._compare_parameters(old_params, new_params),
                "confidence": adaptation_record.confidence,
                "timestamp": adaptation_record.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка адаптации стратегии {strategy_name}: {e}")
            return {
                "success": False,
                "strategy_name": strategy_name,
                "error": str(e)
            }
    
    async def _calculate_adapted_parameters(self, old_params: StrategyParams, 
                                          market_conditions: MarketConditions) -> StrategyParams:
        """Расчет новых параметров на основе рыночных условий"""
        
        # Копируем старые параметры
        new_params = StrategyParams(
            ma_fast_period=old_params.ma_fast_period,
            ma_slow_period=old_params.ma_slow_period,
            rsi_period=old_params.rsi_period,
            rsi_oversold=old_params.rsi_oversold,
            rsi_overbought=old_params.rsi_overbought,
            macd_fast=old_params.macd_fast,
            macd_slow=old_params.macd_slow,
            macd_signal=old_params.macd_signal,
            stop_loss_pct=old_params.stop_loss_pct,
            take_profit_pct=old_params.take_profit_pct,
            max_position_size=old_params.max_position_size,
            min_confidence=old_params.min_confidence,
            strong_signal_threshold=old_params.strong_signal_threshold
        )
        
        adaptation_strength = self.adaptation_thresholds[self.adaptation_speed]["adaptation_strength"]
        
        # Адаптация под режим рынка
        if market_conditions.regime == MarketRegime.HIGH_VOLATILITY:
            # Увеличиваем стоп-лоссы и уменьшаем размер позиций
            new_params.stop_loss_pct = min(0.05, old_params.stop_loss_pct * (1 + adaptation_strength))
            new_params.take_profit_pct = max(0.015, old_params.take_profit_pct * (1 + adaptation_strength * 0.5))
            new_params.min_confidence = min(90, old_params.min_confidence + 10 * adaptation_strength)
            new_params.max_position_size = old_params.max_position_size * (1 - adaptation_strength * 0.3)
            
        elif market_conditions.regime == MarketRegime.LOW_VOLATILITY:
            # Уменьшаем стоп-лоссы и увеличиваем размер позиций
            new_params.stop_loss_pct = max(0.005, old_params.stop_loss_pct * (1 - adaptation_strength * 0.3))
            new_params.min_confidence = max(40, old_params.min_confidence - 5 * adaptation_strength)
            new_params.max_position_size = old_params.max_position_size * (1 + adaptation_strength * 0.2)
            
        elif market_conditions.regime in [MarketRegime.BULL_TREND, MarketRegime.BEAR_TREND]:
            # Адаптация под тренд
            new_params.ma_fast_period = max(5, int(old_params.ma_fast_period * (1 - adaptation_strength * 0.2)))
            new_params.take_profit_pct = old_params.take_profit_pct * (1 + adaptation_strength * 0.3)
            
        elif market_conditions.regime == MarketRegime.SIDEWAYS:
            # Адаптация под боковик
            new_params.ma_fast_period = min(20, int(old_params.ma_fast_period * (1 + adaptation_strength * 0.3)))
            new_params.rsi_oversold = max(20, old_params.rsi_oversold - 5 * adaptation_strength)
            new_params.rsi_overbought = min(90, old_params.rsi_overbought + 5 * adaptation_strength)
            
        # Адаптация под волатильность
        if market_conditions.volatility > 0.05:
            new_params.rsi_period = min(21, int(old_params.rsi_period * (1 + adaptation_strength * 0.2)))
        elif market_conditions.volatility < 0.015:
            new_params.rsi_period = max(10, int(old_params.rsi_period * (1 - adaptation_strength * 0.2)))
        
        return new_params
    
    def _calculate_adaptation_confidence(self, market_conditions: MarketConditions) -> float:
        """Расчет уверенности в адаптации"""
        
        base_confidence = 0.7
        
        # Бонус за четкие рыночные сигналы
        if market_conditions.regime in [MarketRegime.HIGH_VOLATILITY, MarketRegime.BULL_TREND, MarketRegime.BEAR_TREND]:
            base_confidence += 0.15
        
        # Бонус за экстремальные RSI
        if market_conditions.rsi_level > 80 or market_conditions.rsi_level < 20:
            base_confidence += 0.1
        
        # Штраф за неопределенность
        if market_conditions.regime == MarketRegime.SIDEWAYS:
            base_confidence -= 0.1
        
        return min(1.0, max(0.3, base_confidence))
    
    def _compare_parameters(self, old_params: StrategyParams, new_params: StrategyParams) -> List[str]:
        """Сравнение параметров для логирования изменений"""
        
        changes = []
        
        if old_params.ma_fast_period != new_params.ma_fast_period:
            changes.append(f"MA Fast: {old_params.ma_fast_period} → {new_params.ma_fast_period}")
        
        if old_params.stop_loss_pct != new_params.stop_loss_pct:
            changes.append(f"Stop Loss: {old_params.stop_loss_pct:.3f} → {new_params.stop_loss_pct:.3f}")
        
        if old_params.min_confidence != new_params.min_confidence:
            changes.append(f"Min Confidence: {old_params.min_confidence} → {new_params.min_confidence}")
        
        if old_params.max_position_size != new_params.max_position_size:
            changes.append(f"Max Position: {old_params.max_position_size} → {new_params.max_position_size}")
        
        return changes
    
    async def _save_adaptation_record(self, record: AdaptationRecord, strategy_name: str):
        """Сохранение записи об адаптации в базу данных"""
        
        try:
            conn = sqlite3.connect(self.performance_analyzer.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO strategy_adaptations 
                (timestamp, strategy_name, old_params, new_params, market_conditions, 
                 performance_before, adaptation_reason, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.timestamp.isoformat(),
                strategy_name,
                json.dumps(asdict(record.old_params)),
                json.dumps(asdict(record.new_params)),
                json.dumps(asdict(record.market_conditions)),
                json.dumps(record.performance_metrics),
                record.adaptation_reason,
                record.confidence
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Ошибка сохранения записи адаптации: {e}")
    
    async def get_adaptation_report(self) -> Dict:
        """Получение отчета по адаптациям"""
        
        recent_adaptations = self.adaptation_history[-10:]  # Последние 10
        
        return {
            "timestamp": datetime.now().isoformat(),
            "adaptation_speed": self.adaptation_speed.value,
            "total_adaptations": len(self.adaptation_history),
            "recent_adaptations_count": len(recent_adaptations),
            "strategies_with_adaptations": len(self.last_adaptation_time),
            "recent_adaptations": [
                {
                    "timestamp": record.timestamp.isoformat(),
                    "reason": record.adaptation_reason,
                    "confidence": record.confidence,
                    "market_regime": record.market_conditions.regime.value
                } for record in recent_adaptations
            ],
            "adaptation_frequency": {
                strategy: (datetime.now() - last_time).total_seconds() / 3600
                for strategy, last_time in self.last_adaptation_time.items()
            }
        }

# Тестирование адаптивной системы
async def test_adaptive_strategies():
    """Тестирование системы адаптивных стратегий"""
    
    # Инициализация с быстрой адаптацией для тестирования
    adaptive_manager = AdaptiveStrategyManager(AdaptationSpeed.FAST)
    
    # Добавление тестовой стратегии
    from strategy_risk_integration import StrategyConfig
    
    config = StrategyConfig(
        strategy_name="adaptive_test",
        symbol="BTCUSDT",
        timeframe="1h",
        risk_per_trade_pct=1.0,
        min_confidence=0.65
    )
    
    adaptive_manager.strategy_manager.add_strategy("adaptive_test", config)
    
    # Симуляция рыночных данных с высокой волатильностью
    market_data = {
        'open': 50000,
        'high': 52000,
        'low': 48000,
        'close': 49000,
        'volume': 5000,
        'volatility': 0.08  # Высокая волатильность
    }
    
    # Исторические данные
    historical_data = []
    base_price = 50000
    for i in range(100):
        price = base_price + np.random.randn() * 1000
        historical_data.append({
            'timestamp': (datetime.now() - timedelta(hours=100-i)).isoformat(),
            'close': price,
            'volume': 1000 + np.random.randint(0, 2000)
        })
    
    # Запуск цикла адаптации
    print("=== Тестирование системы адаптивных стратегий ===\n")
    
    adaptation_results = await adaptive_manager.run_adaptation_cycle(market_data, historical_data)
    
    print("Результаты адаптации:")
    print(json.dumps(adaptation_results, indent=2, ensure_ascii=False))
    
    # Отчет по адаптациям
    print("\n=== Отчет по адаптациям ===")
    adaptation_report = await adaptive_manager.get_adaptation_report()
    print(json.dumps(adaptation_report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test_adaptive_strategies())