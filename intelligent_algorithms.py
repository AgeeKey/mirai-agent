#!/usr/bin/env python3
"""
Mirai Intelligent Algorithms
Система самообучающихся алгоритмов для торговли, аналитики и прогнозирования
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
import json
import logging
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
from pathlib import Path
import sqlite3
import requests
from collections import deque
import threading
import time

@dataclass
class PredictionResult:
    """Результат прогнозирования"""
    prediction: Union[float, int, str]
    confidence: float
    model_name: str
    features_used: List[str]
    timestamp: datetime
    accuracy_score: float

@dataclass
class LearningMetrics:
    """Метрики обучения модели"""
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_samples: int
    last_updated: datetime

class MarketDataCollector:
    """Сборщик рыночных данных"""
    
    def __init__(self):
        self.data_queue = deque(maxlen=10000)
        self.logger = logging.getLogger('MarketDataCollector')
        
    async def collect_market_data(self) -> Dict[str, Any]:
        """Сбор рыночных данных из различных источников"""
        try:
            # Симуляция сбора данных (в реальной версии - подключение к API)
            current_time = datetime.now()
            
            # Генерируем реалистичные данные для демонстрации
            base_price = 50000 + np.random.normal(0, 1000)
            volume = 1000000 + np.random.normal(0, 100000)
            
            market_data = {
                'timestamp': current_time.isoformat(),
                'price': base_price,
                'volume': max(0, volume),
                'high_24h': base_price * (1 + np.random.uniform(0, 0.1)),
                'low_24h': base_price * (1 - np.random.uniform(0, 0.1)),
                'change_24h': np.random.uniform(-10, 10),
                'volatility': np.random.uniform(0.1, 0.5),
                'rsi': np.random.uniform(20, 80),
                'sma_20': base_price * (1 + np.random.uniform(-0.05, 0.05)),
                'ema_12': base_price * (1 + np.random.uniform(-0.03, 0.03)),
                'macd': np.random.uniform(-500, 500),
                'bollinger_upper': base_price * 1.02,
                'bollinger_lower': base_price * 0.98,
                'support_level': base_price * 0.95,
                'resistance_level': base_price * 1.05
            }
            
            self.data_queue.append(market_data)
            return market_data
            
        except Exception as e:
            self.logger.error(f"Ошибка сбора рыночных данных: {e}")
            return {}
    
    def get_historical_data(self, hours: int = 24) -> pd.DataFrame:
        """Получение исторических данных"""
        if not self.data_queue:
            return pd.DataFrame()
        
        # Конвертируем в DataFrame
        df = pd.DataFrame(list(self.data_queue))
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Фильтруем по времени
            cutoff_time = datetime.now() - timedelta(hours=hours)
            df = df[df['timestamp'] > cutoff_time]
        
        return df

class TradingAlgorithm:
    """Алгоритм торговли с машинным обучением"""
    
    def __init__(self, name: str):
        self.name = name
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.logger = logging.getLogger(f'TradingAlgorithm_{name}')
        self.performance_history = []
        self.model_path = f'/root/mirai-agent/models/trading_{name}.joblib'
        self.is_trained = False
        
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Подготовка признаков для модели"""
        if data.empty:
            return pd.DataFrame()
        
        features = data.copy()
        
        # Технические индикаторы
        if 'price' in features.columns:
            features['price_change'] = features['price'].pct_change()
            features['price_sma_5'] = features['price'].rolling(window=5).mean()
            features['price_sma_10'] = features['price'].rolling(window=10).mean()
            features['price_volatility'] = features['price'].rolling(window=10).std()
        
        if 'volume' in features.columns:
            features['volume_change'] = features['volume'].pct_change()
            features['volume_sma'] = features['volume'].rolling(window=5).mean()
        
        # Добавляем временные признаки
        if 'timestamp' in features.columns:
            features['hour'] = pd.to_datetime(features['timestamp']).dt.hour
            features['day_of_week'] = pd.to_datetime(features['timestamp']).dt.dayofweek
        
        # Удаляем NaN значения
        features = features.fillna(method='bfill').fillna(method='ffill')
        
        return features
    
    def create_target(self, data: pd.DataFrame, prediction_type: str = 'price_direction') -> pd.Series:
        """Создание целевой переменной"""
        if data.empty or 'price' not in data.columns:
            return pd.Series()
        
        if prediction_type == 'price_direction':
            # Предсказываем направление движения цены (1 - вверх, 0 - вниз)
            return (data['price'].shift(-1) > data['price']).astype(int)
        elif prediction_type == 'price_return':
            # Предсказываем процентное изменение цены
            return data['price'].pct_change().shift(-1)
        else:
            return pd.Series()
    
    async def train_model(self, data: pd.DataFrame, prediction_type: str = 'price_direction'):
        """Обучение модели"""
        try:
            if data.empty or len(data) < 50:
                self.logger.warning("Недостаточно данных для обучения")
                return False
            
            # Подготовка признаков
            features = self.prepare_features(data)
            target = self.create_target(data, prediction_type)
            
            if features.empty or target.empty:
                self.logger.warning("Ошибка подготовки данных")
                return False
            
            # Выбираем только числовые столбцы
            numeric_features = features.select_dtypes(include=[np.number])
            
            # Удаляем строки с NaN в целевой переменной
            valid_indices = ~target.isna()
            X = numeric_features[valid_indices]
            y = target[valid_indices]
            
            if len(X) < 30:
                self.logger.warning("Недостаточно валидных данных после очистки")
                return False
            
            # Сохраняем названия признаков
            self.feature_columns = X.columns.tolist()
            
            # Нормализация признаков
            X_scaled = self.scaler.fit_transform(X)
            
            # Разделение на обучающую и тестовую выборки
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
            
            # Выбор модели в зависимости от типа предсказания
            if prediction_type == 'price_direction':
                self.model = GradientBoostingClassifier(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=3,
                    random_state=42
                )
            else:
                self.model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
            
            # Обучение модели
            self.model.fit(X_train, y_train)
            
            # Оценка качества
            train_score = self.model.score(X_train, y_train)
            test_score = self.model.score(X_test, y_test)
            
            self.logger.info(f"Модель обучена. Train score: {train_score:.3f}, Test score: {test_score:.3f}")
            
            # Сохранение модели
            Path(self.model_path).parent.mkdir(exist_ok=True)
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'prediction_type': prediction_type
            }, self.model_path)
            
            self.is_trained = True
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обучения модели: {e}")
            return False
    
    def load_model(self) -> bool:
        """Загрузка сохраненной модели"""
        try:
            if Path(self.model_path).exists():
                model_data = joblib.load(self.model_path)
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.feature_columns = model_data['feature_columns']
                self.is_trained = True
                self.logger.info("Модель успешно загружена")
                return True
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели: {e}")
        return False
    
    async def predict(self, current_data: Dict[str, Any]) -> Optional[PredictionResult]:
        """Создание прогноза"""
        try:
            if not self.is_trained:
                if not self.load_model():
                    self.logger.warning("Модель не обучена и не может быть загружена")
                    return None
            
            # Подготовка данных для прогноза
            df = pd.DataFrame([current_data])
            features = self.prepare_features(df)
            
            if features.empty:
                return None
            
            # Выбираем только нужные признаки
            feature_data = features[self.feature_columns] if self.feature_columns else features.select_dtypes(include=[np.number])
            
            if feature_data.empty:
                return None
            
            # Нормализация
            X = self.scaler.transform(feature_data)
            
            # Прогноз
            prediction = self.model.predict(X)[0]
            
            # Расчет уверенности
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(X)[0]
                confidence = max(proba)
            else:
                confidence = 0.8  # Базовая уверенность для регрессии
            
            return PredictionResult(
                prediction=prediction,
                confidence=confidence,
                model_name=self.name,
                features_used=self.feature_columns,
                timestamp=datetime.now(),
                accuracy_score=confidence
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка прогнозирования: {e}")
            return None
    
    def evaluate_performance(self, actual_value: Union[float, int], predicted_value: Union[float, int]):
        """Оценка производительности прогноза"""
        error = abs(actual_value - predicted_value)
        relative_error = error / abs(actual_value) if actual_value != 0 else float('inf')
        
        performance_record = {
            'timestamp': datetime.now().isoformat(),
            'actual': actual_value,
            'predicted': predicted_value,
            'error': error,
            'relative_error': relative_error
        }
        
        self.performance_history.append(performance_record)
        
        # Ограничиваем историю
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]

class AnalyticsEngine:
    """Аналитический движок для обработки данных"""
    
    def __init__(self):
        self.logger = logging.getLogger('AnalyticsEngine')
        self.cached_results = {}
        
    async def analyze_market_trends(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Анализ рыночных трендов"""
        try:
            if data.empty:
                return {}
            
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'data_points': len(data),
                'trends': {},
                'patterns': {},
                'indicators': {}
            }
            
            if 'price' in data.columns:
                prices = data['price']
                
                # Анализ трендов
                analysis['trends'] = {
                    'current_trend': self.detect_trend(prices),
                    'trend_strength': self.calculate_trend_strength(prices),
                    'price_volatility': prices.std(),
                    'price_range': {
                        'min': prices.min(),
                        'max': prices.max(),
                        'current': prices.iloc[-1] if len(prices) > 0 else 0
                    }
                }
                
                # Технические индикаторы
                analysis['indicators'] = {
                    'sma_20': prices.rolling(window=min(20, len(prices))).mean().iloc[-1] if len(prices) >= 20 else prices.mean(),
                    'rsi': self.calculate_rsi(prices),
                    'bollinger_position': self.calculate_bollinger_position(prices),
                    'momentum': self.calculate_momentum(prices)
                }
                
                # Паттерны
                analysis['patterns'] = {
                    'support_resistance': self.find_support_resistance(prices),
                    'breakout_probability': self.calculate_breakout_probability(prices),
                    'reversal_signals': self.detect_reversal_signals(prices)
                }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа трендов: {e}")
            return {}
    
    def detect_trend(self, prices: pd.Series) -> str:
        """Определение направления тренда"""
        if len(prices) < 10:
            return 'uncertain'
        
        recent_prices = prices.tail(10)
        slope = np.polyfit(range(len(recent_prices)), recent_prices, 1)[0]
        
        if slope > prices.mean() * 0.01:
            return 'uptrend'
        elif slope < -prices.mean() * 0.01:
            return 'downtrend'
        else:
            return 'sideways'
    
    def calculate_trend_strength(self, prices: pd.Series) -> float:
        """Расчет силы тренда"""
        if len(prices) < 10:
            return 0.0
        
        recent_prices = prices.tail(10)
        slope = abs(np.polyfit(range(len(recent_prices)), recent_prices, 1)[0])
        volatility = recent_prices.std()
        
        if volatility == 0:
            return 0.0
        
        strength = slope / volatility
        return min(1.0, strength / 10)  # Нормализация
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Расчет RSI"""
        if len(prices) < period + 1:
            return 50.0  # Нейтральное значение
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def calculate_bollinger_position(self, prices: pd.Series, period: int = 20) -> float:
        """Позиция относительно полос Боллинджера"""
        if len(prices) < period:
            return 0.5
        
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        
        current_price = prices.iloc[-1]
        upper = upper_band.iloc[-1]
        lower = lower_band.iloc[-1]
        
        if upper == lower:
            return 0.5
        
        position = (current_price - lower) / (upper - lower)
        return max(0, min(1, position))
    
    def calculate_momentum(self, prices: pd.Series, period: int = 10) -> float:
        """Расчет момента"""
        if len(prices) < period + 1:
            return 0.0
        
        momentum = prices.iloc[-1] - prices.iloc[-period-1]
        return momentum / prices.iloc[-period-1] if prices.iloc[-period-1] != 0 else 0.0
    
    def find_support_resistance(self, prices: pd.Series) -> Dict[str, float]:
        """Поиск уровней поддержки и сопротивления"""
        if len(prices) < 20:
            current_price = prices.iloc[-1] if len(prices) > 0 else 0
            return {
                'support': current_price * 0.95,
                'resistance': current_price * 1.05
            }
        
        # Простой алгоритм поиска локальных минимумов и максимумов
        recent_prices = prices.tail(50)
        
        # Поддержка - средний уровень локальных минимумов
        local_mins = []
        for i in range(2, len(recent_prices) - 2):
            if (recent_prices.iloc[i] < recent_prices.iloc[i-1] and 
                recent_prices.iloc[i] < recent_prices.iloc[i+1] and
                recent_prices.iloc[i] < recent_prices.iloc[i-2] and
                recent_prices.iloc[i] < recent_prices.iloc[i+2]):
                local_mins.append(recent_prices.iloc[i])
        
        # Сопротивление - средний уровень локальных максимумов
        local_maxs = []
        for i in range(2, len(recent_prices) - 2):
            if (recent_prices.iloc[i] > recent_prices.iloc[i-1] and 
                recent_prices.iloc[i] > recent_prices.iloc[i+1] and
                recent_prices.iloc[i] > recent_prices.iloc[i-2] and
                recent_prices.iloc[i] > recent_prices.iloc[i+2]):
                local_maxs.append(recent_prices.iloc[i])
        
        support = np.mean(local_mins) if local_mins else recent_prices.min()
        resistance = np.mean(local_maxs) if local_maxs else recent_prices.max()
        
        return {
            'support': support,
            'resistance': resistance
        }
    
    def calculate_breakout_probability(self, prices: pd.Series) -> float:
        """Вероятность пробоя"""
        if len(prices) < 20:
            return 0.5
        
        # Анализ сужения диапазона и увеличения объема
        recent_prices = prices.tail(20)
        price_range = recent_prices.max() - recent_prices.min()
        avg_range = prices.rolling(window=50).apply(lambda x: x.max() - x.min()).mean()
        
        if avg_range == 0:
            return 0.5
        
        range_ratio = price_range / avg_range
        
        # Чем меньше диапазон, тем выше вероятность пробоя
        breakout_prob = max(0.1, min(0.9, 1 - range_ratio))
        
        return breakout_prob
    
    def detect_reversal_signals(self, prices: pd.Series) -> List[str]:
        """Обнаружение сигналов разворота"""
        signals = []
        
        if len(prices) < 10:
            return signals
        
        recent_prices = prices.tail(10)
        rsi = self.calculate_rsi(prices)
        
        # Перекупленность/перепроданность
        if rsi > 70:
            signals.append('overbought')
        elif rsi < 30:
            signals.append('oversold')
        
        # Дивергенция (упрощенная версия)
        price_trend = recent_prices.iloc[-1] - recent_prices.iloc[0]
        if price_trend > 0 and rsi < 50:
            signals.append('bearish_divergence')
        elif price_trend < 0 and rsi > 50:
            signals.append('bullish_divergence')
        
        return signals

class IntelligentAlgorithmManager:
    """Менеджер интеллектуальных алгоритмов"""
    
    def __init__(self):
        self.data_collector = MarketDataCollector()
        self.analytics_engine = AnalyticsEngine()
        self.trading_algorithms = {}
        self.logger = logging.getLogger('IntelligentAlgorithmManager')
        self.is_running = False
        self.update_interval = 60  # секунды
        
        # Инициализация торговых алгоритмов
        self.init_trading_algorithms()
    
    def init_trading_algorithms(self):
        """Инициализация торговых алгоритмов"""
        algorithms = [
            'trend_following',
            'mean_reversion',
            'momentum_strategy',
            'volatility_breakout'
        ]
        
        for algo_name in algorithms:
            self.trading_algorithms[algo_name] = TradingAlgorithm(algo_name)
    
    async def start_learning_cycle(self):
        """Запуск цикла обучения"""
        self.logger.info("🚀 Запуск цикла интеллектуального обучения")
        self.is_running = True
        
        while self.is_running:
            try:
                # Сбор данных
                market_data = await self.data_collector.collect_market_data()
                
                if market_data:
                    # Получение исторических данных
                    historical_data = self.data_collector.get_historical_data(hours=168)  # Неделя
                    
                    if not historical_data.empty and len(historical_data) > 50:
                        # Анализ трендов
                        trends_analysis = await self.analytics_engine.analyze_market_trends(historical_data)
                        
                        # Обучение алгоритмов
                        await self.train_algorithms(historical_data)
                        
                        # Создание прогнозов
                        predictions = await self.generate_predictions(market_data)
                        
                        # Логирование результатов
                        self.log_learning_results(trends_analysis, predictions)
                
                # Пауза между итерациями
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Ошибка в цикле обучения: {e}")
                await asyncio.sleep(30)  # Короткая пауза при ошибке
    
    async def train_algorithms(self, data: pd.DataFrame):
        """Обучение всех алгоритмов"""
        for name, algorithm in self.trading_algorithms.items():
            try:
                success = await algorithm.train_model(data)
                if success:
                    self.logger.info(f"✅ Алгоритм {name} успешно обучен")
                else:
                    self.logger.warning(f"⚠️ Не удалось обучить алгоритм {name}")
            except Exception as e:
                self.logger.error(f"Ошибка обучения алгоритма {name}: {e}")
    
    async def generate_predictions(self, current_data: Dict[str, Any]) -> Dict[str, PredictionResult]:
        """Генерация прогнозов от всех алгоритмов"""
        predictions = {}
        
        for name, algorithm in self.trading_algorithms.items():
            try:
                prediction = await algorithm.predict(current_data)
                if prediction:
                    predictions[name] = prediction
            except Exception as e:
                self.logger.error(f"Ошибка прогнозирования для {name}: {e}")
        
        return predictions
    
    def log_learning_results(self, trends_analysis: Dict, predictions: Dict[str, PredictionResult]):
        """Логирование результатов обучения"""
        self.logger.info("📊 Результаты анализа и прогнозирования:")
        
        # Анализ трендов
        if trends_analysis.get('trends'):
            trend_info = trends_analysis['trends']
            self.logger.info(f"📈 Тренд: {trend_info.get('current_trend', 'неопределен')}")
            self.logger.info(f"💪 Сила тренда: {trend_info.get('trend_strength', 0):.3f}")
        
        # Прогнозы
        for algo_name, prediction in predictions.items():
            self.logger.info(f"🔮 {algo_name}: {prediction.prediction:.4f} (уверенность: {prediction.confidence:.3f})")
    
    def stop_learning_cycle(self):
        """Остановка цикла обучения"""
        self.logger.info("🛑 Остановка цикла обучения")
        self.is_running = False
    
    async def get_consensus_prediction(self, current_data: Dict[str, Any]) -> Optional[PredictionResult]:
        """Получение консенсус-прогноза от всех алгоритмов"""
        predictions = await self.generate_predictions(current_data)
        
        if not predictions:
            return None
        
        # Взвешенное усреднение прогнозов
        total_weight = 0
        weighted_prediction = 0
        confidence_sum = 0
        
        for prediction in predictions.values():
            weight = prediction.confidence
            total_weight += weight
            weighted_prediction += prediction.prediction * weight
            confidence_sum += prediction.confidence
        
        if total_weight == 0:
            return None
        
        consensus_prediction = weighted_prediction / total_weight
        average_confidence = confidence_sum / len(predictions)
        
        return PredictionResult(
            prediction=consensus_prediction,
            confidence=average_confidence,
            model_name='consensus',
            features_used=[],
            timestamp=datetime.now(),
            accuracy_score=average_confidence
        )

async def main():
    """Демонстрация работы интеллектуальных алгоритмов"""
    manager = IntelligentAlgorithmManager()
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Запуск на несколько циклов для демонстрации
        await asyncio.wait_for(manager.start_learning_cycle(), timeout=300)  # 5 минут
    except asyncio.TimeoutError:
        manager.stop_learning_cycle()
        print("✅ Демонстрация завершена")

if __name__ == "__main__":
    asyncio.run(main())