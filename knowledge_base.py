#!/usr/bin/env python3
"""
Mirai Knowledge Base
Система накопления и управления знаниями для непрерывного обучения агента
"""

import asyncio
import json
import sqlite3
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict, Counter
import hashlib
import pickle
import gzip
import threading
from concurrent.futures import ThreadPoolExecutor
import aiofiles
import re

@dataclass
class KnowledgeEntry:
    """Запись в базе знаний"""
    id: str
    topic: str
    content: Dict[str, Any]
    category: str
    confidence: float
    source: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    relevance_score: float = 1.0

@dataclass
class LearningEvent:
    """Событие обучения"""
    event_id: str
    event_type: str
    data: Dict[str, Any]
    outcome: str
    success_metrics: Dict[str, float]
    timestamp: datetime
    context: Dict[str, Any]

class KnowledgeGraph:
    """Граф знаний для связи концепций"""
    
    def __init__(self):
        self.nodes = {}  # topic -> node_data
        self.edges = defaultdict(list)  # topic -> [related_topics]
        self.weights = {}  # (topic1, topic2) -> weight
        
    def add_node(self, topic: str, data: Dict[str, Any]):
        """Добавление узла в граф"""
        self.nodes[topic] = data
        
    def add_edge(self, topic1: str, topic2: str, weight: float = 1.0):
        """Добавление связи между темами"""
        if topic1 not in self.edges[topic2]:
            self.edges[topic1].append(topic2)
        if topic2 not in self.edges[topic1]:
            self.edges[topic2].append(topic1)
        
        self.weights[(topic1, topic2)] = weight
        self.weights[(topic2, topic1)] = weight
        
    def get_related_topics(self, topic: str, max_depth: int = 2, min_weight: float = 0.3) -> List[Tuple[str, float]]:
        """Получение связанных тем"""
        if topic not in self.nodes:
            return []
        
        related = []
        visited = set()
        queue = [(topic, 0, 1.0)]  # (topic, depth, weight)
        
        while queue:
            current_topic, depth, current_weight = queue.pop(0)
            
            if current_topic in visited or depth > max_depth:
                continue
                
            visited.add(current_topic)
            
            if current_topic != topic and current_weight >= min_weight:
                related.append((current_topic, current_weight))
            
            if depth < max_depth:
                for neighbor in self.edges.get(current_topic, []):
                    if neighbor not in visited:
                        edge_weight = self.weights.get((current_topic, neighbor), 0.5)
                        new_weight = current_weight * edge_weight
                        queue.append((neighbor, depth + 1, new_weight))
        
        return sorted(related, key=lambda x: x[1], reverse=True)

class SemanticAnalyzer:
    """Семантический анализатор для обработки текста"""
    
    def __init__(self):
        self.word_frequencies = defaultdict(int)
        self.topic_keywords = defaultdict(set)
        
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Извлечение ключевых слов из текста"""
        if not text:
            return []
        
        # Простой алгоритм извлечения ключевых слов
        words = re.findall(r'\b[a-zA-Zа-яА-Я]{3,}\b', text.lower())
        
        # Фильтруем стоп-слова
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'это', 'для', 'как', 'что', 'или', 'при', 'его', 'она', 'они', 'все', 'был', 'быть'
        }
        
        words = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Подсчет частоты
        word_count = Counter(words)
        
        # Возвращаем наиболее частые слова
        return [word for word, count in word_count.most_common(max_keywords)]
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Расчет семантической похожести текстов"""
        keywords1 = set(self.extract_keywords(text1))
        keywords2 = set(self.extract_keywords(text2))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = keywords1.intersection(keywords2)
        union = keywords1.union(keywords2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def categorize_content(self, content: str) -> str:
        """Автоматическая категоризация контента"""
        keywords = self.extract_keywords(content, 20)
        
        # Простая система категоризации
        categories = {
            'trading': ['trade', 'price', 'market', 'strategy', 'profit', 'loss', 'order', 'position'],
            'technical': ['algorithm', 'code', 'function', 'class', 'method', 'implementation', 'system'],
            'analytics': ['data', 'analysis', 'metric', 'performance', 'statistics', 'trend', 'pattern'],
            'ai_ml': ['model', 'learning', 'prediction', 'neural', 'training', 'accuracy', 'intelligence'],
            'system': ['server', 'database', 'api', 'service', 'configuration', 'deployment', 'monitoring'],
            'business': ['revenue', 'cost', 'investment', 'risk', 'management', 'decision', 'strategy']
        }
        
        scores = {}
        for category, category_keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in category_keywords)
            scores[category] = score
        
        if not scores or max(scores.values()) == 0:
            return 'general'
        
        return max(scores, key=scores.get)

class MiraiKnowledgeBase:
    """Основная система базы знаний Mirai"""
    
    def __init__(self, db_path: str = '/root/mirai-agent/state/knowledge_base.db'):
        self.db_path = db_path
        self.knowledge_graph = KnowledgeGraph()
        self.semantic_analyzer = SemanticAnalyzer()
        self.logger = self.setup_logging()
        self.cache = {}
        self.max_cache_size = 1000
        
        # Инициализация
        self.init_database()
        self.load_knowledge_graph()
        
        # Статистика
        self.stats = {
            'total_entries': 0,
            'categories': defaultdict(int),
            'daily_additions': defaultdict(int),
            'access_patterns': defaultdict(int)
        }
        
        self.update_statistics()
    
    def setup_logging(self):
        """Настройка логирования"""
        logger = logging.getLogger('MiraiKnowledgeBase')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler('/root/mirai-agent/logs/knowledge_base.log')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def init_database(self):
        """Инициализация базы данных знаний"""
        Path(self.db_path).parent.mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Основная таблица знаний
            conn.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_entries (
                    id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    source TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    relevance_score REAL DEFAULT 1.0
                )
            ''')
            
            # Таблица связей между знаниями
            conn.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic1 TEXT NOT NULL,
                    topic2 TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    created_at TEXT NOT NULL
                )
            ''')
            
            # Таблица событий обучения
            conn.execute('''
                CREATE TABLE IF NOT EXISTS learning_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    success_metrics TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    context TEXT NOT NULL
                )
            ''')
            
            # Таблица запросов и поиска
            conn.execute('''
                CREATE TABLE IF NOT EXISTS search_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    results_count INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_feedback TEXT
                )
            ''')
            
            # Индексы для оптимизации
            conn.execute('CREATE INDEX IF NOT EXISTS idx_topic ON knowledge_entries(topic)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_category ON knowledge_entries(category)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON knowledge_entries(created_at)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_relevance ON knowledge_entries(relevance_score)')
            
            conn.commit()
    
    def generate_entry_id(self, topic: str, content: Dict[str, Any]) -> str:
        """Генерация уникального ID записи"""
        content_str = json.dumps(content, sort_keys=True)
        hash_input = f"{topic}:{content_str}".encode()
        return hashlib.sha256(hash_input).hexdigest()[:16]
    
    async def add_knowledge(self, topic: str, content: Dict[str, Any], 
                          category: str = None, confidence: float = 0.8,
                          source: str = 'system', tags: List[str] = None) -> str:
        """Добавление знания в базу"""
        try:
            # Автоматическая категоризация если не указана
            if not category:
                content_text = json.dumps(content)
                category = self.semantic_analyzer.categorize_content(content_text)
            
            # Извлечение тегов если не указаны
            if not tags:
                content_text = json.dumps(content)
                tags = self.semantic_analyzer.extract_keywords(content_text)
            
            entry_id = self.generate_entry_id(topic, content)
            current_time = datetime.now()
            
            entry = KnowledgeEntry(
                id=entry_id,
                topic=topic,
                content=content,
                category=category,
                confidence=confidence,
                source=source,
                tags=tags,
                created_at=current_time,
                updated_at=current_time
            )
            
            # Сохранение в базу данных
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO knowledge_entries 
                    (id, topic, content, category, confidence, source, tags, 
                     created_at, updated_at, access_count, relevance_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry.id,
                    entry.topic,
                    json.dumps(entry.content, default=str),  # Исправлено для datetime
                    entry.category,
                    entry.confidence,
                    entry.source,
                    json.dumps(entry.tags),
                    entry.created_at.isoformat(),
                    entry.updated_at.isoformat(),
                    entry.access_count,
                    entry.relevance_score
                ))
                conn.commit()
            
            # Добавление в граф знаний
            self.knowledge_graph.add_node(topic, {
                'category': category,
                'confidence': confidence,
                'tags': tags
            })
            
            # Поиск связанных тем
            await self.find_and_create_relations(entry)
            
            # Обновление статистики
            self.stats['total_entries'] += 1
            self.stats['categories'][category] += 1
            today = datetime.now().date().isoformat()
            self.stats['daily_additions'][today] += 1
            
            # Очистка кеша
            self.cache.clear()
            
            self.logger.info(f"✅ Добавлено знание: {topic} (категория: {category})")
            return entry_id
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления знания: {e}")
            return ""
    
    async def find_and_create_relations(self, entry: KnowledgeEntry):
        """Поиск и создание связей между знаниями"""
        try:
            # Получение похожих записей
            similar_entries = await self.search_knowledge(
                entry.topic, 
                max_results=10,
                min_confidence=0.6
            )
            
            for similar_entry in similar_entries:
                if similar_entry.id != entry.id:
                    # Расчет семантической близости
                    similarity = self.semantic_analyzer.calculate_similarity(
                        json.dumps(entry.content),
                        json.dumps(similar_entry.content)
                    )
                    
                    if similarity > 0.3:
                        # Создание связи
                        await self.create_relation(
                            entry.topic,
                            similar_entry.topic,
                            'semantic_similarity',
                            similarity
                        )
            
        except Exception as e:
            self.logger.error(f"Ошибка создания связей: {e}")
    
    async def create_relation(self, topic1: str, topic2: str, 
                            relation_type: str, weight: float = 1.0):
        """Создание связи между темами"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO knowledge_relations
                    (topic1, topic2, relation_type, weight, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    topic1,
                    topic2,
                    relation_type,
                    weight,
                    datetime.now().isoformat()
                ))
                conn.commit()
            
            # Обновление графа знаний
            self.knowledge_graph.add_edge(topic1, topic2, weight)
            
        except Exception as e:
            self.logger.error(f"Ошибка создания связи: {e}")
    
    async def search_knowledge(self, query: str, category: str = None,
                             max_results: int = 10, min_confidence: float = 0.5) -> List[KnowledgeEntry]:
        """Поиск знаний"""
        try:
            # Проверка кеша
            cache_key = f"{query}:{category}:{max_results}:{min_confidence}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            results = []
            
            with sqlite3.connect(self.db_path) as conn:
                # Базовый запрос
                sql = '''
                    SELECT id, topic, content, category, confidence, source, tags,
                           created_at, updated_at, access_count, relevance_score
                    FROM knowledge_entries
                    WHERE confidence >= ?
                '''
                params = [min_confidence]
                
                # Фильтр по категории
                if category:
                    sql += ' AND category = ?'
                    params.append(category)
                
                # Поиск по теме и содержимому
                if query:
                    sql += ' AND (topic LIKE ? OR content LIKE ?)'
                    query_pattern = f'%{query}%'
                    params.extend([query_pattern, query_pattern])
                
                sql += ' ORDER BY relevance_score DESC, confidence DESC LIMIT ?'
                params.append(max_results)
                
                cursor = conn.execute(sql, params)
                
                for row in cursor.fetchall():
                    entry = KnowledgeEntry(
                        id=row[0],
                        topic=row[1],
                        content=json.loads(row[2]),
                        category=row[3],
                        confidence=row[4],
                        source=row[5],
                        tags=json.loads(row[6]),
                        created_at=datetime.fromisoformat(row[7]),
                        updated_at=datetime.fromisoformat(row[8]),
                        access_count=row[9],
                        relevance_score=row[10]
                    )
                    results.append(entry)
            
            # Семантическое ранжирование если есть запрос
            if query and results:
                scored_results = []
                for entry in results:
                    content_text = f"{entry.topic} {json.dumps(entry.content)}"
                    similarity = self.semantic_analyzer.calculate_similarity(query, content_text)
                    scored_results.append((entry, similarity))
                
                # Сортировка по семантической близости
                scored_results.sort(key=lambda x: x[1], reverse=True)
                results = [entry for entry, score in scored_results]
            
            # Обновление счетчиков доступа
            await self.update_access_counts([entry.id for entry in results])
            
            # Кеширование результатов
            if len(self.cache) < self.max_cache_size:
                self.cache[cache_key] = results
            
            # Логирование запроса
            await self.log_search_query(query, len(results))
            
            return results
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска знаний: {e}")
            return []
    
    async def update_access_counts(self, entry_ids: List[str]):
        """Обновление счетчиков доступа"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for entry_id in entry_ids:
                    conn.execute(
                        'UPDATE knowledge_entries SET access_count = access_count + 1 WHERE id = ?',
                        (entry_id,)
                    )
                conn.commit()
        except Exception as e:
            self.logger.error(f"Ошибка обновления счетчиков: {e}")
    
    async def log_search_query(self, query: str, results_count: int):
        """Логирование поискового запроса"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO search_queries (query, results_count, timestamp)
                    VALUES (?, ?, ?)
                ''', (query, results_count, datetime.now().isoformat()))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Ошибка логирования запроса: {e}")
    
    async def get_knowledge_by_topic(self, topic: str) -> Optional[KnowledgeEntry]:
        """Получение знания по теме"""
        results = await self.search_knowledge(topic, max_results=1)
        return results[0] if results else None
    
    async def update_knowledge(self, entry_id: str, content: Dict[str, Any] = None,
                             confidence: float = None, tags: List[str] = None) -> bool:
        """Обновление существующего знания"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Получение текущей записи
                cursor = conn.execute('SELECT * FROM knowledge_entries WHERE id = ?', (entry_id,))
                row = cursor.fetchone()
                
                if not row:
                    return False
                
                # Подготовка обновлений
                updates = []
                params = []
                
                if content is not None:
                    updates.append('content = ?')
                    params.append(json.dumps(content))
                
                if confidence is not None:
                    updates.append('confidence = ?')
                    params.append(confidence)
                
                if tags is not None:
                    updates.append('tags = ?')
                    params.append(json.dumps(tags))
                
                updates.append('updated_at = ?')
                params.append(datetime.now().isoformat())
                
                params.append(entry_id)
                
                # Выполнение обновления
                sql = f"UPDATE knowledge_entries SET {', '.join(updates)} WHERE id = ?"
                conn.execute(sql, params)
                conn.commit()
                
                # Очистка кеша
                self.cache.clear()
                
                self.logger.info(f"✅ Обновлено знание: {entry_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления знания: {e}")
            return False
    
    async def delete_knowledge(self, entry_id: str) -> bool:
        """Удаление знания"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('DELETE FROM knowledge_entries WHERE id = ?', (entry_id,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    # Удаление связей
                    conn.execute('''
                        DELETE FROM knowledge_relations 
                        WHERE topic1 IN (SELECT topic FROM knowledge_entries WHERE id = ?)
                        OR topic2 IN (SELECT topic FROM knowledge_entries WHERE id = ?)
                    ''', (entry_id, entry_id))
                    conn.commit()
                    
                    # Очистка кеша
                    self.cache.clear()
                    
                    self.logger.info(f"🗑️ Удалено знание: {entry_id}")
                    return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка удаления знания: {e}")
            return False
    
    def load_knowledge_graph(self):
        """Загрузка графа знаний из базы данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Загрузка узлов
                cursor = conn.execute('SELECT topic, category, confidence, tags FROM knowledge_entries')
                for topic, category, confidence, tags in cursor.fetchall():
                    self.knowledge_graph.add_node(topic, {
                        'category': category,
                        'confidence': confidence,
                        'tags': json.loads(tags)
                    })
                
                # Загрузка рёбер
                cursor = conn.execute('SELECT topic1, topic2, weight FROM knowledge_relations')
                for topic1, topic2, weight in cursor.fetchall():
                    self.knowledge_graph.add_edge(topic1, topic2, weight)
                    
            self.logger.info(f"📊 Загружен граф знаний: {len(self.knowledge_graph.nodes)} узлов, {len(self.knowledge_graph.edges)} рёбер")
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки графа знаний: {e}")
    
    def update_statistics(self):
        """Обновление статистики"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Общее количество записей
                cursor = conn.execute('SELECT COUNT(*) FROM knowledge_entries')
                self.stats['total_entries'] = cursor.fetchone()[0]
                
                # Статистика по категориям
                cursor = conn.execute('SELECT category, COUNT(*) FROM knowledge_entries GROUP BY category')
                self.stats['categories'] = dict(cursor.fetchall())
                
                # Популярные запросы
                cursor = conn.execute('''
                    SELECT query, COUNT(*) as count FROM search_queries 
                    GROUP BY query ORDER BY count DESC LIMIT 10
                ''')
                self.stats['popular_queries'] = dict(cursor.fetchall())
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления статистики: {e}")
    
    async def get_recommendations(self, topic: str, max_recommendations: int = 5) -> List[KnowledgeEntry]:
        """Получение рекомендаций по теме"""
        try:
            # Получение связанных тем из графа
            related_topics = self.knowledge_graph.get_related_topics(topic)
            
            recommendations = []
            for related_topic, weight in related_topics[:max_recommendations]:
                knowledge = await self.get_knowledge_by_topic(related_topic)
                if knowledge:
                    recommendations.append(knowledge)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Ошибка получения рекомендаций: {e}")
            return []
    
    async def export_knowledge(self, filepath: str, category: str = None) -> bool:
        """Экспорт знаний в файл"""
        try:
            results = await self.search_knowledge("", category=category, max_results=10000)
            
            export_data = {
                'export_date': datetime.now().isoformat(),
                'total_entries': len(results),
                'category_filter': category,
                'knowledge_entries': []
            }
            
            for entry in results:
                export_data['knowledge_entries'].append({
                    'topic': entry.topic,
                    'content': entry.content,
                    'category': entry.category,
                    'confidence': entry.confidence,
                    'tags': entry.tags,
                    'created_at': entry.created_at.isoformat(),
                    'access_count': entry.access_count
                })
            
            # Сжатое сохранение
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📄 Экспорт завершен: {filepath} ({len(results)} записей)")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка экспорта: {e}")
            return False
    
    async def import_knowledge(self, filepath: str) -> int:
        """Импорт знаний из файла"""
        try:
            imported_count = 0
            
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                import_data = json.load(f)
            
            for entry_data in import_data.get('knowledge_entries', []):
                await self.add_knowledge(
                    topic=entry_data['topic'],
                    content=entry_data['content'],
                    category=entry_data['category'],
                    confidence=entry_data['confidence'],
                    tags=entry_data['tags']
                )
                imported_count += 1
            
            self.logger.info(f"📥 Импорт завершен: {imported_count} записей")
            return imported_count
            
        except Exception as e:
            self.logger.error(f"Ошибка импорта: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики базы знаний"""
        self.update_statistics()
        return dict(self.stats)

async def demonstrate_knowledge_base():
    """Демонстрация работы базы знаний"""
    kb = MiraiKnowledgeBase()
    
    # Добавление знаний
    await kb.add_knowledge(
        topic="trading_strategy_momentum",
        content={
            "description": "Стратегия торговли на основе моментума",
            "indicators": ["RSI", "MACD", "Moving Averages"],
            "timeframes": ["1h", "4h", "1d"],
            "risk_level": "medium",
            "expected_profit": 0.15,
            "max_drawdown": 0.08
        },
        category="trading",
        tags=["momentum", "strategy", "technical_analysis"]
    )
    
    await kb.add_knowledge(
        topic="ai_model_performance",
        content={
            "model_type": "Random Forest",
            "accuracy": 0.87,
            "precision": 0.82,
            "recall": 0.89,
            "training_data_size": 10000,
            "features_count": 25,
            "optimization_notes": "Grid search для гиперпараметров"
        },
        category="ai_ml",
        tags=["machine_learning", "model", "performance"]
    )
    
    # Поиск знаний
    search_results = await kb.search_knowledge("trading", max_results=5)
    print(f"🔍 Найдено {len(search_results)} результатов по запросу 'trading'")
    
    # Получение рекомендаций
    recommendations = await kb.get_recommendations("trading_strategy_momentum")
    print(f"💡 Рекомендации: {len(recommendations)} связанных тем")
    
    # Статистика
    stats = kb.get_statistics()
    print(f"📊 Статистика: {stats['total_entries']} записей в {len(stats['categories'])} категориях")

if __name__ == "__main__":
    asyncio.run(demonstrate_knowledge_base())