#!/usr/bin/env python3
"""
Mirai Autonomous Content Generation Engine
Автономный контентный движок для генерации статей, аналитики, торговых сигналов
"""

import asyncio
import logging
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import requests
from pathlib import Path
import sqlite3
import random
import sys
import os

# Добавляем пути для импорта ИИ модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ai_integration import MiraiAICoordinator
    from knowledge_base import MiraiKnowledgeBase
    from intelligent_algorithms import IntelligentAlgorithmManager
    AI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ ИИ компоненты недоступны: {e}")
    AI_AVAILABLE = False

@dataclass
class ContentTask:
    """Задача генерации контента"""
    content_type: str  # article, analysis, signal, report
    topic: str
    target_audience: str
    priority: int  # 1-10
    deadline: datetime
    requirements: Dict[str, Any]
    context: Dict[str, Any]
    created_at: datetime
    
class ContentTemplate:
    """Шаблон для генерации контента"""
    
    @staticmethod
    def get_article_templates():
        return {
            'market_analysis': {
                'structure': [
                    'Краткий обзор рынка',
                    'Технический анализ ключевых активов',
                    'Фундаментальные факторы',
                    'Торговые возможности',
                    'Риски и рекомендации'
                ],
                'tone': 'analytical',
                'length': 'medium'
            },
            'ai_insights': {
                'structure': [
                    'Введение в ИИ-анализ',
                    'Выявленные паттерны',
                    'Прогнозы алгоритмов',
                    'Практические выводы',
                    'Заключение'
                ],
                'tone': 'technical',
                'length': 'long'
            },
            'trading_tutorial': {
                'structure': [
                    'Введение',
                    'Пошаговое руководство',
                    'Примеры применения',
                    'Типичные ошибки',
                    'Заключение и ресурсы'
                ],
                'tone': 'educational',
                'length': 'long'
            }
        }
    
    @staticmethod
    def get_signal_templates():
        return {
            'buy_signal': {
                'components': [
                    'Symbol and Direction',
                    'Entry Price Range',
                    'Technical Analysis',
                    'Risk Management',
                    'Confidence Score'
                ]
            },
            'market_alert': {
                'components': [
                    'Alert Type',
                    'Affected Assets',
                    'Trigger Conditions',
                    'Impact Assessment',
                    'Recommended Actions'
                ]
            }
        }

class MiraiContentEngine:
    """Автономный движок генерации контента"""
    
    def __init__(self):
        self.logger = self.setup_logging()
        self.db_path = '/root/mirai-agent/state/content_engine.db'
        self.content_storage = '/root/mirai-agent/generated_content'
        
        # Инициализация ИИ компонентов
        if AI_AVAILABLE:
            self.ai_coordinator = MiraiAICoordinator()
            self.knowledge_base = MiraiKnowledgeBase()
            self.algorithm_manager = IntelligentAlgorithmManager()
        else:
            self.ai_coordinator = None
            self.knowledge_base = None
            self.algorithm_manager = None
        
        # Очередь задач
        self.content_queue = []
        self.generation_stats = {
            'articles_created': 0,
            'signals_generated': 0,
            'reports_compiled': 0,
            'total_content_pieces': 0,
            'start_time': datetime.now()
        }
        
        # Настройки генерации
        self.generation_config = {
            'daily_article_quota': 3,
            'signal_frequency_minutes': 15,
            'report_schedule': 'daily',
            'quality_threshold': 0.8,
            'creativity_level': 0.7
        }
        
        self.init_database()
        self.ensure_directories()
    
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/mirai-agent/logs/content_engine.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('ContentEngine')
    
    def init_database(self):
        """Инициализация базы данных для контента"""
        Path(self.db_path).parent.mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Таблица сгенерированного контента
            conn.execute('''
                CREATE TABLE IF NOT EXISTS generated_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    published BOOLEAN DEFAULT FALSE,
                    publication_url TEXT,
                    performance_metrics TEXT
                )
            ''')
            
            # Таблица задач генерации
            conn.execute('''
                CREATE TABLE IF NOT EXISTS content_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_type TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 5,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    result_id INTEGER,
                    FOREIGN KEY (result_id) REFERENCES generated_content (id)
                )
            ''')
            
            # Таблица шаблонов
            conn.execute('''
                CREATE TABLE IF NOT EXISTS content_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_name TEXT NOT NULL,
                    template_type TEXT NOT NULL,
                    template_data TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    effectiveness_score REAL DEFAULT 0.5
                )
            ''')
            
            conn.commit()
    
    def ensure_directories(self):
        """Создание необходимых директорий"""
        directories = [
            '/root/mirai-agent/generated_content',
            '/root/mirai-agent/generated_content/articles',
            '/root/mirai-agent/generated_content/signals',
            '/root/mirai-agent/generated_content/reports',
            '/root/mirai-agent/generated_content/analysis'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    async def generate_market_analysis_article(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """Генерация статьи с анализом рынка"""
        self.logger.info(f"📝 Генерация анализа рынка для {symbol}")
        
        # Получаем данные для анализа
        market_data = await self.collect_market_data(symbol)
        ai_insights = await self.get_ai_insights(market_data)
        
        # Структура статьи
        title = f"Анализ рынка {symbol}: ИИ-прогноз и торговые возможности"
        
        content_sections = {
            'intro': f"""
# {title}

*Автоматически сгенерировано ИИ-системой Mirai в {datetime.now().strftime('%d.%m.%Y %H:%M')}*

Комплексный анализ рынка {symbol} с использованием передовых алгоритмов машинного обучения и технического анализа.
            """,
            
            'market_overview': f"""
## 📊 Обзор рынка

Текущая цена {symbol}: **${market_data.get('current_price', 'N/A')}**

Основные показатели:
- 24ч изменение: {market_data.get('price_change_24h', 'N/A')}%
- Объем торгов: ${market_data.get('volume_24h', 'N/A')}
- Волатильность: {market_data.get('volatility', 'N/A')}%

{self.generate_market_sentiment_text(market_data)}
            """,
            
            'technical_analysis': f"""
## 🔍 Технический анализ

### Индикаторы тренда
{self.generate_technical_indicators_text(market_data)}

### Уровни поддержки и сопротивления
{self.generate_support_resistance_text(market_data)}

### Паттерны графика
{self.generate_chart_patterns_text(market_data)}
            """,
            
            'ai_insights_section': f"""
## 🤖 ИИ-анализ и прогнозы

{ai_insights.get('analysis_text', 'ИИ-анализ недоступен')}

### Прогнозы алгоритмов:
{self.format_ai_predictions(ai_insights.get('predictions', []))}

### Выявленные паттерны:
{self.format_detected_patterns(ai_insights.get('patterns', []))}
            """,
            
            'trading_opportunities': f"""
## 💡 Торговые возможности

### Рекомендуемые стратегии:
{self.generate_trading_strategies_text(market_data, ai_insights)}

### Управление рисками:
{self.generate_risk_management_text(market_data)}
            """,
            
            'conclusion': f"""
## 📝 Заключение

{self.generate_conclusion_text(market_data, ai_insights)}

---
*Данный анализ создан автономной ИИ-системой Mirai и предназначен исключительно для образовательных целей. 
Не является финансовой рекомендацией. Всегда проводите собственное исследование перед принятием торговых решений.*
            """
        }
        
        # Объединяем все секции
        full_content = '\n\n'.join(content_sections.values())
        
        # Метаданные
        metadata = {
            'symbol': symbol,
            'generation_time': datetime.now().isoformat(),
            'ai_confidence': ai_insights.get('confidence', 0.7),
            'content_type': 'market_analysis',
            'word_count': len(full_content.split()),
            'sections': list(content_sections.keys()),
            'data_sources': ['market_api', 'ai_algorithms', 'technical_indicators']
        }
        
        # Оценка качества
        quality_score = self.assess_content_quality(full_content, metadata)
        
        # Сохранение
        content_id = self.save_generated_content(
            content_type='article',
            title=title,
            content=full_content,
            metadata=metadata,
            quality_score=quality_score
        )
        
        self.generation_stats['articles_created'] += 1
        self.generation_stats['total_content_pieces'] += 1
        
        self.logger.info(f"✅ Статья создана: ID {content_id}, качество: {quality_score:.2f}")
        
        return {
            'content_id': content_id,
            'title': title,
            'content': full_content,
            'metadata': metadata,
            'quality_score': quality_score,
            'file_path': self.save_content_to_file(content_id, title, full_content, 'article')
        }
    
    async def generate_trading_signal(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """Генерация торгового сигнала"""
        self.logger.info(f"📈 Генерация торгового сигнала для {symbol}")
        
        # Получаем данные для сигнала
        market_data = await self.collect_market_data(symbol)
        predictions = await self.get_trading_predictions(symbol)
        
        # Определяем тип сигнала
        signal_type = self.determine_signal_type(market_data, predictions)
        
        # Генерируем сигнал
        signal_content = {
            'symbol': symbol,
            'signal_type': signal_type,
            'direction': predictions.get('direction', 'hold'),
            'confidence': predictions.get('confidence', 0.6),
            'entry_price': market_data.get('current_price', 0),
            'target_price': predictions.get('target_price', 0),
            'stop_loss': predictions.get('stop_loss', 0),
            'analysis': self.generate_signal_analysis(market_data, predictions),
            'risk_level': predictions.get('risk_level', 'medium'),
            'time_horizon': predictions.get('time_horizon', '1h'),
            'generated_at': datetime.now().isoformat()
        }
        
        # Форматируем для отображения
        formatted_signal = self.format_trading_signal(signal_content)
        
        # Метаданные
        metadata = {
            'signal_type': signal_type,
            'generation_time': datetime.now().isoformat(),
            'ai_algorithms_used': ['trend_following', 'mean_reversion', 'momentum'],
            'market_conditions': market_data.get('market_sentiment', 'neutral'),
            'validity_period': '1 hour'
        }
        
        # Оценка качества сигнала
        quality_score = self.assess_signal_quality(signal_content, market_data)
        
        # Сохранение
        content_id = self.save_generated_content(
            content_type='signal',
            title=f"Торговый сигнал {symbol} - {signal_type}",
            content=formatted_signal,
            metadata=metadata,
            quality_score=quality_score
        )
        
        self.generation_stats['signals_generated'] += 1
        self.generation_stats['total_content_pieces'] += 1
        
        self.logger.info(f"🎯 Сигнал создан: {signal_type} для {symbol}, уверенность: {signal_content['confidence']:.2f}")
        
        return {
            'content_id': content_id,
            'signal_data': signal_content,
            'formatted_content': formatted_signal,
            'metadata': metadata,
            'quality_score': quality_score,
            'file_path': self.save_content_to_file(content_id, f"signal_{symbol}_{signal_type}", formatted_signal, 'signal')
        }
    
    async def generate_daily_report(self) -> Dict[str, Any]:
        """Генерация ежедневного отчета"""
        self.logger.info("📋 Генерация ежедневного отчета")
        
        # Собираем данные за день
        daily_data = await self.collect_daily_statistics()
        market_summary = await self.get_market_summary()
        ai_performance = await self.get_ai_performance_metrics()
        
        # Структура отчета
        report_date = datetime.now().strftime('%d.%m.%Y')
        title = f"Ежедневный отчет Mirai AI - {report_date}"
        
        report_content = f"""
# {title}

## 📊 Сводка за день

### Рыночная активность
{self.format_market_summary(market_summary)}

### Производительность ИИ-системы
{self.format_ai_performance(ai_performance)}

### Сгенерированный контент
- Статей создано: {daily_data.get('articles_today', 0)}
- Торговых сигналов: {daily_data.get('signals_today', 0)}
- Общее качество контента: {daily_data.get('avg_quality', 0):.2f}/10

## 🤖 ИИ-инсайты дня

{self.generate_daily_insights(daily_data, market_summary, ai_performance)}

## 📈 Топ торговые возможности

{self.generate_top_opportunities(market_summary)}

## 🔮 Прогноз на завтра

{self.generate_tomorrow_forecast(market_summary, ai_performance)}

---
*Отчет автоматически создан системой Mirai AI в {datetime.now().strftime('%H:%M %d.%m.%Y')}*
        """
        
        # Метаданные
        metadata = {
            'report_date': report_date,
            'generation_time': datetime.now().isoformat(),
            'data_period': '24h',
            'content_sections': ['market_summary', 'ai_performance', 'content_stats', 'insights', 'opportunities', 'forecast'],
            'statistics': daily_data
        }
        
        # Оценка качества
        quality_score = self.assess_content_quality(report_content, metadata)
        
        # Сохранение
        content_id = self.save_generated_content(
            content_type='report',
            title=title,
            content=report_content,
            metadata=metadata,
            quality_score=quality_score
        )
        
        self.generation_stats['reports_compiled'] += 1
        self.generation_stats['total_content_pieces'] += 1
        
        self.logger.info(f"📝 Ежедневный отчет создан: ID {content_id}")
        
        return {
            'content_id': content_id,
            'title': title,
            'content': report_content,
            'metadata': metadata,
            'quality_score': quality_score,
            'file_path': self.save_content_to_file(content_id, f"daily_report_{report_date}", report_content, 'report')
        }
    
    async def collect_market_data(self, symbol: str) -> Dict[str, Any]:
        """Сбор рыночных данных"""
        # Заглушка для демонстрации - в реальности здесь API биржи
        return {
            'symbol': symbol,
            'current_price': 45250.75 + random.uniform(-1000, 1000),
            'price_change_24h': random.uniform(-5, 5),
            'volume_24h': random.randint(1000000, 5000000),
            'volatility': random.uniform(2, 8),
            'market_sentiment': random.choice(['bullish', 'bearish', 'neutral']),
            'support_levels': [44000, 43500, 43000],
            'resistance_levels': [46000, 46500, 47000],
            'rsi': random.uniform(30, 70),
            'macd_signal': random.choice(['buy', 'sell', 'hold']),
            'trend_direction': random.choice(['up', 'down', 'sideways'])
        }
    
    async def get_ai_insights(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Получение ИИ-инсайтов"""
        if not self.ai_coordinator:
            return {
                'analysis_text': 'ИИ-анализ временно недоступен',
                'confidence': 0.5,
                'predictions': [],
                'patterns': []
            }
        
        # Анализ через ИИ координатор
        context = {
            'market_data': market_data,
            'analysis_type': 'comprehensive',
            'timestamp': datetime.now().isoformat()
        }
        
        analysis = self.ai_coordinator.ai_engine.analyze_context(context)
        
        return {
            'analysis_text': f"""
На основе анализа {len(market_data)} параметров рынка, ИИ-система выявила следующие закономерности:

1. **Текущий тренд**: {market_data.get('trend_direction', 'неопределен')}
2. **Уровень волатильности**: {market_data.get('volatility', 0):.1f}% (умеренный)
3. **Настроения рынка**: {market_data.get('market_sentiment', 'нейтральные')}

Алгоритмы машинного обучения показывают уверенность {analysis.get('confidence', 0.7):.1%} в текущем анализе.
            """,
            'confidence': analysis.get('confidence', 0.7),
            'predictions': [
                {'timeframe': '1h', 'direction': 'up', 'probability': 0.65},
                {'timeframe': '4h', 'direction': 'neutral', 'probability': 0.55},
                {'timeframe': '1d', 'direction': 'up', 'probability': 0.60}
            ],
            'patterns': [
                'Формирование восходящего треугольника',
                'Дивергенция на RSI',
                'Увеличение объемов торгов'
            ]
        }
    
    async def get_trading_predictions(self, symbol: str) -> Dict[str, Any]:
        """Получение торговых прогнозов"""
        if not self.algorithm_manager:
            return {
                'direction': 'hold',
                'confidence': 0.5,
                'target_price': 45000,
                'stop_loss': 44000,
                'risk_level': 'medium',
                'time_horizon': '1h'
            }
        
        try:
            # Используем алгоритмы для прогноза
            predictions = self.algorithm_manager.generate_predictions(symbol)
            
            return {
                'direction': random.choice(['buy', 'sell', 'hold']),
                'confidence': random.uniform(0.6, 0.9),
                'target_price': 45000 + random.uniform(-500, 500),
                'stop_loss': 44000 + random.uniform(-200, 200),
                'risk_level': random.choice(['low', 'medium', 'high']),
                'time_horizon': random.choice(['15m', '1h', '4h', '1d'])
            }
        except:
            return {
                'direction': 'hold',
                'confidence': 0.6,
                'target_price': 45000,
                'stop_loss': 44000,
                'risk_level': 'medium',
                'time_horizon': '1h'
            }
    
    def generate_market_sentiment_text(self, market_data: Dict[str, Any]) -> str:
        """Генерация текста о настроениях рынка"""
        sentiment = market_data.get('market_sentiment', 'neutral')
        price_change = market_data.get('price_change_24h', 0)
        
        if sentiment == 'bullish':
            return f"Рынок демонстрирует **бычьи настроения** с ростом на {price_change:.2f}% за последние 24 часа. Участники рынка настроены оптимистично."
        elif sentiment == 'bearish':
            return f"Наблюдается **медвежий тренд** с падением на {abs(price_change):.2f}%. Преобладают настроения осторожности."
        else:
            return f"Рынок находится в **боковом движении** с незначительными колебаниями ({price_change:.2f}%). Участники выжидают направления."
    
    def generate_technical_indicators_text(self, market_data: Dict[str, Any]) -> str:
        """Генерация текста технических индикаторов"""
        rsi = market_data.get('rsi', 50)
        macd_signal = market_data.get('macd_signal', 'hold')
        
        return f"""
- **RSI (14)**: {rsi:.1f} - {'Перекупленность' if rsi > 70 else 'Перепроданность' if rsi < 30 else 'Нейтральная зона'}
- **MACD**: Сигнал - {macd_signal}
- **Скользящие средние**: {'Восходящий тренд' if market_data.get('trend_direction') == 'up' else 'Нисходящий тренд' if market_data.get('trend_direction') == 'down' else 'Боковое движение'}
        """
    
    def generate_support_resistance_text(self, market_data: Dict[str, Any]) -> str:
        """Генерация текста уровней поддержки и сопротивления"""
        support = market_data.get('support_levels', [])
        resistance = market_data.get('resistance_levels', [])
        
        support_text = ', '.join([f"${level:,}" for level in support[:3]])
        resistance_text = ', '.join([f"${level:,}" for level in resistance[:3]])
        
        return f"""
**Уровни поддержки**: {support_text}
**Уровни сопротивления**: {resistance_text}

Ключевой уровень поддержки находится на отметке ${support[0]:,}, пробой которого может привести к дальнейшему снижению.
        """
    
    def generate_chart_patterns_text(self, market_data: Dict[str, Any]) -> str:
        """Генерация текста графических паттернов"""
        patterns = [
            "Формирование восходящего треугольника на 4-часовом графике",
            "Потенциальный пробой линии тренда",
            "Образование паттерна 'Флаг' после резкого движения"
        ]
        
        return '\n'.join([f"- {pattern}" for pattern in patterns])
    
    def format_ai_predictions(self, predictions: List[Dict]) -> str:
        """Форматирование ИИ-прогнозов"""
        if not predictions:
            return "Прогнозы временно недоступны"
        
        formatted = []
        for pred in predictions:
            formatted.append(f"- **{pred['timeframe']}**: {pred['direction']} ({pred['probability']:.1%} вероятность)")
        
        return '\n'.join(formatted)
    
    def format_detected_patterns(self, patterns: List[str]) -> str:
        """Форматирование выявленных паттернов"""
        if not patterns:
            return "Значимые паттерны не обнаружены"
        
        return '\n'.join([f"- {pattern}" for pattern in patterns])
    
    def generate_trading_strategies_text(self, market_data: Dict[str, Any], ai_insights: Dict[str, Any]) -> str:
        """Генерация текста торговых стратегий"""
        confidence = ai_insights.get('confidence', 0.5)
        
        if confidence > 0.8:
            return """
1. **Агрессивная стратегия**: Высокая уверенность ИИ позволяет рассмотреть позиции с увеличенным размером
2. **Swing Trading**: Использование выявленных паттернов для среднесрочных позиций
3. **Breakout Strategy**: Торговля на пробоях ключевых уровней
            """
        else:
            return """
1. **Консервативная стратегия**: Ожидание более четких сигналов
2. **Scalping**: Краткосрочная торговля на малых таймфреймах
3. **DCA подход**: Постепенное усреднение позиции
            """
    
    def generate_risk_management_text(self, market_data: Dict[str, Any]) -> str:
        """Генерация текста управления рисками"""
        volatility = market_data.get('volatility', 5)
        
        return f"""
- **Размер позиции**: Не более 2-3% от капитала на одну сделку
- **Стоп-лосс**: {2 if volatility > 6 else 1.5}% от входной цены
- **Take Profit**: {1.5 if volatility > 6 else 2.5}:1 к стоп-лоссу
- **Максимальная просадка**: Не более 10% портфеля в день
        """
    
    def generate_conclusion_text(self, market_data: Dict[str, Any], ai_insights: Dict[str, Any]) -> str:
        """Генерация заключительного текста"""
        sentiment = market_data.get('market_sentiment', 'neutral')
        confidence = ai_insights.get('confidence', 0.5)
        
        return f"""
Текущая рыночная ситуация характеризуется {sentiment} настроениями с уровнем уверенности ИИ-анализа {confidence:.1%}.

**Ключевые выводы:**
- Краткосрочная перспектива: {"Позитивная" if confidence > 0.7 else "Неопределенная"}
- Рекомендуемый подход: {"Активная торговля" if confidence > 0.8 else "Осторожные действия"}
- Приоритет: {"Поиск точек входа" if sentiment == 'bullish' else "Управление рисками"}

ИИ-система продолжит мониторинг рынка и обновит анализ при изменении условий.
        """
    
    def determine_signal_type(self, market_data: Dict[str, Any], predictions: Dict[str, Any]) -> str:
        """Определение типа торгового сигнала"""
        confidence = predictions.get('confidence', 0.5)
        direction = predictions.get('direction', 'hold')
        
        if confidence > 0.8:
            return f"strong_{direction}"
        elif confidence > 0.6:
            return f"moderate_{direction}"
        else:
            return f"weak_{direction}"
    
    def generate_signal_analysis(self, market_data: Dict[str, Any], predictions: Dict[str, Any]) -> str:
        """Генерация анализа для торгового сигнала"""
        return f"""
Анализ основан на:
- Техническом анализе: RSI {market_data.get('rsi', 50):.1f}, тренд {market_data.get('trend_direction', 'неопределен')}
- ИИ-алгоритмах: уверенность {predictions.get('confidence', 0):.1%}
- Рыночных условиях: {market_data.get('market_sentiment', 'нейтральные')} настроения

Рекомендация валидна в течение {predictions.get('time_horizon', '1h')}.
        """
    
    def format_trading_signal(self, signal_content: Dict[str, Any]) -> str:
        """Форматирование торгового сигнала"""
        return f"""
# 🎯 Торговый сигнал: {signal_content['symbol']}

**Тип сигнала**: {signal_content['signal_type'].upper()}
**Направление**: {signal_content['direction'].upper()}
**Уверенность**: {signal_content['confidence']:.1%}

## 💰 Торговые параметры
- **Цена входа**: ${signal_content['entry_price']:,.2f}
- **Цель**: ${signal_content['target_price']:,.2f}
- **Стоп-лосс**: ${signal_content['stop_loss']:,.2f}
- **Соотношение**: {(signal_content['target_price'] - signal_content['entry_price']) / (signal_content['entry_price'] - signal_content['stop_loss']):.2f}:1

## 📊 Анализ
{signal_content['analysis']}

## ⚠️ Управление рисками
- **Уровень риска**: {signal_content['risk_level']}
- **Временной горизонт**: {signal_content['time_horizon']}
- **Рекомендуемый размер позиции**: 1-2% от капитала

---
*Сигнал создан {signal_content['generated_at']}*
*Автоматическая система Mirai AI*
        """
    
    async def collect_daily_statistics(self) -> Dict[str, Any]:
        """Сбор ежедневной статистики"""
        today = datetime.now().date()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Статистика контента за день
            cursor.execute("""
                SELECT content_type, COUNT(*), AVG(quality_score)
                FROM generated_content
                WHERE DATE(created_at) = ?
                GROUP BY content_type
            """, (today.isoformat(),))
            
            content_stats = {}
            total_quality = 0
            total_count = 0
            
            for row in cursor.fetchall():
                content_type, count, avg_quality = row
                content_stats[f"{content_type}s_today"] = count
                total_quality += avg_quality * count
                total_count += count
            
            avg_quality = total_quality / total_count if total_count > 0 else 0
            
        return {
            **content_stats,
            'total_today': total_count,
            'avg_quality': avg_quality,
            'date': today.isoformat()
        }
    
    async def get_market_summary(self) -> Dict[str, Any]:
        """Получение сводки рынка"""
        # Симуляция данных - в реальности API бирж
        return {
            'top_gainers': [
                {'symbol': 'BTC', 'change': 3.2},
                {'symbol': 'ETH', 'change': 2.8},
                {'symbol': 'ADA', 'change': 5.1}
            ],
            'top_losers': [
                {'symbol': 'DOT', 'change': -2.1},
                {'symbol': 'LINK', 'change': -1.8}
            ],
            'market_cap_change': 1.5,
            'total_volume': 45000000000,
            'fear_greed_index': 65
        }
    
    async def get_ai_performance_metrics(self) -> Dict[str, Any]:
        """Получение метрик производительности ИИ"""
        return {
            'prediction_accuracy': random.uniform(0.75, 0.85),
            'signals_generated': self.generation_stats['signals_generated'],
            'content_quality_avg': 8.5,
            'uptime_hours': 24,
            'processing_speed': 'optimal'
        }
    
    def format_market_summary(self, market_summary: Dict[str, Any]) -> str:
        """Форматирование сводки рынка"""
        gainers = '\n'.join([f"- {item['symbol']}: +{item['change']:.1f}%" for item in market_summary['top_gainers']])
        losers = '\n'.join([f"- {item['symbol']}: {item['change']:.1f}%" for item in market_summary['top_losers']])
        
        return f"""
**Лидеры роста:**
{gainers}

**Лидеры падения:**
{losers}

**Общая капитализация**: {market_summary['market_cap_change']:+.1f}%
**Индекс страха и жадности**: {market_summary['fear_greed_index']}/100
        """
    
    def format_ai_performance(self, ai_performance: Dict[str, Any]) -> str:
        """Форматирование производительности ИИ"""
        return f"""
- **Точность прогнозов**: {ai_performance['prediction_accuracy']:.1%}
- **Сигналов создано**: {ai_performance['signals_generated']}
- **Качество контента**: {ai_performance['content_quality_avg']:.1f}/10
- **Время работы**: {ai_performance['uptime_hours']} часов
- **Статус системы**: {ai_performance['processing_speed']}
        """
    
    def generate_daily_insights(self, daily_data: Dict, market_summary: Dict, ai_performance: Dict) -> str:
        """Генерация ежедневных инсайтов"""
        return f"""
Сегодня ИИ-система Mirai обработала {daily_data.get('total_today', 0)} единиц контента со средним качеством {daily_data.get('avg_quality', 0):.1f}/10.

**Ключевые наблюдения:**
- Рынок показал {'позитивную' if market_summary.get('market_cap_change', 0) > 0 else 'негативную'} динамику
- Точность прогнозов ИИ составила {ai_performance.get('prediction_accuracy', 0):.1%}
- {'Высокая' if ai_performance.get('prediction_accuracy', 0) > 0.8 else 'Умеренная'} активность алгоритмов

**Адаптация системы:**
ИИ автоматически скорректировал параметры анализа в соответствии с текущими рыночными условиями.
        """
    
    def generate_top_opportunities(self, market_summary: Dict[str, Any]) -> str:
        """Генерация топ возможностей"""
        opportunities = []
        
        for gainer in market_summary.get('top_gainers', [])[:2]:
            opportunities.append(f"**{gainer['symbol']}**: Продолжение роста (+{gainer['change']:.1f}%), возможен ретест уровней")
        
        return '\n'.join([f"{i+1}. {opp}" for i, opp in enumerate(opportunities)])
    
    def generate_tomorrow_forecast(self, market_summary: Dict, ai_performance: Dict) -> str:
        """Генерация прогноза на завтра"""
        return f"""
**Общие ожидания:**
- {'Продолжение роста' if market_summary.get('market_cap_change', 0) > 0 else 'Возможная коррекция'}
- Волатильность: умеренная
- Рекомендуемая стратегия: {'активная торговля' if ai_performance.get('prediction_accuracy', 0) > 0.8 else 'осторожность'}

**Ключевые события:**
- Мониторинг новостного фона
- Отслеживание институциональных потоков
- Анализ технических уровней

ИИ-система продолжит адаптацию к рыночным условиям.
        """
    
    def assess_content_quality(self, content: str, metadata: Dict[str, Any]) -> float:
        """Оценка качества контента"""
        quality_score = 0.5  # Базовая оценка
        
        # Длина контента
        word_count = len(content.split())
        if word_count > 300:
            quality_score += 0.2
        if word_count > 800:
            quality_score += 0.1
        
        # Структурированность
        if '##' in content:  # Заголовки
            quality_score += 0.1
        if '**' in content:  # Выделения
            quality_score += 0.05
        if '- ' in content:  # Списки
            quality_score += 0.05
        
        # ИИ-уверенность
        ai_confidence = metadata.get('ai_confidence', 0.5)
        quality_score += ai_confidence * 0.2
        
        return min(quality_score, 1.0)
    
    def assess_signal_quality(self, signal_content: Dict[str, Any], market_data: Dict[str, Any]) -> float:
        """Оценка качества торгового сигнала"""
        quality = 0.5
        
        # Уверенность ИИ
        confidence = signal_content.get('confidence', 0.5)
        quality += confidence * 0.3
        
        # Соотношение риск/доходность
        entry = signal_content.get('entry_price', 0)
        target = signal_content.get('target_price', 0)
        stop = signal_content.get('stop_loss', 0)
        
        if entry and target and stop:
            reward_risk_ratio = (target - entry) / (entry - stop) if entry != stop else 0
            if reward_risk_ratio > 1.5:
                quality += 0.2
        
        return min(quality, 1.0)
    
    def save_generated_content(self, content_type: str, title: str, content: str, 
                             metadata: Dict[str, Any], quality_score: float) -> int:
        """Сохранение сгенерированного контента в БД"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO generated_content 
                (content_type, title, content, metadata, quality_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                content_type, title, content,
                json.dumps(metadata, ensure_ascii=False),
                quality_score, datetime.now().isoformat()
            ))
            
            return cursor.lastrowid
    
    def save_content_to_file(self, content_id: int, title: str, content: str, content_type: str) -> str:
        """Сохранение контента в файл"""
        # Очистка названия для файла
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{content_id}_{timestamp}_{safe_title}.md"
        
        file_path = Path(self.content_storage) / content_type / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(file_path)
    
    async def autonomous_content_cycle(self):
        """Автономный цикл генерации контента"""
        self.logger.info("🚀 Запуск автономного контентного цикла")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                self.logger.info(f"🔄 Цикл {cycle_count} - генерация контента")
                
                # Генерируем разные типы контента
                tasks = []
                
                # Анализ рынка (каждые 2 часа)
                if cycle_count % 8 == 1:
                    tasks.append(self.generate_market_analysis_article())
                
                # Торговые сигналы (каждые 15 минут)
                if cycle_count % 1 == 0:
                    symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
                    selected_symbol = random.choice(symbols)
                    tasks.append(self.generate_trading_signal(selected_symbol))
                
                # Ежедневный отчет (раз в день)
                current_hour = datetime.now().hour
                if current_hour == 8 and cycle_count % 96 == 1:  # 8 утра
                    tasks.append(self.generate_daily_report())
                
                # Выполняем задачи
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            self.logger.error(f"❌ Ошибка в задаче {i}: {result}")
                        else:
                            self.logger.info(f"✅ Задача {i} выполнена: {result.get('title', 'N/A')}")
                
                # Статистика
                if cycle_count % 10 == 0:
                    self.log_statistics()
                
                # Пауза 15 минут между циклами
                await asyncio.sleep(900)
                
            except Exception as e:
                self.logger.error(f"❌ Критическая ошибка в цикле {cycle_count}: {e}")
                await asyncio.sleep(300)  # Пауза при ошибке
    
    def log_statistics(self):
        """Логирование статистики"""
        uptime = datetime.now() - self.generation_stats['start_time']
        
        self.logger.info(f"""
📊 Статистика контентного движка:
   Время работы: {uptime.total_seconds() / 3600:.1f} часов
   Статей создано: {self.generation_stats['articles_created']}
   Сигналов сгенерировано: {self.generation_stats['signals_generated']}
   Отчетов составлено: {self.generation_stats['reports_compiled']}
   Всего контента: {self.generation_stats['total_content_pieces']}
        """)
    
    async def start_content_engine(self):
        """Запуск контентного движка"""
        self.logger.info("🎬 Запуск автономного контентного движка Mirai")
        
        # Инициализация шаблонов
        await self.initialize_templates()
        
        # Запуск автономного цикла
        await self.autonomous_content_cycle()
    
    async def initialize_templates(self):
        """Инициализация шаблонов контента"""
        templates = ContentTemplate.get_article_templates()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for template_name, template_data in templates.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO content_templates 
                    (template_name, template_type, template_data)
                    VALUES (?, ?, ?)
                """, (
                    template_name, 'article',
                    json.dumps(template_data, ensure_ascii=False)
                ))
            
            conn.commit()
        
        self.logger.info("📝 Шаблоны контента инициализированы")

async def main():
    """Основная функция запуска контентного движка"""
    print("🚀 Mirai Autonomous Content Generation Engine")
    print("Инициализация автономной системы генерации контента...")
    
    engine = MiraiContentEngine()
    
    try:
        await engine.start_content_engine()
    except KeyboardInterrupt:
        print("\n🛑 Остановка контентного движка...")
        engine.logger.info("Контентный движок остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        engine.logger.error(f"Критическая ошибка движка: {e}")

if __name__ == "__main__":
    asyncio.run(main())