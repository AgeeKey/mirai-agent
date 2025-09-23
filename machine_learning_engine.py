#!/usr/bin/env python3
"""
Mirai Machine Learning & Adaptive System
Система машинного обучения с автоматической адаптацией и накоплением опыта
"""

import asyncio
import logging
import json
import numpy as np
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import pickle
import hashlib
import time
import sys
import os
from collections import defaultdict, deque
import random
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Добавляем пути для импорта ИИ модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ai_integration import MiraiAICoordinator
    from knowledge_base import MiraiKnowledgeBase
    from intelligent_algorithms import IntelligentAlgorithmManager
    from autonomous_content_engine import MiraiContentEngine
    AI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ ИИ компоненты недоступны: {e}")
    AI_AVAILABLE = False

@dataclass
class LearningExperience:
    """Опыт обучения системы"""
    experience_id: str
    timestamp: datetime
    context: Dict[str, Any]
    action_taken: str
    outcome: Dict[str, Any]
    reward: float
    confidence: float
    learning_type: str  # prediction, trading, content, optimization
    metadata: Dict[str, Any]

@dataclass
class ModelPerformance:
    """Метрики производительности модели"""
    model_id: str
    model_type: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    mse: float
    r2_score: float
    training_time: float
    prediction_time: float
    last_updated: datetime

class AdaptiveModel:
    """Адаптивная модель машинного обучения"""
    
    def __init__(self, model_type: str, model_id: str):
        self.model_type = model_type
        self.model_id = model_id
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.performance_history = []
        self.feature_importance = {}
        self.last_training = None
        self.training_data = []
        self.prediction_cache = {}
        
        # Параметры адаптации
        self.adaptation_threshold = 0.1  # Порог для переобучения
        self.max_training_samples = 10000
        self.retrain_frequency = timedelta(hours=6)
        
        self.initialize_model()
    
    def initialize_model(self):
        """Инициализация модели в зависимости от типа"""
        if self.model_type == 'price_prediction':
            self.model = RandomForestRegressor(
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'signal_classification':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                random_state=42
            )
        elif self.model_type == 'content_quality':
            self.model = RandomForestRegressor(
                n_estimators=50,
                random_state=42
            )
        else:
            # Универсальная модель
            self.model = RandomForestRegressor(
                n_estimators=75,
                random_state=42
            )
    
    def add_training_data(self, features: np.ndarray, targets: np.ndarray, context: Dict = None):
        """Добавление данных для обучения"""
        self.training_data.append({
            'features': features,
            'targets': targets,
            'timestamp': datetime.now(),
            'context': context or {}
        })
        
        # Ограничиваем размер тренировочных данных
        if len(self.training_data) > self.max_training_samples:
            self.training_data = self.training_data[-self.max_training_samples:]
    
    def should_retrain(self) -> bool:
        """Проверка необходимости переобучения"""
        if not self.last_training:
            return len(self.training_data) > 50
        
        # Проверка по времени
        time_passed = datetime.now() - self.last_training
        if time_passed > self.retrain_frequency:
            return True
        
        # Проверка по количеству новых данных
        recent_data = [
            d for d in self.training_data 
            if d['timestamp'] > self.last_training
        ]
        
        return len(recent_data) > 100
    
    async def train_model(self) -> Dict[str, Any]:
        """Обучение модели"""
        if len(self.training_data) < 10:
            return {'status': 'insufficient_data', 'samples': len(self.training_data)}
        
        start_time = time.time()
        
        try:
            # Подготовка данных
            all_features = []
            all_targets = []
            
            for data_point in self.training_data:
                features = data_point['features']
                targets = data_point['targets']
                
                if features.ndim == 1:
                    features = features.reshape(1, -1)
                
                all_features.append(features)
                all_targets.extend(targets if isinstance(targets, (list, np.ndarray)) else [targets])
            
            # Объединение данных
            X = np.vstack(all_features)
            y = np.array(all_targets)
            
            # Нормализация
            X_scaled = self.scaler.fit_transform(X)
            
            # Разделение на train/test
            if len(X_scaled) > 20:
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y, test_size=0.2, random_state=42
                )
            else:
                X_train, X_test = X_scaled, X_scaled
                y_train, y_test = y, y
            
            # Обучение
            self.model.fit(X_train, y_train)
            
            # Оценка производительности
            train_predictions = self.model.predict(X_train)
            test_predictions = self.model.predict(X_test)
            
            # Метрики
            performance = {
                'train_r2': r2_score(y_train, train_predictions) if len(y_train) > 1 else 0,
                'test_r2': r2_score(y_test, test_predictions) if len(y_test) > 1 else 0,
                'train_mse': mean_squared_error(y_train, train_predictions),
                'test_mse': mean_squared_error(y_test, test_predictions),
                'training_time': time.time() - start_time,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'feature_count': X.shape[1]
            }
            
            # Важность признаков
            if hasattr(self.model, 'feature_importances_'):
                self.feature_importance = {
                    f'feature_{i}': importance 
                    for i, importance in enumerate(self.model.feature_importances_)
                }
            
            self.performance_history.append(performance)
            self.last_training = datetime.now()
            
            return {
                'status': 'success',
                'performance': performance,
                'model_id': self.model_id,
                'training_samples': len(self.training_data)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'model_id': self.model_id
            }
    
    def predict(self, features: np.ndarray, cache_key: str = None) -> Dict[str, Any]:
        """Прогнозирование"""
        if self.model is None:
            return {'error': 'Model not trained'}
        
        # Проверка кэша
        if cache_key and cache_key in self.prediction_cache:
            return self.prediction_cache[cache_key]
        
        start_time = time.time()
        
        try:
            # Подготовка данных
            if features.ndim == 1:
                features = features.reshape(1, -1)
            
            # Нормализация
            features_scaled = self.scaler.transform(features)
            
            # Прогноз
            prediction = self.model.predict(features_scaled)
            
            # Уверенность (для регрессии - через стандартное отклонение предикторов)
            confidence = 0.8  # Заглушка, можно улучшить
            
            result = {
                'prediction': prediction.tolist() if isinstance(prediction, np.ndarray) else prediction,
                'confidence': confidence,
                'prediction_time': time.time() - start_time,
                'model_id': self.model_id,
                'features_count': features.shape[1]
            }
            
            # Кэширование
            if cache_key:
                self.prediction_cache[cache_key] = result
                # Очистка старого кэша
                if len(self.prediction_cache) > 1000:
                    keys_to_remove = list(self.prediction_cache.keys())[:100]
                    for key in keys_to_remove:
                        del self.prediction_cache[key]
            
            return result
            
        except Exception as e:
            return {'error': str(e)}

class MiraiLearningEngine:
    """Движок машинного обучения и адаптации"""
    
    def __init__(self):
        self.logger = self.setup_logging()
        self.db_path = '/root/mirai-agent/state/learning_engine.db'
        self.models_path = '/root/mirai-agent/models'
        self.experiences_path = '/root/mirai-agent/experiences'
        
        # ИИ компоненты
        if AI_AVAILABLE:
            self.ai_coordinator = MiraiAICoordinator()
            self.knowledge_base = MiraiKnowledgeBase()
            self.algorithm_manager = IntelligentAlgorithmManager()
            self.content_engine = MiraiContentEngine()
        else:
            self.ai_coordinator = None
            self.knowledge_base = None
            self.algorithm_manager = None
            self.content_engine = None
        
        # Модели
        self.models = {}
        self.model_performance = {}
        
        # Опыт обучения
        self.experiences = deque(maxlen=100000)
        self.learning_stats = {
            'total_experiences': 0,
            'models_trained': 0,
            'predictions_made': 0,
            'avg_accuracy': 0.0,
            'start_time': datetime.now()
        }
        
        # Настройки обучения
        self.learning_config = {
            'auto_retrain': True,
            'experience_batch_size': 100,
            'min_samples_for_training': 50,
            'performance_threshold': 0.7,
            'learning_rate_decay': 0.95,
            'exploration_rate': 0.1
        }
        
        self.init_database()
        self.ensure_directories()
        self.initialize_models()
    
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/mirai-agent/logs/learning_engine.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('LearningEngine')
    
    def init_database(self):
        """Инициализация базы данных для обучения"""
        Path(self.db_path).parent.mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Таблица опытов обучения
            conn.execute('''
                CREATE TABLE IF NOT EXISTS learning_experiences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experience_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    context TEXT NOT NULL,
                    action_taken TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    reward REAL NOT NULL,
                    confidence REAL NOT NULL,
                    learning_type TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
            ''')
            
            # Таблица производительности моделей
            conn.execute('''
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    accuracy REAL NOT NULL,
                    precision_score REAL NOT NULL,
                    recall_score REAL NOT NULL,
                    f1_score REAL NOT NULL,
                    mse REAL NOT NULL,
                    r2_score REAL NOT NULL,
                    training_time REAL NOT NULL,
                    prediction_time REAL NOT NULL,
                    last_updated TEXT NOT NULL
                )
            ''')
            
            # Таблица адаптаций системы
            conn.execute('''
                CREATE TABLE IF NOT EXISTS system_adaptations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    adaptation_type TEXT NOT NULL,
                    adaptation_data TEXT NOT NULL,
                    performance_before REAL NOT NULL,
                    performance_after REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    success BOOLEAN DEFAULT TRUE
                )
            ''')
            
            conn.commit()
    
    def ensure_directories(self):
        """Создание необходимых директорий"""
        directories = [
            self.models_path,
            self.experiences_path,
            '/root/mirai-agent/learning_reports'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def initialize_models(self):
        """Инициализация моделей машинного обучения"""
        model_configs = [
            ('price_prediction', 'Прогнозирование цен активов'),
            ('signal_classification', 'Классификация торговых сигналов'),
            ('content_quality', 'Оценка качества контента'),
            ('market_sentiment', 'Анализ настроений рынка'),
            ('risk_assessment', 'Оценка рисков'),
            ('portfolio_optimization', 'Оптимизация портфеля')
        ]
        
        for model_type, description in model_configs:
            model_id = f"mirai_{model_type}_{datetime.now().strftime('%Y%m%d')}"
            self.models[model_type] = AdaptiveModel(model_type, model_id)
            self.logger.info(f"🤖 Инициализирована модель: {model_type}")
    
    async def add_learning_experience(self, context: Dict[str, Any], action: str, 
                                    outcome: Dict[str, Any], reward: float,
                                    learning_type: str = 'general') -> str:
        """Добавление опыта обучения"""
        experience_id = hashlib.md5(
            f"{datetime.now().isoformat()}_{action}_{learning_type}".encode()
        ).hexdigest()
        
        experience = LearningExperience(
            experience_id=experience_id,
            timestamp=datetime.now(),
            context=context,
            action_taken=action,
            outcome=outcome,
            reward=reward,
            confidence=outcome.get('confidence', 0.5),
            learning_type=learning_type,
            metadata={'source': 'autonomous_learning'}
        )
        
        # Добавляем в память
        self.experiences.append(experience)
        self.learning_stats['total_experiences'] += 1
        
        # Сохраняем в БД
        self.save_experience_to_db(experience)
        
        # Обновляем модели, если есть соответствующие данные
        await self.update_models_with_experience(experience)
        
        self.logger.info(f"📚 Добавлен опыт обучения: {learning_type} - награда: {reward:.3f}")
        
        return experience_id
    
    def save_experience_to_db(self, experience: LearningExperience):
        """Сохранение опыта в базу данных"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO learning_experiences 
                (experience_id, timestamp, context, action_taken, outcome, 
                 reward, confidence, learning_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experience.experience_id,
                experience.timestamp.isoformat(),
                json.dumps(experience.context, ensure_ascii=False),
                experience.action_taken,
                json.dumps(experience.outcome, ensure_ascii=False),
                experience.reward,
                experience.confidence,
                experience.learning_type,
                json.dumps(experience.metadata, ensure_ascii=False)
            ))
    
    async def update_models_with_experience(self, experience: LearningExperience):
        """Обновление моделей на основе опыта"""
        learning_type = experience.learning_type
        
        try:
            # Определяем, какую модель обновлять
            if learning_type in ['trading', 'signal']:
                await self.update_trading_models(experience)
            elif learning_type in ['content', 'article']:
                await self.update_content_models(experience)
            elif learning_type in ['prediction', 'forecast']:
                await self.update_prediction_models(experience)
            elif learning_type == 'risk':
                await self.update_risk_models(experience)
            
            # Общие обновления
            await self.update_general_models(experience)
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка обновления моделей: {e}")
    
    async def update_trading_models(self, experience: LearningExperience):
        """Обновление торговых моделей"""
        if 'signal_classification' in self.models:
            model = self.models['signal_classification']
            
            # Извлекаем признаки из контекста
            context = experience.context
            features = self.extract_trading_features(context)
            
            # Цель - успешность сигнала
            target = 1 if experience.reward > 0 else 0
            
            if features is not None:
                model.add_training_data(features, np.array([target]), context)
                
                if model.should_retrain():
                    result = await model.train_model()
                    self.logger.info(f"🔄 Модель signal_classification переобучена: {result['status']}")
    
    async def update_content_models(self, experience: LearningExperience):
        """Обновление моделей контента"""
        if 'content_quality' in self.models:
            model = self.models['content_quality']
            
            # Извлекаем признаки контента
            context = experience.context
            features = self.extract_content_features(context)
            
            # Цель - качество контента
            target = experience.reward
            
            if features is not None:
                model.add_training_data(features, np.array([target]), context)
                
                if model.should_retrain():
                    result = await model.train_model()
                    self.logger.info(f"🔄 Модель content_quality переобучена: {result['status']}")
    
    async def update_prediction_models(self, experience: LearningExperience):
        """Обновление прогностических моделей"""
        if 'price_prediction' in self.models:
            model = self.models['price_prediction']
            
            # Извлекаем рыночные признаки
            context = experience.context
            features = self.extract_market_features(context)
            
            # Цель - фактическая цена или изменение
            target = experience.outcome.get('actual_price', experience.reward)
            
            if features is not None:
                model.add_training_data(features, np.array([target]), context)
                
                if model.should_retrain():
                    result = await model.train_model()
                    self.logger.info(f"🔄 Модель price_prediction переобучена: {result['status']}")
    
    async def update_risk_models(self, experience: LearningExperience):
        """Обновление моделей риска"""
        if 'risk_assessment' in self.models:
            model = self.models['risk_assessment']
            
            # Извлекаем признаки риска
            context = experience.context
            features = self.extract_risk_features(context)
            
            # Цель - уровень риска
            target = experience.outcome.get('risk_level', abs(experience.reward))
            
            if features is not None:
                model.add_training_data(features, np.array([target]), context)
                
                if model.should_retrain():
                    result = await model.train_model()
                    self.logger.info(f"🔄 Модель risk_assessment переобучена: {result['status']}")
    
    async def update_general_models(self, experience: LearningExperience):
        """Обновление общих моделей"""
        # Обновление модели настроений рынка
        if 'market_sentiment' in self.models:
            model = self.models['market_sentiment']
            context = experience.context
            
            # Простые признаки настроений
            features = np.array([
                experience.reward,
                experience.confidence,
                hash(experience.action_taken) % 100,
                len(str(experience.outcome))
            ]).reshape(1, -1)
            
            sentiment_score = (experience.reward + 1) / 2  # Нормализация к [0, 1]
            
            model.add_training_data(features, np.array([sentiment_score]), context)
    
    def extract_trading_features(self, context: Dict[str, Any]) -> Optional[np.ndarray]:
        """Извлечение признаков для торговых моделей"""
        try:
            features = []
            
            # Основные рыночные данные
            market_data = context.get('market_data', {})
            features.extend([
                market_data.get('current_price', 0),
                market_data.get('volume_24h', 0),
                market_data.get('price_change_24h', 0),
                market_data.get('volatility', 0),
                market_data.get('rsi', 50)
            ])
            
            # Технические индикаторы
            features.extend([
                1 if market_data.get('trend_direction') == 'up' else 0,
                1 if market_data.get('macd_signal') == 'buy' else 0,
                len(market_data.get('support_levels', [])),
                len(market_data.get('resistance_levels', []))
            ])
            
            # Временные признаки
            now = datetime.now()
            features.extend([
                now.hour,
                now.weekday(),
                now.month
            ])
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения торговых признаков: {e}")
            return None
    
    def extract_content_features(self, context: Dict[str, Any]) -> Optional[np.ndarray]:
        """Извлечение признаков для моделей контента"""
        try:
            features = []
            
            # Метрики контента
            content_data = context.get('content_data', {})
            features.extend([
                content_data.get('word_count', 0),
                content_data.get('section_count', 0),
                content_data.get('ai_confidence', 0.5),
                len(content_data.get('topics', [])),
                content_data.get('readability_score', 0.5)
            ])
            
            # Характеристики аудитории
            features.extend([
                1 if content_data.get('target_audience') == 'professional' else 0,
                1 if content_data.get('content_type') == 'analysis' else 0,
                content_data.get('complexity_level', 5)
            ])
            
            # Временные факторы
            now = datetime.now()
            features.extend([
                now.hour,
                1 if now.weekday() < 5 else 0  # рабочий день
            ])
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения признаков контента: {e}")
            return None
    
    def extract_market_features(self, context: Dict[str, Any]) -> Optional[np.ndarray]:
        """Извлечение рыночных признаков"""
        try:
            features = []
            
            # Базовые рыночные данные
            market_data = context.get('market_data', {})
            features.extend([
                market_data.get('current_price', 0),
                market_data.get('volume_24h', 0),
                market_data.get('price_change_24h', 0),
                market_data.get('volatility', 0),
                market_data.get('market_cap', 0)
            ])
            
            # Индикаторы
            features.extend([
                market_data.get('rsi', 50),
                market_data.get('macd', 0),
                market_data.get('bollinger_position', 0.5),
                market_data.get('volume_ratio', 1.0)
            ])
            
            # Внешние факторы
            features.extend([
                market_data.get('fear_greed_index', 50),
                1 if market_data.get('market_sentiment') == 'bullish' else 0
            ])
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения рыночных признаков: {e}")
            return None
    
    def extract_risk_features(self, context: Dict[str, Any]) -> Optional[np.ndarray]:
        """Извлечение признаков риска"""
        try:
            features = []
            
            # Данные позиции
            position_data = context.get('position_data', {})
            features.extend([
                position_data.get('position_size', 0),
                position_data.get('leverage', 1),
                position_data.get('stop_loss_distance', 0),
                position_data.get('take_profit_distance', 0)
            ])
            
            # Рыночные условия
            market_data = context.get('market_data', {})
            features.extend([
                market_data.get('volatility', 0),
                market_data.get('volume_24h', 0),
                market_data.get('price_change_24h', 0)
            ])
            
            # Временные риски
            now = datetime.now()
            features.extend([
                1 if now.weekday() >= 5 else 0,  # выходные
                now.hour,
                1 if 9 <= now.hour <= 16 else 0  # торговые часы
            ])
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения признаков риска: {e}")
            return None
    
    async def make_prediction(self, model_type: str, features: Dict[str, Any], 
                            cache_key: str = None) -> Dict[str, Any]:
        """Создание прогноза с помощью модели"""
        if model_type not in self.models:
            return {'error': f'Model {model_type} not found'}
        
        model = self.models[model_type]
        
        # Извлекаем признаки
        if model_type == 'price_prediction':
            feature_array = self.extract_market_features({'market_data': features})
        elif model_type == 'signal_classification':
            feature_array = self.extract_trading_features({'market_data': features})
        elif model_type == 'content_quality':
            feature_array = self.extract_content_features({'content_data': features})
        elif model_type == 'risk_assessment':
            feature_array = self.extract_risk_features(features)
        else:
            # Общий случай
            feature_array = np.array(list(features.values())).reshape(1, -1)
        
        if feature_array is None:
            return {'error': 'Failed to extract features'}
        
        # Делаем прогноз
        result = model.predict(feature_array, cache_key)
        
        self.learning_stats['predictions_made'] += 1
        
        self.logger.info(f"🔮 Прогноз {model_type}: {result.get('prediction', 'N/A')}")
        
        return result
    
    async def optimize_system_parameters(self) -> Dict[str, Any]:
        """Автоматическая оптимизация параметров системы"""
        self.logger.info("⚙️ Запуск автоматической оптимизации системы")
        
        optimization_results = {}
        
        # Анализируем производительность моделей
        for model_type, model in self.models.items():
            if model.performance_history:
                recent_performance = model.performance_history[-5:]  # Последние 5 обучений
                avg_performance = np.mean([p.get('test_r2', 0) for p in recent_performance])
                
                # Если производительность падает, корректируем параметры
                if avg_performance < self.learning_config['performance_threshold']:
                    await self.optimize_model_parameters(model_type, model)
                    optimization_results[model_type] = 'optimized'
                else:
                    optimization_results[model_type] = 'stable'
        
        # Оптимизация глобальных параметров
        await self.optimize_global_parameters()
        
        # Адаптация к рыночным условиям
        await self.adapt_to_market_conditions()
        
        self.logger.info(f"✅ Оптимизация завершена: {optimization_results}")
        
        return {
            'status': 'completed',
            'models_optimized': optimization_results,
            'timestamp': datetime.now().isoformat()
        }
    
    async def optimize_model_parameters(self, model_type: str, model: AdaptiveModel):
        """Оптимизация параметров конкретной модели"""
        self.logger.info(f"🔧 Оптимизация модели {model_type}")
        
        # Адаптируем параметры модели
        if hasattr(model.model, 'n_estimators'):
            # Увеличиваем количество деревьев для улучшения производительности
            current_estimators = model.model.n_estimators
            new_estimators = min(current_estimators + 20, 200)
            model.model.n_estimators = new_estimators
            
            self.logger.info(f"📈 {model_type}: n_estimators {current_estimators} → {new_estimators}")
        
        # Адаптируем частоту переобучения
        if model.performance_history:
            recent_performance = model.performance_history[-3:]
            if len(recent_performance) >= 2:
                performance_trend = recent_performance[-1].get('test_r2', 0) - recent_performance[-2].get('test_r2', 0)
                
                if performance_trend < 0:  # Производительность падает
                    # Увеличиваем частоту переобучения
                    model.retrain_frequency = timedelta(hours=max(1, model.retrain_frequency.total_seconds() / 3600 - 1))
                    self.logger.info(f"⏰ {model_type}: частота переобучения увеличена")
    
    async def optimize_global_parameters(self):
        """Оптимизация глобальных параметров системы"""
        # Анализируем общую статистику
        total_experiences = len(self.experiences)
        
        if total_experiences > 1000:
            # Увеличиваем размер батча для обучения
            self.learning_config['experience_batch_size'] = min(
                self.learning_config['experience_batch_size'] + 20, 500
            )
        
        # Адаптируем скорость исследования
        recent_rewards = [exp.reward for exp in list(self.experiences)[-100:]]
        if recent_rewards:
            avg_reward = np.mean(recent_rewards)
            if avg_reward > 0.7:
                # Снижаем исследование, увеличиваем эксплуатацию
                self.learning_config['exploration_rate'] *= 0.95
            elif avg_reward < 0.3:
                # Увеличиваем исследование
                self.learning_config['exploration_rate'] = min(
                    self.learning_config['exploration_rate'] * 1.05, 0.3
                )
        
        self.logger.info(f"🌐 Глобальные параметры обновлены: exploration_rate={self.learning_config['exploration_rate']:.3f}")
    
    async def adapt_to_market_conditions(self):
        """Адаптация к рыночным условиям"""
        # Анализируем последние торговые опыты
        trading_experiences = [
            exp for exp in list(self.experiences)[-200:]
            if exp.learning_type in ['trading', 'signal']
        ]
        
        if len(trading_experiences) >= 20:
            # Анализируем успешность в разных рыночных условиях
            rewards_by_condition = defaultdict(list)
            
            for exp in trading_experiences:
                market_sentiment = exp.context.get('market_data', {}).get('market_sentiment', 'neutral')
                rewards_by_condition[market_sentiment].append(exp.reward)
            
            # Адаптируем стратегии под условия
            for condition, rewards in rewards_by_condition.items():
                if len(rewards) >= 5:
                    avg_reward = np.mean(rewards)
                    self.logger.info(f"📊 Рынок {condition}: средняя награда {avg_reward:.3f}")
                    
                    # Сохраняем адаптацию в БД
                    await self.save_adaptation_result(
                        adaptation_type='market_condition',
                        adaptation_data={'condition': condition, 'avg_reward': avg_reward},
                        performance_improvement=avg_reward
                    )
    
    async def save_adaptation_result(self, adaptation_type: str, adaptation_data: Dict,
                                   performance_improvement: float):
        """Сохранение результата адаптации"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO system_adaptations 
                (adaptation_type, adaptation_data, performance_before, performance_after, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                adaptation_type,
                json.dumps(adaptation_data, ensure_ascii=False),
                0.5,  # Базовая производительность
                performance_improvement,
                datetime.now().isoformat()
            ))
    
    async def generate_learning_report(self) -> Dict[str, Any]:
        """Генерация отчета об обучении"""
        self.logger.info("📊 Генерация отчета об обучении")
        
        # Статистика по моделям
        model_stats = {}
        for model_type, model in self.models.items():
            if model.performance_history:
                latest_performance = model.performance_history[-1]
                model_stats[model_type] = {
                    'training_samples': len(model.training_data),
                    'latest_r2': latest_performance.get('test_r2', 0),
                    'latest_mse': latest_performance.get('test_mse', 0),
                    'last_trained': model.last_training.isoformat() if model.last_training else None,
                    'performance_trend': self.calculate_performance_trend(model.performance_history)
                }
            else:
                model_stats[model_type] = {'status': 'not_trained'}
        
        # Статистика по опытам
        experiences_by_type = defaultdict(int)
        rewards_by_type = defaultdict(list)
        
        for exp in list(self.experiences)[-1000:]:  # Последние 1000 опытов
            experiences_by_type[exp.learning_type] += 1
            rewards_by_type[exp.learning_type].append(exp.reward)
        
        experience_stats = {}
        for exp_type, count in experiences_by_type.items():
            rewards = rewards_by_type[exp_type]
            experience_stats[exp_type] = {
                'count': count,
                'avg_reward': np.mean(rewards),
                'success_rate': len([r for r in rewards if r > 0]) / len(rewards)
            }
        
        # Общая статистика обучения
        uptime = datetime.now() - self.learning_stats['start_time']
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'uptime_hours': uptime.total_seconds() / 3600,
            'total_experiences': self.learning_stats['total_experiences'],
            'predictions_made': self.learning_stats['predictions_made'],
            'models_active': len([m for m in self.models.values() if m.last_training]),
            'model_statistics': model_stats,
            'experience_statistics': experience_stats,
            'learning_config': self.learning_config,
            'system_health': self.assess_system_health()
        }
        
        # Сохранение отчета
        report_path = f"/root/mirai-agent/learning_reports/learning_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"📝 Отчет об обучении сохранен: {report_path}")
        
        return report
    
    def calculate_performance_trend(self, performance_history: List[Dict]) -> str:
        """Расчет тренда производительности"""
        if len(performance_history) < 2:
            return 'insufficient_data'
        
        recent_scores = [p.get('test_r2', 0) for p in performance_history[-5:]]
        
        if len(recent_scores) >= 3:
            trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]
            
            if trend > 0.01:
                return 'improving'
            elif trend < -0.01:
                return 'declining'
            else:
                return 'stable'
        
        return 'unknown'
    
    def assess_system_health(self) -> str:
        """Оценка здоровья системы обучения"""
        healthy_models = 0
        total_models = len(self.models)
        
        for model in self.models.values():
            if model.performance_history:
                latest_performance = model.performance_history[-1]
                if latest_performance.get('test_r2', 0) > 0.5:
                    healthy_models += 1
        
        health_ratio = healthy_models / total_models if total_models > 0 else 0
        
        if health_ratio >= 0.8:
            return 'excellent'
        elif health_ratio >= 0.6:
            return 'good'
        elif health_ratio >= 0.4:
            return 'fair'
        else:
            return 'poor'
    
    async def autonomous_learning_cycle(self):
        """Автономный цикл обучения"""
        self.logger.info("🧠 Запуск автономного цикла машинного обучения")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                self.logger.info(f"🔄 Цикл обучения {cycle_count}")
                
                # Проверяем, нужно ли переобучать модели
                retrain_tasks = []
                for model_type, model in self.models.items():
                    if model.should_retrain():
                        retrain_tasks.append(model.train_model())
                        self.logger.info(f"🔄 Планируется переобучение: {model_type}")
                
                # Выполняем переобучение
                if retrain_tasks:
                    results = await asyncio.gather(*retrain_tasks, return_exceptions=True)
                    
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            self.logger.error(f"❌ Ошибка переобучения: {result}")
                        else:
                            self.learning_stats['models_trained'] += 1
                            self.logger.info(f"✅ Модель переобучена: {result.get('status', 'unknown')}")
                
                # Оптимизация системы каждые 10 циклов
                if cycle_count % 10 == 0:
                    await self.optimize_system_parameters()
                
                # Генерация отчета каждые 20 циклов
                if cycle_count % 20 == 0:
                    await self.generate_learning_report()
                
                # Симуляция получения нового опыта
                await self.simulate_learning_experience()
                
                # Пауза между циклами
                await asyncio.sleep(600)  # 10 минут
                
            except Exception as e:
                self.logger.error(f"❌ Критическая ошибка в цикле обучения {cycle_count}: {e}")
                await asyncio.sleep(300)  # Пауза при ошибке
    
    async def simulate_learning_experience(self):
        """Симуляция получения опыта обучения"""
        # Генерируем случайный опыт для демонстрации
        experience_types = ['trading', 'content', 'prediction', 'risk']
        learning_type = random.choice(experience_types)
        
        # Симулируем контекст
        context = {
            'timestamp': datetime.now().isoformat(),
            'market_data': {
                'current_price': 45000 + random.uniform(-1000, 1000),
                'volatility': random.uniform(2, 8),
                'volume_24h': random.randint(1000000, 5000000),
                'trend_direction': random.choice(['up', 'down', 'sideways'])
            }
        }
        
        # Симулируем действие и результат
        action = f"generated_{learning_type}_prediction"
        outcome = {
            'success': random.choice([True, False]),
            'confidence': random.uniform(0.5, 0.9),
            'execution_time': random.uniform(0.1, 2.0)
        }
        
        # Награда зависит от успешности
        reward = random.uniform(0.7, 1.0) if outcome['success'] else random.uniform(0.1, 0.4)
        
        # Добавляем опыт
        await self.add_learning_experience(context, action, outcome, reward, learning_type)
    
    async def start_learning_engine(self):
        """Запуск движка машинного обучения"""
        self.logger.info("🚀 Запуск автономного движка машинного обучения Mirai")
        
        # Загружаем существующие модели, если есть
        await self.load_saved_models()
        
        # Запускаем автономный цикл
        await self.autonomous_learning_cycle()
    
    async def load_saved_models(self):
        """Загрузка сохраненных моделей"""
        for model_type in self.models.keys():
            model_file = Path(self.models_path) / f"{model_type}_model.pkl"
            if model_file.exists():
                try:
                    with open(model_file, 'rb') as f:
                        saved_data = pickle.load(f)
                    
                    self.models[model_type].model = saved_data.get('model')
                    self.models[model_type].scaler = saved_data.get('scaler')
                    self.models[model_type].last_training = saved_data.get('last_training')
                    
                    self.logger.info(f"📁 Загружена модель: {model_type}")
                except Exception as e:
                    self.logger.error(f"❌ Ошибка загрузки модели {model_type}: {e}")
    
    def save_models(self):
        """Сохранение моделей"""
        for model_type, model in self.models.items():
            if model.model is not None:
                model_file = Path(self.models_path) / f"{model_type}_model.pkl"
                
                try:
                    save_data = {
                        'model': model.model,
                        'scaler': model.scaler,
                        'last_training': model.last_training,
                        'performance_history': model.performance_history
                    }
                    
                    with open(model_file, 'wb') as f:
                        pickle.dump(save_data, f)
                    
                    self.logger.info(f"💾 Сохранена модель: {model_type}")
                except Exception as e:
                    self.logger.error(f"❌ Ошибка сохранения модели {model_type}: {e}")

async def main():
    """Основная функция запуска движка обучения"""
    print("🧠 Mirai Machine Learning & Adaptive System")
    print("Инициализация автономной системы машинного обучения...")
    
    learning_engine = MiraiLearningEngine()
    
    try:
        await learning_engine.start_learning_engine()
    except KeyboardInterrupt:
        print("\n🛑 Остановка движка обучения...")
        learning_engine.save_models()
        learning_engine.logger.info("Движок обучения остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        learning_engine.save_models()
        learning_engine.logger.error(f"Критическая ошибка движка обучения: {e}")

if __name__ == "__main__":
    asyncio.run(main())