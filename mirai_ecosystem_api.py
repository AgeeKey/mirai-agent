#!/usr/bin/env python3
"""
Mirai Agent - Enhanced API для развития экосистемы
Включает: рабочий дневник, аналитику, блог, контент-менеджмент
"""

from fastapi import FastAPI, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import asyncio
import aiofiles

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(
    title="Mirai Agent Ecosystem",
    description="Autonomous AI Agent for Trading & Services",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_PATH = "/app/state/mirai_ecosystem.db"

def init_database():
    """Initialize SQLite database with ecosystem tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Diary entries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diary_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT,
            project TEXT,
            outcome TEXT,
            metrics TEXT
        )
    ''')
    
    # Analytics data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            metadata TEXT
        )
    ''')
    
    # Blog posts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            title TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            excerpt TEXT,
            published BOOLEAN DEFAULT FALSE,
            category TEXT,
            tags TEXT,
            views INTEGER DEFAULT 0
        )
    ''')
    
    # Trading data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trading_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_date DATE NOT NULL,
            start_balance REAL,
            end_balance REAL,
            pnl REAL,
            trades_count INTEGER,
            win_rate REAL,
            notes TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Pydantic models
class DiaryEntry(BaseModel):
    category: str
    title: str
    content: str
    tags: Optional[str] = None
    project: Optional[str] = None
    outcome: Optional[str] = None
    metrics: Optional[str] = None

class BlogPost(BaseModel):
    title: str
    slug: str
    content: str
    excerpt: Optional[str] = None
    published: bool = False
    category: Optional[str] = None
    tags: Optional[str] = None

class TradingSession(BaseModel):
    session_date: str
    start_balance: float
    end_balance: float
    pnl: float
    trades_count: int
    win_rate: float
    notes: Optional[str] = None

class AnalyticsMetric(BaseModel):
    metric_name: str
    metric_value: float
    metadata: Optional[Dict[str, Any]] = None

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()

# === ОСНОВНЫЕ ЭНДПОИНТЫ ===

@app.get("/")
async def root():
    """Root endpoint with service information"""
    service_type = os.getenv("SERVICE_TYPE", "unknown")
    domain = os.getenv("DOMAIN", "localhost")
    
    if service_type == "trading":
        return {
            "message": "Mirai Trading Platform - Рабочий дневник ИИ-агента",
            "service": service_type,
            "domain": domain,
            "features": ["diary", "analytics", "trading_logs", "performance_tracking"],
            "status": "healthy"
        }
    else:
        return {
            "message": "Mirai Information Portal - Портал знаний и сервисов",
            "service": service_type,
            "domain": domain,
            "features": ["blog", "resources", "community", "documentation"],
            "status": "healthy"
        }

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# === ДНЕВНИК (DIARY) ===

@app.post("/api/v1/diary/entry")
async def create_diary_entry(entry: DiaryEntry):
    """Создать запись в дневнике"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO diary_entries (category, title, content, tags, project, outcome, metrics)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (entry.category, entry.title, entry.content, entry.tags, 
          entry.project, entry.outcome, entry.metrics))
    
    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": entry_id, "message": "Diary entry created successfully"}

@app.get("/api/v1/diary/entries")
async def get_diary_entries(
    category: Optional[str] = None,
    project: Optional[str] = None,
    days: int = 30
):
    """Получить записи дневника с фильтрацией"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = '''
        SELECT * FROM diary_entries 
        WHERE timestamp >= datetime('now', '-{} days')
    '''.format(days)
    
    params = []
    if category:
        query += ' AND category = ?'
        params.append(category)
    if project:
        query += ' AND project = ?'
        params.append(project)
    
    query += ' ORDER BY timestamp DESC'
    
    cursor.execute(query, params)
    entries = cursor.fetchall()
    conn.close()
    
    return {
        "entries": [
            {
                "id": row[0],
                "timestamp": row[1],
                "category": row[2],
                "title": row[3],
                "content": row[4],
                "tags": row[5],
                "project": row[6],
                "outcome": row[7],
                "metrics": row[8]
            }
            for row in entries
        ]
    }

# === АНАЛИТИКА ===

@app.post("/api/v1/analytics/metric")
async def record_metric(metric: AnalyticsMetric):
    """Записать метрику"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    metadata_json = json.dumps(metric.metadata) if metric.metadata else None
    
    cursor.execute('''
        INSERT INTO analytics (metric_name, metric_value, metadata)
        VALUES (?, ?, ?)
    ''', (metric.metric_name, metric.metric_value, metadata_json))
    
    conn.commit()
    conn.close()
    
    return {"message": "Metric recorded successfully"}

@app.get("/api/v1/analytics/metrics/{metric_name}")
async def get_metrics(metric_name: str, days: int = 30):
    """Получить метрики за период"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT timestamp, metric_value, metadata FROM analytics
        WHERE metric_name = ? AND timestamp >= datetime('now', '-{} days')
        ORDER BY timestamp DESC
    '''.format(days), (metric_name,))
    
    metrics = cursor.fetchall()
    conn.close()
    
    return {
        "metric_name": metric_name,
        "data": [
            {
                "timestamp": row[0],
                "value": row[1],
                "metadata": json.loads(row[2]) if row[2] else None
            }
            for row in metrics
        ]
    }

@app.get("/api/v1/analytics/dashboard")
async def analytics_dashboard():
    """Дашборд аналитики"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Основные метрики за последние 7 дней
    cursor.execute('''
        SELECT metric_name, AVG(metric_value) as avg_value, COUNT(*) as count
        FROM analytics 
        WHERE timestamp >= datetime('now', '-7 days')
        GROUP BY metric_name
    ''')
    
    metrics_summary = cursor.fetchall()
    
    # Количество записей в дневнике за неделю
    cursor.execute('''
        SELECT COUNT(*) FROM diary_entries 
        WHERE timestamp >= datetime('now', '-7 days')
    ''')
    diary_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "summary": {
            "diary_entries_week": diary_count,
            "metrics": {
                row[0]: {"average": row[1], "count": row[2]}
                for row in metrics_summary
            }
        }
    }

# === БЛОГ (для aimirai.info) ===

@app.post("/api/v1/blog/post")
async def create_blog_post(post: BlogPost):
    """Создать пост в блоге"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO blog_posts (title, slug, content, excerpt, published, category, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (post.title, post.slug, post.content, post.excerpt, 
              post.published, post.category, post.tags))
        
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {"id": post_id, "message": "Blog post created successfully"}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Post with this slug already exists")

@app.get("/api/v1/blog/posts")
async def get_blog_posts(published_only: bool = False, category: Optional[str] = None):
    """Получить посты блога"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = 'SELECT * FROM blog_posts'
    params = []
    
    conditions = []
    if published_only:
        conditions.append('published = ?')
        params.append(True)
    if category:
        conditions.append('category = ?')
        params.append(category)
    
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    
    query += ' ORDER BY created_at DESC'
    
    cursor.execute(query, params)
    posts = cursor.fetchall()
    conn.close()
    
    return {
        "posts": [
            {
                "id": row[0],
                "created_at": row[1],
                "updated_at": row[2],
                "title": row[3],
                "slug": row[4],
                "content": row[5],
                "excerpt": row[6],
                "published": row[7],
                "category": row[8],
                "tags": row[9],
                "views": row[10]
            }
            for row in posts
        ]
    }

# === ТРЕЙДИНГ ===

@app.get("/api/v1/trading/status")
async def trading_status():
    """Trading status endpoint"""
    return {
        "trading_active": False,
        "dry_run": True,
        "positions": [],
        "balance": 0.0,
        "risk_limit": 30.0  # USDT
    }

@app.post("/api/v1/trading/session")
async def record_trading_session(session: TradingSession):
    """Записать торговую сессию"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO trading_sessions 
        (session_date, start_balance, end_balance, pnl, trades_count, win_rate, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (session.session_date, session.start_balance, session.end_balance,
          session.pnl, session.trades_count, session.win_rate, session.notes))
    
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": session_id, "message": "Trading session recorded"}

@app.get("/api/v1/trading/performance")
async def trading_performance(days: int = 30):
    """Получить статистику торговли"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_sessions,
            SUM(pnl) as total_pnl,
            AVG(pnl) as avg_pnl,
            AVG(win_rate) as avg_win_rate,
            SUM(trades_count) as total_trades
        FROM trading_sessions 
        WHERE session_date >= date('now', '-{} days')
    '''.format(days))
    
    stats = cursor.fetchone()
    conn.close()
    
    return {
        "period_days": days,
        "total_sessions": stats[0] or 0,
        "total_pnl": stats[1] or 0.0,
        "average_pnl": stats[2] or 0.0,
        "average_win_rate": stats[3] or 0.0,
        "total_trades": stats[4] or 0
    }

# === СЕРВИСЫ (для aimirai.info) ===

@app.get("/api/v1/services/info")
async def services_info():
    """Services information endpoint"""
    return {
        "services": [
            "ai_advisor",
            "portfolio_manager", 
            "risk_engine",
            "content_generator",
            "learning_assistant"
        ],
        "status": "operational",
        "uptime": "00:05:00",
        "features": {
            "blog": "активен",
            "documentation": "в разработке",
            "community": "планируется",
            "courses": "планируется"
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )