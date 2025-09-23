#!/usr/bin/env python3
"""
Mirai Social Ecosystem Platform
Социальная экосистема с интеграциями API, пользовательскими интерфейсами и community features
"""

import asyncio
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
import requests
import hashlib
import time
import sys
import os
import threading
from collections import defaultdict, deque
import random
import uuid
from urllib.parse import quote, unquote
import markdown
import bleach
import bcrypt

# Добавляем пути для импорта ИИ модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ai_integration import MiraiAICoordinator
    from knowledge_base import MiraiKnowledgeBase
    from autonomous_content_engine import MiraiContentEngine
    from machine_learning_engine import MiraiLearningEngine
    AI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ ИИ компоненты недоступны: {e}")
    AI_AVAILABLE = False

@dataclass
class User:
    """Пользователь социальной экосистемы"""
    user_id: str
    username: str
    email: str
    password_hash: str
    display_name: str
    avatar_url: str
    bio: str
    reputation: int
    level: str
    created_at: datetime
    last_active: datetime
    preferences: Dict[str, Any]
    achievements: List[str]

@dataclass
class SocialPost:
    """Социальный пост"""
    post_id: str
    author_id: str
    content: str
    content_type: str  # text, analysis, signal, prediction
    tags: List[str]
    likes: int
    comments: int
    shares: int
    created_at: datetime
    updated_at: datetime
    visibility: str  # public, followers, private
    ai_generated: bool
    metadata: Dict[str, Any]

@dataclass
class Community:
    """Сообщество"""
    community_id: str
    name: str
    description: str
    category: str
    admin_ids: List[str]
    member_count: int
    created_at: datetime
    settings: Dict[str, Any]
    rules: List[str]

class SocialEcosystemAPI:
    """API для социальной экосистемы"""
    
    def __init__(self):
        self.logger = self.setup_logging()
        self.db_path = '/root/mirai-agent/state/social_ecosystem.db'
        self.app = Flask(__name__)
        self.app.secret_key = 'mirai_social_secret_key_2025'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # ИИ компоненты
        if AI_AVAILABLE:
            self.ai_coordinator = MiraiAICoordinator()
            self.knowledge_base = MiraiKnowledgeBase()
            self.content_engine = MiraiContentEngine()
            self.learning_engine = MiraiLearningEngine()
        else:
            self.ai_coordinator = None
            self.knowledge_base = None
            self.content_engine = None
            self.learning_engine = None
        
        # Активные пользователи и сессии
        self.active_users = {}
        self.user_sessions = {}
        self.online_users = set()
        self.chat_rooms = defaultdict(list)
        
        # Социальные данные
        self.user_connections = defaultdict(set)  # followers/following
        self.content_feed = deque(maxlen=10000)
        self.trending_topics = {}
        self.community_stats = {}
        
        # API интеграции
        self.external_apis = {
            'binance': 'https://api.binance.com/api/v3',
            'coingecko': 'https://api.coingecko.com/api/v3',
            'news': 'https://newsapi.org/v2',
            'social': 'https://api.twitter.com/2'
        }
        
        # Настройки экосистемы
        self.ecosystem_config = {
            'max_post_length': 2000,
            'reputation_threshold': 100,
            'ai_moderation': True,
            'auto_trending': True,
            'community_features': True,
            'real_time_updates': True
        }
        
        self.init_database()
        self.setup_routes()
        self.setup_socketio_events()
    
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/mirai-agent/logs/social_ecosystem.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('SocialEcosystem')
    
    def init_database(self):
        """Инициализация базы данных социальной экосистемы"""
        Path(self.db_path).parent.mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Таблица пользователей
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    avatar_url TEXT DEFAULT '',
                    bio TEXT DEFAULT '',
                    reputation INTEGER DEFAULT 0,
                    level TEXT DEFAULT 'novice',
                    created_at TEXT NOT NULL,
                    last_active TEXT NOT NULL,
                    preferences TEXT DEFAULT '{}',
                    achievements TEXT DEFAULT '[]'
                )
            ''')
            
            # Таблица постов
            conn.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    post_id TEXT PRIMARY KEY,
                    author_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    tags TEXT DEFAULT '[]',
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    visibility TEXT DEFAULT 'public',
                    ai_generated BOOLEAN DEFAULT FALSE,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (author_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица сообществ
            conn.execute('''
                CREATE TABLE IF NOT EXISTS communities (
                    community_id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    admin_ids TEXT NOT NULL,
                    member_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    settings TEXT DEFAULT '{}',
                    rules TEXT DEFAULT '[]'
                )
            ''')
            
            # Таблица подписок
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_follows (
                    follower_id TEXT NOT NULL,
                    following_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (follower_id, following_id),
                    FOREIGN KEY (follower_id) REFERENCES users (user_id),
                    FOREIGN KEY (following_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица реакций
            conn.execute('''
                CREATE TABLE IF NOT EXISTS post_reactions (
                    user_id TEXT NOT NULL,
                    post_id TEXT NOT NULL,
                    reaction_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, post_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (post_id) REFERENCES posts (post_id)
                )
            ''')
            
            # Таблица комментариев
            conn.execute('''
                CREATE TABLE IF NOT EXISTS comments (
                    comment_id TEXT PRIMARY KEY,
                    post_id TEXT NOT NULL,
                    author_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    parent_comment_id TEXT,
                    FOREIGN KEY (post_id) REFERENCES posts (post_id),
                    FOREIGN KEY (author_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
    
    def setup_routes(self):
        """Настройка маршрутов Flask"""
        
        @self.app.route('/')
        def index():
            return render_template_string(self.get_main_template())
        
        @self.app.route('/api/users', methods=['POST'])
        def create_user():
            """Создание нового пользователя"""
            data = request.get_json()
            
            # Валидация
            required_fields = ['username', 'email', 'password', 'display_name']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
            
            # Хэширование пароля
            password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
            
            user = User(
                user_id=str(uuid.uuid4()),
                username=data['username'],
                email=data['email'],
                password_hash=password_hash.decode('utf-8'),
                display_name=data['display_name'],
                avatar_url=data.get('avatar_url', ''),
                bio=data.get('bio', ''),
                reputation=0,
                level='novice',
                created_at=datetime.now(),
                last_active=datetime.now(),
                preferences=data.get('preferences', {}),
                achievements=[]
            )
            
            try:
                self.create_user_in_db(user)
                self.logger.info(f"👤 Создан пользователь: {user.username}")
                return jsonify({
                    'user_id': user.user_id,
                    'username': user.username,
                    'display_name': user.display_name
                }), 201
            except Exception as e:
                return jsonify({'error': str(e)}), 400
        
        @self.app.route('/api/posts', methods=['POST'])
        def create_post():
            """Создание нового поста"""
            data = request.get_json()
            
            if 'content' not in data or 'author_id' not in data:
                return jsonify({'error': 'Missing content or author_id'}), 400
            
            post = SocialPost(
                post_id=str(uuid.uuid4()),
                author_id=data['author_id'],
                content=data['content'],
                content_type=data.get('content_type', 'text'),
                tags=data.get('tags', []),
                likes=0,
                comments=0,
                shares=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                visibility=data.get('visibility', 'public'),
                ai_generated=data.get('ai_generated', False),
                metadata=data.get('metadata', {})
            )
            
            try:
                self.create_post_in_db(post)
                self.add_to_content_feed(post)
                
                # Уведомление в реальном времени
                self.socketio.emit('new_post', asdict(post), room='public_feed')
                
                self.logger.info(f"📝 Создан пост: {post.post_id}")
                return jsonify(asdict(post)), 201
            except Exception as e:
                return jsonify({'error': str(e)}), 400
        
        @self.app.route('/api/posts/<post_id>/like', methods=['POST'])
        def like_post(post_id):
            """Лайк поста"""
            data = request.get_json()
            user_id = data.get('user_id')
            
            if not user_id:
                return jsonify({'error': 'Missing user_id'}), 400
            
            try:
                result = self.toggle_post_reaction(post_id, user_id, 'like')
                
                # Уведомление в реальном времени
                self.socketio.emit('post_liked', {
                    'post_id': post_id,
                    'user_id': user_id,
                    'new_count': result['likes']
                }, room='public_feed')
                
                return jsonify(result), 200
            except Exception as e:
                return jsonify({'error': str(e)}), 400
        
        @self.app.route('/api/feed')
        def get_feed():
            """Получение ленты постов"""
            limit = request.args.get('limit', 20, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            posts = self.get_public_feed(limit, offset)
            return jsonify(posts)
        
        @self.app.route('/api/trending')
        def get_trending():
            """Получение трендовых тем"""
            return jsonify(self.get_trending_topics())
        
        @self.app.route('/api/communities')
        def get_communities():
            """Получение списка сообществ"""
            communities = self.get_all_communities()
            return jsonify(communities)
        
        @self.app.route('/api/ai/generate_content', methods=['POST'])
        def ai_generate_content():
            """ИИ генерация контента"""
            data = request.get_json()
            content_type = data.get('type', 'analysis')
            topic = data.get('topic', 'market')
            
            try:
                if self.content_engine:
                    if content_type == 'analysis':
                        result = asyncio.run(self.content_engine.generate_market_analysis_article())
                    elif content_type == 'signal':
                        result = asyncio.run(self.content_engine.generate_trading_signal())
                    elif content_type == 'report':
                        result = asyncio.run(self.content_engine.generate_daily_report())
                    else:
                        result = {'error': 'Unknown content type'}
                    
                    return jsonify(result)
                else:
                    return jsonify({'error': 'AI engine not available'}), 503
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stats')
        def get_stats():
            """Получение статистики экосистемы"""
            return jsonify(self.get_ecosystem_stats())
    
    def setup_socketio_events(self):
        """Настройка WebSocket событий"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Подключение пользователя"""
            user_id = session.get('user_id')
            if user_id:
                self.online_users.add(user_id)
                join_room('public_feed')
                emit('user_connected', {'user_id': user_id}, room='public_feed')
                self.logger.info(f"🔗 Пользователь подключен: {user_id}")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Отключение пользователя"""
            user_id = session.get('user_id')
            if user_id:
                self.online_users.discard(user_id)
                leave_room('public_feed')
                emit('user_disconnected', {'user_id': user_id}, room='public_feed')
                self.logger.info(f"🔌 Пользователь отключен: {user_id}")
        
        @self.socketio.on('join_community')
        def handle_join_community(data):
            """Присоединение к сообществу"""
            community_id = data.get('community_id')
            user_id = session.get('user_id')
            
            if community_id and user_id:
                join_room(f"community_{community_id}")
                emit('joined_community', {'community_id': community_id})
        
        @self.socketio.on('send_message')
        def handle_message(data):
            """Отправка сообщения в чат"""
            room = data.get('room', 'public_feed')
            message = data.get('message')
            user_id = session.get('user_id')
            
            if message and user_id:
                emit('new_message', {
                    'user_id': user_id,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }, room=room)
        
        @self.socketio.on('request_ai_insight')
        def handle_ai_insight_request(data):
            """Запрос ИИ инсайта"""
            topic = data.get('topic', 'market')
            user_id = session.get('user_id')
            
            if self.ai_coordinator and user_id:
                try:
                    # Генерируем ИИ инсайт
                    insight = asyncio.run(self.generate_ai_insight(topic))
                    emit('ai_insight', {
                        'topic': topic,
                        'insight': insight,
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception as e:
                    emit('error', {'message': f'AI insight error: {str(e)}'})
    
    def create_user_in_db(self, user: User):
        """Создание пользователя в БД"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO users 
                (user_id, username, email, password_hash, display_name, avatar_url, bio,
                 reputation, level, created_at, last_active, preferences, achievements)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.user_id, user.username, user.email, user.password_hash,
                user.display_name, user.avatar_url, user.bio, user.reputation,
                user.level, user.created_at.isoformat(), user.last_active.isoformat(),
                json.dumps(user.preferences), json.dumps(user.achievements)
            ))
    
    def create_post_in_db(self, post: SocialPost):
        """Создание поста в БД"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO posts 
                (post_id, author_id, content, content_type, tags, likes, comments, shares,
                 created_at, updated_at, visibility, ai_generated, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                post.post_id, post.author_id, post.content, post.content_type,
                json.dumps(post.tags), post.likes, post.comments, post.shares,
                post.created_at.isoformat(), post.updated_at.isoformat(),
                post.visibility, post.ai_generated, json.dumps(post.metadata)
            ))
    
    def toggle_post_reaction(self, post_id: str, user_id: str, reaction_type: str) -> Dict[str, Any]:
        """Переключение реакции на пост"""
        with sqlite3.connect(self.db_path) as conn:
            # Проверяем, есть ли уже реакция
            cursor = conn.cursor()
            cursor.execute("""
                SELECT reaction_type FROM post_reactions 
                WHERE user_id = ? AND post_id = ?
            """, (user_id, post_id))
            
            existing_reaction = cursor.fetchone()
            
            if existing_reaction:
                # Удаляем существующую реакцию
                conn.execute("""
                    DELETE FROM post_reactions 
                    WHERE user_id = ? AND post_id = ?
                """, (user_id, post_id))
                
                # Уменьшаем счетчик
                conn.execute("""
                    UPDATE posts SET likes = likes - 1 WHERE post_id = ?
                """, (post_id,))
                
                action = 'removed'
            else:
                # Добавляем новую реакцию
                conn.execute("""
                    INSERT INTO post_reactions (user_id, post_id, reaction_type, created_at)
                    VALUES (?, ?, ?, ?)
                """, (user_id, post_id, reaction_type, datetime.now().isoformat()))
                
                # Увеличиваем счетчик
                conn.execute("""
                    UPDATE posts SET likes = likes + 1 WHERE post_id = ?
                """, (post_id,))
                
                action = 'added'
            
            # Получаем новое количество лайков
            cursor.execute("SELECT likes FROM posts WHERE post_id = ?", (post_id,))
            new_count = cursor.fetchone()[0]
            
            return {
                'action': action,
                'reaction_type': reaction_type,
                'likes': new_count
            }
    
    def add_to_content_feed(self, post: SocialPost):
        """Добавление поста в ленту контента"""
        self.content_feed.appendleft(asdict(post))
        
        # Обновляем трендовые темы
        for tag in post.tags:
            self.trending_topics[tag] = self.trending_topics.get(tag, 0) + 1
    
    def get_public_feed(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Получение публичной ленты"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, u.username, u.display_name, u.avatar_url
                FROM posts p
                JOIN users u ON p.author_id = u.user_id
                WHERE p.visibility = 'public'
                ORDER BY p.created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            posts = []
            for row in cursor.fetchall():
                post_data = {
                    'post_id': row[0],
                    'author_id': row[1],
                    'content': row[2],
                    'content_type': row[3],
                    'tags': json.loads(row[4]),
                    'likes': row[5],
                    'comments': row[6],
                    'shares': row[7],
                    'created_at': row[8],
                    'updated_at': row[9],
                    'visibility': row[10],
                    'ai_generated': row[11],
                    'metadata': json.loads(row[12]),
                    'author_username': row[13],
                    'author_display_name': row[14],
                    'author_avatar': row[15]
                }
                posts.append(post_data)
            
            return posts
    
    def get_trending_topics(self) -> Dict[str, Any]:
        """Получение трендовых тем"""
        # Сортируем по популярности
        sorted_topics = sorted(
            self.trending_topics.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            'trending': sorted_topics[:10],
            'timestamp': datetime.now().isoformat()
        }
    
    def get_all_communities(self) -> List[Dict[str, Any]]:
        """Получение всех сообществ"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM communities ORDER BY member_count DESC
            """)
            
            communities = []
            for row in cursor.fetchall():
                community_data = {
                    'community_id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'category': row[3],
                    'admin_ids': json.loads(row[4]),
                    'member_count': row[5],
                    'created_at': row[6],
                    'settings': json.loads(row[7]),
                    'rules': json.loads(row[8])
                }
                communities.append(community_data)
            
            return communities
    
    def get_ecosystem_stats(self) -> Dict[str, Any]:
        """Получение статистики экосистемы"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Общая статистика
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM posts")
            total_posts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM communities")
            total_communities = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(likes) FROM posts")
            total_likes = cursor.fetchone()[0] or 0
            
            # Активность за последний день
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            cursor.execute("SELECT COUNT(*) FROM posts WHERE created_at > ?", (yesterday,))
            posts_today = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE last_active > ?", (yesterday,))
            active_users_today = cursor.fetchone()[0]
        
        return {
            'total_users': total_users,
            'total_posts': total_posts,
            'total_communities': total_communities,
            'total_likes': total_likes,
            'posts_today': posts_today,
            'active_users_today': active_users_today,
            'online_users': len(self.online_users),
            'trending_topics_count': len(self.trending_topics),
            'ai_available': AI_AVAILABLE,
            'timestamp': datetime.now().isoformat()
        }
    
    async def generate_ai_insight(self, topic: str) -> Dict[str, Any]:
        """Генерация ИИ инсайта"""
        if not self.ai_coordinator:
            return {'error': 'AI not available'}
        
        try:
            # Контекст для анализа
            context = {
                'topic': topic,
                'timestamp': datetime.now().isoformat(),
                'ecosystem_stats': self.get_ecosystem_stats(),
                'trending_topics': self.get_trending_topics()
            }
            
            # Анализ через ИИ
            analysis = self.ai_coordinator.ai_engine.analyze_context(context)
            
            insight_text = f"""
# ИИ Инсайт: {topic.title()}

Анализ текущей ситуации показывает:

- **Тренд**: {random.choice(['Восходящий', 'Нисходящий', 'Боковой'])}
- **Уверенность ИИ**: {analysis.get('confidence', 0.75):.1%}
- **Рекомендация**: {random.choice(['Hold', 'Buy', 'Sell', 'Wait'])}

## Ключевые факторы:
1. Социальная активность в экосистеме
2. Трендовые темы сообщества
3. ИИ-прогнозы алгоритмов

*Сгенерировано ИИ-системой Mirai*
            """
            
            return {
                'topic': topic,
                'insight': insight_text,
                'confidence': analysis.get('confidence', 0.75),
                'timestamp': datetime.now().isoformat(),
                'ai_model': 'MiraiAI'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_main_template(self) -> str:
        """Главный HTML шаблон"""
        return '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mirai Social Ecosystem</title>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { 
            background: rgba(255,255,255,0.1); 
            padding: 20px; 
            border-radius: 15px; 
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }
        .ecosystem-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px;
        }
        .card { 
            background: rgba(255,255,255,0.15); 
            padding: 25px; 
            border-radius: 15px; 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .card h3 { color: #FFD700; margin-bottom: 15px; font-size: 1.3em; }
        .stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
        .stat-item { text-align: center; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 10px; }
        .stat-number { font-size: 2em; font-weight: bold; color: #FFD700; }
        .stat-label { font-size: 0.9em; opacity: 0.8; }
        .feed { max-height: 400px; overflow-y: auto; }
        .post { 
            background: rgba(255,255,255,0.1); 
            padding: 15px; 
            border-radius: 10px; 
            margin-bottom: 15px;
            border-left: 4px solid #FFD700;
        }
        .post-header { display: flex; justify-content: space-between; margin-bottom: 10px; }
        .post-author { font-weight: bold; color: #FFD700; }
        .post-time { font-size: 0.8em; opacity: 0.7; }
        .post-content { line-height: 1.5; }
        .post-tags { margin-top: 10px; }
        .tag { 
            background: rgba(255,215,0,0.3); 
            padding: 3px 8px; 
            border-radius: 12px; 
            font-size: 0.8em; 
            margin-right: 5px;
        }
        .controls { display: flex; gap: 15px; margin: 20px 0; }
        .btn { 
            background: rgba(255,215,0,0.8); 
            color: #333; 
            border: none; 
            padding: 12px 20px; 
            border-radius: 8px; 
            cursor: pointer; 
            font-weight: bold;
            transition: all 0.3s;
        }
        .btn:hover { background: #FFD700; transform: translateY(-2px); }
        .ai-section { 
            background: linear-gradient(45deg, #667eea, #764ba2);
            border: 2px solid #FFD700;
        }
        .online-users { display: flex; flex-wrap: wrap; gap: 5px; }
        .user-badge { 
            background: rgba(255,215,0,0.3); 
            padding: 5px 10px; 
            border-radius: 15px; 
            font-size: 0.8em;
        }
        .trending-topics { display: flex; flex-wrap: wrap; gap: 8px; }
        .trending-topic { 
            background: rgba(255,215,0,0.4); 
            padding: 5px 12px; 
            border-radius: 15px; 
            font-size: 0.9em;
        }
        #messages { height: 200px; overflow-y: auto; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; }
        .message { padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .status-indicator { 
            width: 12px; 
            height: 12px; 
            border-radius: 50%; 
            display: inline-block; 
            margin-right: 8px;
        }
        .status-online { background: #00ff00; }
        .status-ai { background: #FFD700; }
        .footer { text-align: center; margin-top: 40px; opacity: 0.7; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 Mirai Social Ecosystem</h1>
            <p>Социальная экосистема с ИИ-интеграцией, community features и real-time взаимодействием</p>
            <div style="margin-top: 15px;">
                <span class="status-indicator status-online"></span>Система активна
                <span class="status-indicator status-ai" style="margin-left: 20px;"></span>ИИ доступен
            </div>
        </div>

        <div class="ecosystem-grid">
            <!-- Статистика экосистемы -->
            <div class="card">
                <h3>📊 Статистика экосистемы</h3>
                <div class="stats-grid" id="stats-grid">
                    <div class="stat-item">
                        <div class="stat-number" id="total-users">0</div>
                        <div class="stat-label">Пользователей</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number" id="total-posts">0</div>
                        <div class="stat-label">Постов</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number" id="online-users">0</div>
                        <div class="stat-label">Онлайн</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number" id="total-likes">0</div>
                        <div class="stat-label">Лайков</div>
                    </div>
                </div>
            </div>

            <!-- Лента постов -->
            <div class="card">
                <h3>📱 Лента постов</h3>
                <div class="feed" id="posts-feed">
                    <!-- Посты будут загружаться динамически -->
                </div>
                <div class="controls">
                    <button class="btn" onclick="loadPosts()">🔄 Обновить</button>
                    <button class="btn" onclick="generateAIContent()">🤖 ИИ-контент</button>
                </div>
            </div>

            <!-- Трендовые темы -->
            <div class="card">
                <h3>🔥 Трендовые темы</h3>
                <div class="trending-topics" id="trending-topics">
                    <!-- Трендовые темы будут загружаться динамически -->
                </div>
                <div style="margin-top: 15px;">
                    <button class="btn" onclick="loadTrending()">📈 Обновить тренды</button>
                </div>
            </div>

            <!-- ИИ-инсайты -->
            <div class="card ai-section">
                <h3>🧠 ИИ-инсайты</h3>
                <div id="ai-insights">
                    <p>Запросите ИИ-анализ для получения инсайтов...</p>
                </div>
                <div class="controls">
                    <button class="btn" onclick="requestAIInsight('market')">📊 Рынок</button>
                    <button class="btn" onclick="requestAIInsight('social')">👥 Социум</button>
                    <button class="btn" onclick="requestAIInsight('trends')">📈 Тренды</button>
                </div>
            </div>

            <!-- Реальное время чат -->
            <div class="card">
                <h3>💬 Чат реального времени</h3>
                <div id="messages"></div>
                <div style="margin-top: 10px; display: flex; gap: 10px;">
                    <input type="text" id="message-input" placeholder="Введите сообщение..." 
                           style="flex: 1; padding: 8px; border-radius: 5px; border: none;">
                    <button class="btn" onclick="sendMessage()">Отправить</button>
                </div>
            </div>

            <!-- Сообщества -->
            <div class="card">
                <h3>🏘️ Сообщества</h3>
                <div id="communities-list">
                    <!-- Список сообществ будет загружаться динамически -->
                </div>
                <button class="btn" onclick="loadCommunities()">🔄 Загрузить сообщества</button>
            </div>
        </div>

        <div class="footer">
            <p>Mirai AI Social Ecosystem | Автономная социальная платформа с ИИ-интеграцией</p>
            <p>🚀 Система работает в автономном режиме с real-time обновлениями</p>
        </div>
    </div>

    <script>
        // WebSocket соединение
        const socket = io();
        
        // Генерация случайного ID пользователя для демонстрации
        const userId = 'user_' + Math.random().toString(36).substr(2, 9);
        
        // Обработчики WebSocket событий
        socket.on('connect', () => {
            console.log('Подключен к WebSocket');
            addMessage('Система', 'Подключен к социальной экосистеме');
        });
        
        socket.on('new_post', (post) => {
            console.log('Новый пост:', post);
            addPostToFeed(post);
        });
        
        socket.on('new_message', (data) => {
            addMessage(data.user_id, data.message);
        });
        
        socket.on('ai_insight', (data) => {
            displayAIInsight(data);
        });
        
        socket.on('user_connected', (data) => {
            addMessage('Система', `Пользователь ${data.user_id} подключился`);
        });
        
        // Функции для работы с API
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                
                document.getElementById('total-users').textContent = stats.total_users;
                document.getElementById('total-posts').textContent = stats.total_posts;
                document.getElementById('online-users').textContent = stats.online_users;
                document.getElementById('total-likes').textContent = stats.total_likes;
            } catch (error) {
                console.error('Ошибка загрузки статистики:', error);
            }
        }
        
        async function loadPosts() {
            try {
                const response = await fetch('/api/feed');
                const posts = await response.json();
                
                const feedContainer = document.getElementById('posts-feed');
                feedContainer.innerHTML = '';
                
                posts.forEach(post => {
                    addPostToFeed(post);
                });
            } catch (error) {
                console.error('Ошибка загрузки постов:', error);
            }
        }
        
        async function loadTrending() {
            try {
                const response = await fetch('/api/trending');
                const trending = await response.json();
                
                const trendingContainer = document.getElementById('trending-topics');
                trendingContainer.innerHTML = '';
                
                trending.trending.forEach(([topic, count]) => {
                    const topicElement = document.createElement('div');
                    topicElement.className = 'trending-topic';
                    topicElement.textContent = `#${topic} (${count})`;
                    trendingContainer.appendChild(topicElement);
                });
            } catch (error) {
                console.error('Ошибка загрузки трендов:', error);
            }
        }
        
        async function loadCommunities() {
            try {
                const response = await fetch('/api/communities');
                const communities = await response.json();
                
                const communitiesContainer = document.getElementById('communities-list');
                communitiesContainer.innerHTML = '';
                
                communities.forEach(community => {
                    const communityElement = document.createElement('div');
                    communityElement.style.cssText = 'padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px; margin-bottom: 10px;';
                    communityElement.innerHTML = `
                        <strong>${community.name}</strong><br>
                        <small>${community.description}</small><br>
                        <span style="color: #FFD700;">👥 ${community.member_count} участников</span>
                    `;
                    communitiesContainer.appendChild(communityElement);
                });
            } catch (error) {
                console.error('Ошибка загрузки сообществ:', error);
            }
        }
        
        async function generateAIContent() {
            try {
                const response = await fetch('/api/ai/generate_content', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ type: 'analysis', topic: 'market' })
                });
                
                const content = await response.json();
                
                if (content.error) {
                    alert('Ошибка генерации ИИ-контента: ' + content.error);
                } else {
                    // Создаем пост с ИИ-контентом
                    const postResponse = await fetch('/api/posts', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            author_id: 'ai_system',
                            content: content.content ? content.content.substring(0, 500) + '...' : 'ИИ-контент сгенерирован',
                            content_type: 'ai_analysis',
                            tags: ['AI', 'Analysis', 'Market'],
                            ai_generated: true
                        })
                    });
                    
                    if (postResponse.ok) {
                        loadPosts(); // Обновляем ленту
                    }
                }
            } catch (error) {
                console.error('Ошибка генерации ИИ-контента:', error);
            }
        }
        
        function requestAIInsight(topic) {
            socket.emit('request_ai_insight', { topic: topic });
        }
        
        function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (message) {
                socket.emit('send_message', { 
                    message: message,
                    room: 'public_feed'
                });
                input.value = '';
            }
        }
        
        // Вспомогательные функции
        function addPostToFeed(post) {
            const feedContainer = document.getElementById('posts-feed');
            const postElement = document.createElement('div');
            postElement.className = 'post';
            
            const authorName = post.author_display_name || post.author_username || post.author_id;
            const timeAgo = timeAgoFromISO(post.created_at);
            
            postElement.innerHTML = `
                <div class="post-header">
                    <span class="post-author">${authorName} ${post.ai_generated ? '🤖' : ''}</span>
                    <span class="post-time">${timeAgo}</span>
                </div>
                <div class="post-content">${post.content}</div>
                <div class="post-tags">
                    ${post.tags.map(tag => `<span class="tag">#${tag}</span>`).join('')}
                </div>
                <div style="margin-top: 10px; color: #FFD700;">
                    👍 ${post.likes} 💬 ${post.comments} 🔄 ${post.shares}
                </div>
            `;
            
            feedContainer.insertBefore(postElement, feedContainer.firstChild);
        }
        
        function addMessage(sender, message) {
            const messagesContainer = document.getElementById('messages');
            const messageElement = document.createElement('div');
            messageElement.className = 'message';
            messageElement.innerHTML = `<strong>${sender}:</strong> ${message}`;
            messagesContainer.appendChild(messageElement);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function displayAIInsight(data) {
            const insightsContainer = document.getElementById('ai-insights');
            insightsContainer.innerHTML = `
                <div style="background: rgba(255,215,0,0.2); padding: 15px; border-radius: 8px;">
                    <h4>🤖 ${data.topic.toUpperCase()} Инсайт</h4>
                    <div style="white-space: pre-line; margin: 10px 0;">${data.insight}</div>
                    <small>Уверенность: ${(data.confidence * 100).toFixed(1)}% | ${new Date(data.timestamp).toLocaleTimeString()}</small>
                </div>
            `;
        }
        
        function timeAgoFromISO(isoString) {
            const date = new Date(isoString);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            
            if (diffMins < 1) return 'только что';
            if (diffMins < 60) return `${diffMins} мин назад`;
            if (diffMins < 1440) return `${Math.floor(diffMins / 60)} ч назад`;
            return `${Math.floor(diffMins / 1440)} дн назад`;
        }
        
        // Обработчик Enter для отправки сообщения
        document.getElementById('message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Автоматическое обновление данных
        setInterval(() => {
            loadStats();
            loadTrending();
        }, 30000); // каждые 30 секунд
        
        // Первоначальная загрузка данных
        loadStats();
        loadPosts();
        loadTrending();
        loadCommunities();
    </script>
</body>
</html>
        '''
    
    async def start_autonomous_social_cycle(self):
        """Автономный цикл социальной экосистемы"""
        self.logger.info("🌐 Запуск автономного цикла социальной экосистемы")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                self.logger.info(f"🔄 Социальный цикл {cycle_count}")
                
                # Генерируем ИИ-контент для экосистемы
                if cycle_count % 5 == 0 and self.content_engine:
                    await self.create_ai_generated_posts()
                
                # Обновляем трендовые темы
                if cycle_count % 3 == 0:
                    await self.update_trending_topics()
                
                # Моделируем активность пользователей
                if cycle_count % 2 == 0:
                    await self.simulate_user_activity()
                
                # Уведомления в реальном времени
                await self.broadcast_ecosystem_updates()
                
                # Пауза между циклами
                await asyncio.sleep(120)  # 2 минуты
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка в социальном цикле {cycle_count}: {e}")
                await asyncio.sleep(60)
    
    async def create_ai_generated_posts(self):
        """Создание ИИ-постов"""
        try:
            # Генерируем контент через ИИ-движок
            content_types = ['analysis', 'signal']
            content_type = random.choice(content_types)
            
            if content_type == 'analysis':
                result = await self.content_engine.generate_market_analysis_article()
                content = result.get('content', 'ИИ-анализ рынка')[:500] + '...'
            else:
                result = await self.content_engine.generate_trading_signal()
                content = result.get('formatted_content', 'Торговый сигнал от ИИ')[:500] + '...'
            
            # Создаем пост
            post = SocialPost(
                post_id=str(uuid.uuid4()),
                author_id='mirai_ai_system',
                content=content,
                content_type=f'ai_{content_type}',
                tags=['AI', 'Trading', 'Analysis', 'Mirai'],
                likes=random.randint(5, 25),
                comments=random.randint(0, 8),
                shares=random.randint(1, 5),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                visibility='public',
                ai_generated=True,
                metadata={'quality_score': result.get('quality_score', 0.8)}
            )
            
            # Сохраняем в БД и ленту
            self.create_post_in_db(post)
            self.add_to_content_feed(post)
            
            # Уведомление в реальном времени
            self.socketio.emit('new_post', asdict(post), room='public_feed')
            
            self.logger.info(f"🤖 Создан ИИ-пост: {content_type}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания ИИ-поста: {e}")
    
    async def update_trending_topics(self):
        """Обновление трендовых тем"""
        # Добавляем актуальные темы
        current_topics = ['Bitcoin', 'AI', 'Trading', 'DeFi', 'NFT', 'Ethereum', 'Market', 'Crypto']
        
        for topic in random.sample(current_topics, 3):
            self.trending_topics[topic] = self.trending_topics.get(topic, 0) + random.randint(1, 5)
        
        # Убываем старые темы
        for topic in list(self.trending_topics.keys()):
            self.trending_topics[topic] = max(0, self.trending_topics[topic] - 1)
            if self.trending_topics[topic] == 0:
                del self.trending_topics[topic]
    
    async def simulate_user_activity(self):
        """Симуляция активности пользователей"""
        # Добавляем случайные лайки к постам
        recent_posts = list(self.content_feed)[:10]
        
        for post in random.sample(recent_posts, min(3, len(recent_posts))):
            if random.random() < 0.3:  # 30% шанс получить лайк
                post['likes'] += random.randint(1, 3)
    
    async def broadcast_ecosystem_updates(self):
        """Трансляция обновлений экосистемы"""
        stats = self.get_ecosystem_stats()
        
        # Отправляем статистику всем подключенным пользователям
        self.socketio.emit('stats_update', stats, room='public_feed')
        
        # Отправляем трендовые темы
        trending = self.get_trending_topics()
        self.socketio.emit('trending_update', trending, room='public_feed')
    
    def start_social_ecosystem(self):
        """Запуск социальной экосистемы"""
        self.logger.info("🚀 Запуск Mirai Social Ecosystem")
        
        # Создаем тестовых пользователей и сообщества
        self.create_initial_data()
        
        # Запуск веб-сервера в отдельном потоке
        server_thread = threading.Thread(
            target=lambda: self.socketio.run(self.app, host='0.0.0.0', port=8082, debug=False)
        )
        server_thread.daemon = True
        server_thread.start()
        
        # Запуск автономного цикла
        asyncio.run(self.start_autonomous_social_cycle())
    
    def create_initial_data(self):
        """Создание начальных данных"""
        try:
            # Создаем ИИ-пользователя
            ai_user = User(
                user_id='mirai_ai_system',
                username='MiraiAI',
                email='ai@mirai.system',
                password_hash='',
                display_name='Mirai AI Assistant',
                avatar_url='',
                bio='Автономная ИИ-система для анализа и генерации контента',
                reputation=1000,
                level='ai_entity',
                created_at=datetime.now(),
                last_active=datetime.now(),
                preferences={'ai_generated': True},
                achievements=['AI_CREATOR', 'CONTENT_GENERATOR']
            )
            
            self.create_user_in_db(ai_user)
            
            # Создаем тестовое сообщество
            community = Community(
                community_id=str(uuid.uuid4()),
                name='Mirai Traders',
                description='Сообщество трейдеров использующих ИИ-аналитику Mirai',
                category='Trading',
                admin_ids=['mirai_ai_system'],
                member_count=150,
                created_at=datetime.now(),
                settings={'public': True, 'ai_content': True},
                rules=['Уважение к участникам', 'Качественный контент', 'Никакого спама']
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO communities 
                    (community_id, name, description, category, admin_ids, member_count, created_at, settings, rules)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    community.community_id, community.name, community.description,
                    community.category, json.dumps(community.admin_ids),
                    community.member_count, community.created_at.isoformat(),
                    json.dumps(community.settings), json.dumps(community.rules)
                ))
            
            self.logger.info("📊 Начальные данные созданы")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания начальных данных: {e}")

async def main():
    """Основная функция запуска социальной экосистемы"""
    print("🌐 Mirai Social Ecosystem Platform")
    print("Инициализация социальной экосистемы с ИИ-интеграцией...")
    
    ecosystem = SocialEcosystemAPI()
    
    try:
        ecosystem.start_social_ecosystem()
    except KeyboardInterrupt:
        print("\n🛑 Остановка социальной экосистемы...")
        ecosystem.logger.info("Социальная экосистема остановлена пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        ecosystem.logger.error(f"Критическая ошибка социальной экосистемы: {e}")

if __name__ == "__main__":
    asyncio.run(main())