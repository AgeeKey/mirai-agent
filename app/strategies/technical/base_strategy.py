"""
Mirai Agent - Базовая торговая стратегия
Реализация торговой стратегии на основе технических индикаторов
"""
import numpy as np
import pandas as pd
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, timedelta
import talib

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Типы торговых сигналов"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"

class MarketRegime(Enum):
    """Режимы рынка"""
    TRENDING = "trending"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"

@dataclass
class TradingSignal:
    """Структура торгового сигнала"""
    symbol: str
    signal_type: SignalType
    confidence: float  # 0-100%
    entry_price: float
    stop_loss: float
    take_profit: float
    timestamp: datetime
    indicators: Dict
    reasoning: str

@dataclass
class StrategyParams:
    """Параметры стратегии"""
    # Moving Averages
    ma_fast_period: int = 10
    ma_slow_period: int = 30
    
    # RSI
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    
    # MACD
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    
    # Risk Management
    stop_loss_pct: float = 1.0  # 1%
    take_profit_pct: float = 2.0  # 2%
    max_position_size: float = 1000.0  # USD
    
    # Signal thresholds
    min_confidence: float = 60.0
    strong_signal_threshold: float = 80.0

class TechnicalIndicators:
    """Класс для расчета технических индикаторов"""
    
    @staticmethod
    def moving_average(data: np.ndarray, period: int) -> np.ndarray:
        """Простая скользящая средняя"""
        return talib.SMA(data, timeperiod=period)
    
    @staticmethod
    def exponential_moving_average(data: np.ndarray, period: int) -> np.ndarray:
        """Экспоненциальная скользящая средняя"""
        return talib.EMA(data, timeperiod=period)
    
    @staticmethod
    def rsi(data: np.ndarray, period: int = 14) -> np.ndarray:
        """Relative Strength Index"""
        return talib.RSI(data, timeperiod=period)
    
    @staticmethod
    def macd(data: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """MACD индикатор"""
        return talib.MACD(data, fastperiod=fast, slowperiod=slow, signalperiod=signal)
    
    @staticmethod
    def bollinger_bands(data: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Bollinger Bands"""
        return talib.BBANDS(data, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev)
    
    @staticmethod
    def stochastic(high: np.ndarray, low: np.ndarray, close: np.ndarray, k_period: int = 14) -> Tuple[np.ndarray, np.ndarray]:
        """Stochastic Oscillator"""
        return talib.STOCH(high, low, close, fastk_period=k_period, slowk_period=3, slowd_period=3)
    
    @staticmethod
    def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """Average True Range"""
        return talib.ATR(high, low, close, timeperiod=period)

class MarketRegimeDetector:
    """Детектор режимов рынка"""
    
    def __init__(self):
        self.trend_threshold = 0.02  # 2% для определения тренда
        self.volatility_threshold = 0.015  # 1.5% для волатильности
    
    def detect_regime(self, data: pd.DataFrame) -> MarketRegime:
        """Определение текущего режима рынка"""
        try:
            if len(data) < 50:
                return MarketRegime.UNKNOWN
            
            close = data['close'].values
            
            # Расчет трендовости через линейную регрессию
            x = np.arange(len(close))
            slope, _ = np.polyfit(x[-20:], close[-20:], 1)
            trend_strength = abs(slope) / close[-1]
            
            # Расчет волатильности
            returns = np.diff(close) / close[:-1]
            volatility = np.std(returns[-20:])
            
            # Определение режима
            if trend_strength > self.trend_threshold:
                return MarketRegime.TRENDING
            elif volatility > self.volatility_threshold:
                return MarketRegime.VOLATILE
            else:
                return MarketRegime.SIDEWAYS
                
        except Exception as e:
            logger.error(f"Ошибка определения режима рынка: {e}")
            return MarketRegime.UNKNOWN

class BaseTradingStrategy:
    """Базовая торговая стратегия с техническими индикаторами"""
    
    def __init__(self, params: StrategyParams = None):
        self.params = params or StrategyParams()
        self.indicators = TechnicalIndicators()
        self.regime_detector = MarketRegimeDetector()
        self.position_size_calculator = self._create_position_calculator()
        
        logger.info(f"Инициализирована базовая торговая стратегия с параметрами: {self.params}")
    
    def _create_position_calculator(self):
        """Создает калькулятор размера позиции"""
        def calculate_position_size(account_balance: float, risk_per_trade: float, stop_loss_distance: float) -> float:
            """Рассчитывает размер позиции на основе риска"""
            risk_amount = account_balance * (risk_per_trade / 100)
            position_size = risk_amount / stop_loss_distance
            return min(position_size, self.params.max_position_size)
        
        return calculate_position_size
    
    async def analyze_market(self, symbol: str, data: pd.DataFrame) -> TradingSignal:
        """Основная функция анализа рынка и генерации сигналов"""
        try:
            if len(data) < max(self.params.ma_slow_period, self.params.rsi_period) + 10:
                logger.warning(f"Недостаточно данных для анализа {symbol}")
                return self._create_hold_signal(symbol, data['close'].iloc[-1] if len(data) > 0 else 0)
            
            # Подготовка данных
            close = data['close'].values
            high = data['high'].values if 'high' in data.columns else close
            low = data['low'].values if 'low' in data.columns else close
            volume = data['volume'].values if 'volume' in data.columns else np.ones_like(close)
            
            # Расчет индикаторов
            indicators = await self._calculate_indicators(close, high, low, volume)
            
            # Определение режима рынка
            market_regime = self.regime_detector.detect_regime(data)
            
            # Генерация сигнала
            signal = await self._generate_signal(symbol, close, indicators, market_regime)
            
            # Расчет уровней входа, стоп-лосса и тейк-профита
            signal = await self._calculate_levels(signal, close, indicators)
            
            logger.info(f"Сигнал для {symbol}: {signal.signal_type.value} (уверенность: {signal.confidence}%)")
            
            return signal
            
        except Exception as e:
            logger.error(f"Ошибка анализа рынка для {symbol}: {e}")
            return self._create_hold_signal(symbol, data['close'].iloc[-1] if len(data) > 0 else 0)
    
    async def _calculate_indicators(self, close: np.ndarray, high: np.ndarray, low: np.ndarray, volume: np.ndarray) -> Dict:
        """Расчет всех технических индикаторов"""
        indicators = {}
        
        try:
            # Moving Averages
            indicators['ma_fast'] = self.indicators.moving_average(close, self.params.ma_fast_period)
            indicators['ma_slow'] = self.indicators.moving_average(close, self.params.ma_slow_period)
            indicators['ema_fast'] = self.indicators.exponential_moving_average(close, self.params.ma_fast_period)
            
            # RSI
            indicators['rsi'] = self.indicators.rsi(close, self.params.rsi_period)
            
            # MACD
            macd_line, macd_signal, macd_histogram = self.indicators.macd(
                close, self.params.macd_fast, self.params.macd_slow, self.params.macd_signal
            )
            indicators['macd'] = macd_line
            indicators['macd_signal'] = macd_signal
            indicators['macd_histogram'] = macd_histogram
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self.indicators.bollinger_bands(close)
            indicators['bb_upper'] = bb_upper
            indicators['bb_middle'] = bb_middle
            indicators['bb_lower'] = bb_lower
            
            # Stochastic
            stoch_k, stoch_d = self.indicators.stochastic(high, low, close)
            indicators['stoch_k'] = stoch_k
            indicators['stoch_d'] = stoch_d
            
            # ATR для волатильности
            indicators['atr'] = self.indicators.atr(high, low, close)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Ошибка расчета индикаторов: {e}")
            return {}
    
    async def _generate_signal(self, symbol: str, close: np.ndarray, indicators: Dict, market_regime: MarketRegime) -> TradingSignal:
        """Генерация торгового сигнала на основе индикаторов"""
        
        current_price = close[-1]
        signals = []
        reasoning_parts = []
        
        # Анализ Moving Averages
        ma_signal = self._analyze_moving_averages(indicators)
        signals.append(ma_signal)
        if ma_signal != 0:
            reasoning_parts.append(f"MA сигнал: {'бычий' if ma_signal > 0 else 'медвежий'}")
        
        # Анализ RSI
        rsi_signal = self._analyze_rsi(indicators)
        signals.append(rsi_signal)
        if rsi_signal != 0:
            reasoning_parts.append(f"RSI: {'перепроданность' if rsi_signal > 0 else 'перекупленность'}")
        
        # Анализ MACD
        macd_signal = self._analyze_macd(indicators)
        signals.append(macd_signal)
        if macd_signal != 0:
            reasoning_parts.append(f"MACD: {'бычья дивергенция' if macd_signal > 0 else 'медвежья дивергенция'}")
        
        # Анализ Bollinger Bands
        bb_signal = self._analyze_bollinger_bands(close, indicators)
        signals.append(bb_signal)
        if bb_signal != 0:
            reasoning_parts.append(f"BB: {'отскок от нижней границы' if bb_signal > 0 else 'отскок от верхней границы'}")
        
        # Анализ Stochastic
        stoch_signal = self._analyze_stochastic(indicators)
        signals.append(stoch_signal)
        if stoch_signal != 0:
            reasoning_parts.append(f"Stochastic: {'разворот вверх' if stoch_signal > 0 else 'разворот вниз'}")
        
        # Агрегация сигналов
        total_signal = sum(signals)
        signal_strength = abs(total_signal)
        
        # Определение направления и уверенности
        if total_signal > 2:
            signal_type = SignalType.STRONG_BUY if signal_strength >= 4 else SignalType.BUY
            confidence = min(95, 50 + signal_strength * 10)
        elif total_signal < -2:
            signal_type = SignalType.STRONG_SELL if signal_strength >= 4 else SignalType.SELL
            confidence = min(95, 50 + signal_strength * 10)
        else:
            signal_type = SignalType.HOLD
            confidence = 30 + signal_strength * 5
        
        # Корректировка на основе режима рынка
        confidence = self._adjust_confidence_for_regime(confidence, market_regime, signal_type)
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Нет четких сигналов"
        
        return TradingSignal(
            symbol=symbol,
            signal_type=signal_type,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=0,  # Будет рассчитан позже
            take_profit=0,  # Будет рассчитан позже
            timestamp=datetime.now(),
            indicators={k: float(v[-1]) if hasattr(v, '__iter__') and len(v) > 0 else 0 
                       for k, v in indicators.items() if not np.isnan(v[-1] if hasattr(v, '__iter__') and len(v) > 0 else 0)},
            reasoning=reasoning
        )
    
    def _analyze_moving_averages(self, indicators: Dict) -> int:
        """Анализ сигналов скользящих средних"""
        try:
            ma_fast = indicators.get('ma_fast', np.array([]))
            ma_slow = indicators.get('ma_slow', np.array([]))
            
            if len(ma_fast) < 2 or len(ma_slow) < 2:
                return 0
            
            # Текущие значения
            fast_current = ma_fast[-1]
            slow_current = ma_slow[-1]
            
            # Предыдущие значения
            fast_prev = ma_fast[-2]
            slow_prev = ma_slow[-2]
            
            # Пересечение вверх (золотой крест)
            if fast_prev <= slow_prev and fast_current > slow_current:
                return 2  # Сильный бычий сигнал
            
            # Пересечение вниз (смертельный крест)
            if fast_prev >= slow_prev and fast_current < slow_current:
                return -2  # Сильный медвежий сигнал
            
            # Направление тренда
            if fast_current > slow_current:
                return 1  # Бычий тренд
            elif fast_current < slow_current:
                return -1  # Медвежий тренд
            
            return 0
            
        except Exception:
            return 0
    
    def _analyze_rsi(self, indicators: Dict) -> int:
        """Анализ RSI"""
        try:
            rsi = indicators.get('rsi', np.array([]))
            
            if len(rsi) < 2:
                return 0
            
            current_rsi = rsi[-1]
            prev_rsi = rsi[-2]
            
            # Выход из зоны перепроданности
            if prev_rsi <= self.params.rsi_oversold and current_rsi > self.params.rsi_oversold:
                return 2
            
            # Вход в зону перекупленности
            if prev_rsi >= self.params.rsi_overbought and current_rsi < self.params.rsi_overbought:
                return -2
            
            # Простые уровни
            if current_rsi < self.params.rsi_oversold:
                return 1  # Потенциальная покупка
            elif current_rsi > self.params.rsi_overbought:
                return -1  # Потенциальная продажа
            
            return 0
            
        except Exception:
            return 0
    
    def _analyze_macd(self, indicators: Dict) -> int:
        """Анализ MACD"""
        try:
            macd_line = indicators.get('macd', np.array([]))
            macd_signal = indicators.get('macd_signal', np.array([]))
            macd_histogram = indicators.get('macd_histogram', np.array([]))
            
            if len(macd_line) < 2 or len(macd_signal) < 2:
                return 0
            
            # Пересечение MACD и сигнальной линии
            if macd_line[-2] <= macd_signal[-2] and macd_line[-1] > macd_signal[-1]:
                return 2  # Бычий сигнал
            
            if macd_line[-2] >= macd_signal[-2] and macd_line[-1] < macd_signal[-1]:
                return -2  # Медвежий сигнал
            
            # Гистограмма
            if len(macd_histogram) >= 2:
                if macd_histogram[-1] > macd_histogram[-2] > 0:
                    return 1  # Усиление бычьего импульса
                elif macd_histogram[-1] < macd_histogram[-2] < 0:
                    return -1  # Усиление медвежьего импульса
            
            return 0
            
        except Exception:
            return 0
    
    def _analyze_bollinger_bands(self, close: np.ndarray, indicators: Dict) -> int:
        """Анализ Bollinger Bands"""
        try:
            bb_upper = indicators.get('bb_upper', np.array([]))
            bb_lower = indicators.get('bb_lower', np.array([]))
            
            if len(bb_upper) < 1 or len(bb_lower) < 1 or len(close) < 2:
                return 0
            
            current_price = close[-1]
            prev_price = close[-2]
            
            # Отскок от нижней границы
            if prev_price <= bb_lower[-1] and current_price > bb_lower[-1]:
                return 2
            
            # Отскок от верхней границы
            if prev_price >= bb_upper[-1] and current_price < bb_upper[-1]:
                return -2
            
            # Позиция относительно границ
            if current_price < bb_lower[-1]:
                return 1  # Потенциальная покупка
            elif current_price > bb_upper[-1]:
                return -1  # Потенциальная продажа
            
            return 0
            
        except Exception:
            return 0
    
    def _analyze_stochastic(self, indicators: Dict) -> int:
        """Анализ Stochastic"""
        try:
            stoch_k = indicators.get('stoch_k', np.array([]))
            stoch_d = indicators.get('stoch_d', np.array([]))
            
            if len(stoch_k) < 2 or len(stoch_d) < 2:
                return 0
            
            # Пересечение %K и %D
            if stoch_k[-2] <= stoch_d[-2] and stoch_k[-1] > stoch_d[-1] and stoch_k[-1] < 30:
                return 2  # Бычий сигнал в зоне перепроданности
            
            if stoch_k[-2] >= stoch_d[-2] and stoch_k[-1] < stoch_d[-1] and stoch_k[-1] > 70:
                return -2  # Медвежий сигнал в зоне перекупленности
            
            return 0
            
        except Exception:
            return 0
    
    def _adjust_confidence_for_regime(self, confidence: float, regime: MarketRegime, signal_type: SignalType) -> float:
        """Корректировка уверенности на основе режима рынка"""
        
        if regime == MarketRegime.TRENDING:
            # В трендовом рынке усиливаем сигналы по тренду
            if signal_type in [SignalType.BUY, SignalType.STRONG_BUY, SignalType.SELL, SignalType.STRONG_SELL]:
                confidence *= 1.1
        
        elif regime == MarketRegime.SIDEWAYS:
            # В боковом тренде предпочитаем mean reversion
            if signal_type == SignalType.HOLD:
                confidence *= 1.2
            else:
                confidence *= 0.8
        
        elif regime == MarketRegime.VOLATILE:
            # В волатильном рынке снижаем уверенность
            confidence *= 0.7
        
        return min(95, max(10, confidence))
    
    async def _calculate_levels(self, signal: TradingSignal, close: np.ndarray, indicators: Dict) -> TradingSignal:
        """Расчет уровней входа, стоп-лосса и тейк-профита"""
        
        if signal.signal_type == SignalType.HOLD:
            return signal
        
        try:
            current_price = signal.entry_price
            atr = indicators.get('atr', np.array([np.nan]))[-1]
            
            # Используем ATR для динамического расчета уровней
            if not np.isnan(atr):
                # Стоп-лосс на основе ATR
                stop_distance = atr * 1.5  # 1.5 ATR
                # Тейк-профит с соотношением риск/прибыль 1:2
                profit_distance = stop_distance * 2
            else:
                # Фиксированные проценты если ATR недоступен
                stop_distance = current_price * (self.params.stop_loss_pct / 100)
                profit_distance = current_price * (self.params.take_profit_pct / 100)
            
            if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                signal.stop_loss = current_price - stop_distance
                signal.take_profit = current_price + profit_distance
            else:  # SELL или STRONG_SELL
                signal.stop_loss = current_price + stop_distance
                signal.take_profit = current_price - profit_distance
            
            return signal
            
        except Exception as e:
            logger.error(f"Ошибка расчета уровней: {e}")
            return signal
    
    def _create_hold_signal(self, symbol: str, price: float) -> TradingSignal:
        """Создание сигнала HOLD"""
        return TradingSignal(
            symbol=symbol,
            signal_type=SignalType.HOLD,
            confidence=0,
            entry_price=price,
            stop_loss=price,
            take_profit=price,
            timestamp=datetime.now(),
            indicators={},
            reasoning="Недостаточно данных для анализа"
        )
    
    async def validate_signal(self, signal: TradingSignal, account_balance: float = 10000) -> bool:
        """Валидация торгового сигнала"""
        
        # Проверка минимальной уверенности
        if signal.confidence < self.params.min_confidence:
            logger.info(f"Сигнал отклонен: низкая уверенность {signal.confidence}%")
            return False
        
        # Проверка корректности уровней
        if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            if signal.stop_loss >= signal.entry_price:
                logger.warning("Некорректный стоп-лосс для покупки")
                return False
        
        elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
            if signal.stop_loss <= signal.entry_price:
                logger.warning("Некорректный стоп-лосс для продажи")
                return False
        
        # Проверка размера риска
        risk_amount = abs(signal.entry_price - signal.stop_loss)
        risk_percentage = (risk_amount / signal.entry_price) * 100
        
        if risk_percentage > self.params.stop_loss_pct * 2:  # Максимум в 2 раза больше заданного
            logger.warning(f"Слишком высокий риск: {risk_percentage}%")
            return False
        
        return True
    
    def get_strategy_info(self) -> Dict:
        """Информация о стратегии"""
        return {
            "name": "Base Technical Strategy",
            "version": "1.0",
            "description": "Базовая стратегия с техническими индикаторами",
            "indicators": ["MA", "RSI", "MACD", "Bollinger Bands", "Stochastic"],
            "parameters": {
                "ma_fast_period": self.params.ma_fast_period,
                "ma_slow_period": self.params.ma_slow_period,
                "rsi_period": self.params.rsi_period,
                "stop_loss_pct": self.params.stop_loss_pct,
                "take_profit_pct": self.params.take_profit_pct,
                "min_confidence": self.params.min_confidence
            },
            "risk_management": {
                "max_position_size": self.params.max_position_size,
                "stop_loss_percentage": self.params.stop_loss_pct,
                "risk_reward_ratio": self.params.take_profit_pct / self.params.stop_loss_pct
            }
        }

# Пример использования
async def test_strategy():
    """Тестирование стратегии"""
    
    # Создаем тестовые данные
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    
    # Генерируем цены с трендом
    base_price = 50000
    trend = np.cumsum(np.random.randn(100) * 0.001)
    noise = np.random.randn(100) * 0.02
    prices = base_price * (1 + trend + noise)
    
    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.randn(100) * 0.001),
        'high': prices * (1 + np.abs(np.random.randn(100)) * 0.002),
        'low': prices * (1 - np.abs(np.random.randn(100)) * 0.002),
        'close': prices,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    # Инициализируем стратегию
    strategy = BaseTradingStrategy()
    
    # Анализируем рынок
    signal = await strategy.analyze_market("BTCUSDT", data)
    
    print(f"Торговый сигнал: {signal.signal_type.value}")
    print(f"Уверенность: {signal.confidence}%")
    print(f"Цена входа: ${signal.entry_price:.2f}")
    print(f"Стоп-лосс: ${signal.stop_loss:.2f}")
    print(f"Тейк-профит: ${signal.take_profit:.2f}")
    print(f"Обоснование: {signal.reasoning}")
    
    # Валидация сигнала
    is_valid = await strategy.validate_signal(signal)
    print(f"Сигнал валиден: {is_valid}")
    
    # Информация о стратегии
    info = strategy.get_strategy_info()
    print(f"\nИнформация о стратегии: {json.dumps(info, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_strategy())