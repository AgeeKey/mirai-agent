"""
Mirai Agent - Простая панель мониторинга
Веб-интерфейс для отображения метрик без Grafana
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio
import time
import psutil
import sqlite3
import os
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

app = FastAPI(title="Mirai Monitoring Panel", description="Simple monitoring dashboard")

class SimpleMonitoring:
    def __init__(self):
        self.start_time = time.time()
        self.metrics_cache = {}
        self.cache_expiry = {}
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """Получение системных метрик"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_usage": round(cpu_percent, 1),
                "memory_usage": round(memory.percent, 1),
                "disk_usage": round(disk.percent, 1),
                "memory_total": round(memory.total / (1024**3), 1),  # GB
                "memory_available": round(memory.available / (1024**3), 1),  # GB
                "disk_total": round(disk.total / (1024**3), 1),  # GB
                "disk_free": round(disk.free / (1024**3), 1),  # GB
                "uptime": round(time.time() - self.start_time, 0)
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_trading_metrics(self) -> Dict[str, Any]:
        """Получение торговых метрик"""
        try:
            db_path = '/root/mirai-agent/state/mirai.db'
            
            if not os.path.exists(db_path):
                return {
                    "total_pnl": 0.0,
                    "daily_pnl": 0.0,
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "active_positions": 0,
                    "status": "Database not found"
                }
            
            # Создаем простую структуру БД если её нет
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Создаем таблицы если их нет
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    side TEXT,
                    amount REAL,
                    price REAL,
                    pnl REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    side TEXT,
                    amount REAL,
                    entry_price REAL,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            
            # Получаем метрики
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(pnl), 0) FROM trades")
            total_trades, total_pnl = cursor.fetchone()
            
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(pnl), 0) 
                FROM trades 
                WHERE created_at > datetime('now', '-1 day')
            """)
            daily_trades, daily_pnl = cursor.fetchone()
            
            cursor.execute("""
                SELECT COUNT(CASE WHEN pnl > 0 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as win_rate
                FROM trades 
                WHERE created_at > datetime('now', '-7 days')
            """)
            win_rate_result = cursor.fetchone()
            win_rate = win_rate_result[0] if win_rate_result[0] else 0.0
            
            cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'active'")
            active_positions = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_pnl": round(float(total_pnl), 2),
                "daily_pnl": round(float(daily_pnl), 2),
                "total_trades": int(total_trades),
                "daily_trades": int(daily_trades),
                "win_rate": round(float(win_rate), 1),
                "active_positions": int(active_positions),
                "status": "Connected"
            }
            
        except Exception as e:
            return {"error": str(e), "status": "Error"}
    
    async def get_ai_metrics(self) -> Dict[str, Any]:
        """Получение AI метрик"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8080/health", timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "Connected",
                        "ai_confidence": data.get("ai_confidence", 0),
                        "response_time": data.get("response_time", 0),
                        "decisions_count": data.get("decisions_count", 0),
                        "last_decision": data.get("last_decision", ""),
                        "uptime": data.get("uptime", 0)
                    }
                else:
                    return {"status": "Error", "code": response.status_code}
                    
        except Exception as e:
            return {"status": "Disconnected", "error": str(e)}
    
    async def get_api_metrics(self) -> Dict[str, Any]:
        """Получение API метрик"""
        try:
            metrics = {}
            
            # Проверка Trading API
            try:
                async with httpx.AsyncClient() as client:
                    start_time = time.time()
                    response = await client.get("http://localhost:8001/health", timeout=5)
                    response_time = round((time.time() - start_time) * 1000, 1)
                    
                    metrics["trading_api"] = {
                        "status": "Connected" if response.status_code == 200 else "Error",
                        "response_time": response_time,
                        "code": response.status_code
                    }
            except:
                metrics["trading_api"] = {"status": "Disconnected", "response_time": 0}
            
            # Проверка Web API
            try:
                async with httpx.AsyncClient() as client:
                    start_time = time.time()
                    response = await client.get("http://localhost:8000/health", timeout=5)
                    response_time = round((time.time() - start_time) * 1000, 1)
                    
                    metrics["web_api"] = {
                        "status": "Connected" if response.status_code == 200 else "Error",
                        "response_time": response_time,
                        "code": response.status_code
                    }
            except:
                metrics["web_api"] = {"status": "Disconnected", "response_time": 0}
            
            return metrics
            
        except Exception as e:
            return {"error": str(e)}

monitor = SimpleMonitoring()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Главная страница дашборда"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mirai Agent - Monitoring Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            
            .header {
                text-align: center;
                margin-bottom: 30px;
                padding: 20px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                backdrop-filter: blur(10px);
            }
            
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }
            
            .header p {
                font-size: 1.1em;
                opacity: 0.9;
            }
            
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .metric-card {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                padding: 20px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            
            .metric-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            }
            
            .metric-card h3 {
                font-size: 1.3em;
                margin-bottom: 15px;
                color: #f1c40f;
            }
            
            .metric-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
                padding: 8px 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .metric-row:last-child {
                border-bottom: none;
                margin-bottom: 0;
            }
            
            .metric-label {
                font-weight: 500;
                opacity: 0.9;
            }
            
            .metric-value {
                font-weight: bold;
                font-size: 1.1em;
            }
            
            .status-connected { color: #2ecc71; }
            .status-error { color: #e74c3c; }
            .status-warning { color: #f39c12; }
            .status-disconnected { color: #95a5a6; }
            
            .progress-bar {
                width: 100%;
                height: 8px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                overflow: hidden;
                margin-top: 5px;
            }
            
            .progress-fill {
                height: 100%;
                transition: width 0.3s ease;
                border-radius: 4px;
            }
            
            .progress-low { background: #2ecc71; }
            .progress-medium { background: #f39c12; }
            .progress-high { background: #e74c3c; }
            
            .update-info {
                text-align: center;
                margin-top: 20px;
                padding: 15px;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 8px;
                font-size: 0.9em;
                opacity: 0.8;
            }
            
            .refresh-btn {
                background: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 1em;
                margin-left: 10px;
                transition: background 0.3s ease;
            }
            
            .refresh-btn:hover {
                background: #2980b9;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            
            .loading {
                animation: pulse 1.5s infinite;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Mirai Agent</h1>
                <p>Система мониторинга автономного торгового агента</p>
                <button class="refresh-btn" onclick="loadMetrics()">🔄 Обновить</button>
            </div>
            
            <div class="metrics-grid" id="metricsGrid">
                <div class="metric-card loading">
                    <h3>📊 Загрузка метрик...</h3>
                </div>
            </div>
            
            <div class="update-info">
                <span id="lastUpdate">Загрузка данных...</span>
            </div>
        </div>
        
        <script>
            async function loadMetrics() {
                try {
                    const response = await fetch('/metrics');
                    const data = await response.json();
                    renderMetrics(data);
                    document.getElementById('lastUpdate').textContent = 
                        `Последнее обновление: ${new Date().toLocaleString('ru-RU')}`;
                } catch (error) {
                    console.error('Error loading metrics:', error);
                    document.getElementById('metricsGrid').innerHTML = 
                        '<div class="metric-card"><h3>❌ Ошибка загрузки метрик</h3></div>';
                }
            }
            
            function renderMetrics(data) {
                const grid = document.getElementById('metricsGrid');
                grid.innerHTML = '';
                
                // Системные метрики
                if (data.system) {
                    const systemCard = createSystemCard(data.system);
                    grid.appendChild(systemCard);
                }
                
                // Торговые метрики
                if (data.trading) {
                    const tradingCard = createTradingCard(data.trading);
                    grid.appendChild(tradingCard);
                }
                
                // AI метрики
                if (data.ai) {
                    const aiCard = createAICard(data.ai);
                    grid.appendChild(aiCard);
                }
                
                // API метрики
                if (data.api) {
                    const apiCard = createAPICard(data.api);
                    grid.appendChild(apiCard);
                }
            }
            
            function createSystemCard(system) {
                const card = document.createElement('div');
                card.className = 'metric-card';
                
                const cpuClass = system.cpu_usage > 80 ? 'progress-high' : 
                               system.cpu_usage > 60 ? 'progress-medium' : 'progress-low';
                const memoryClass = system.memory_usage > 85 ? 'progress-high' : 
                                  system.memory_usage > 70 ? 'progress-medium' : 'progress-low';
                const diskClass = system.disk_usage > 90 ? 'progress-high' : 
                                system.disk_usage > 80 ? 'progress-medium' : 'progress-low';
                
                card.innerHTML = `
                    <h3>💻 Системные ресурсы</h3>
                    <div class="metric-row">
                        <span class="metric-label">CPU загрузка</span>
                        <span class="metric-value">${system.cpu_usage}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill ${cpuClass}" style="width: ${system.cpu_usage}%"></div>
                    </div>
                    
                    <div class="metric-row">
                        <span class="metric-label">Память</span>
                        <span class="metric-value">${system.memory_usage}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill ${memoryClass}" style="width: ${system.memory_usage}%"></div>
                    </div>
                    
                    <div class="metric-row">
                        <span class="metric-label">Диск</span>
                        <span class="metric-value">${system.disk_usage}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill ${diskClass}" style="width: ${system.disk_usage}%"></div>
                    </div>
                    
                    <div class="metric-row">
                        <span class="metric-label">Uptime</span>
                        <span class="metric-value">${Math.floor(system.uptime / 3600)}ч ${Math.floor((system.uptime % 3600) / 60)}м</span>
                    </div>
                `;
                
                return card;
            }
            
            function createTradingCard(trading) {
                const card = document.createElement('div');
                card.className = 'metric-card';
                
                const pnlColor = trading.daily_pnl >= 0 ? 'status-connected' : 'status-error';
                const totalPnlColor = trading.total_pnl >= 0 ? 'status-connected' : 'status-error';
                
                card.innerHTML = `
                    <h3>📈 Торговые метрики</h3>
                    <div class="metric-row">
                        <span class="metric-label">Общий P&L</span>
                        <span class="metric-value ${totalPnlColor}">$${trading.total_pnl}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Дневной P&L</span>
                        <span class="metric-value ${pnlColor}">$${trading.daily_pnl}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Винрейт</span>
                        <span class="metric-value">${trading.win_rate}%</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Активные позиции</span>
                        <span class="metric-value">${trading.active_positions}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Всего сделок</span>
                        <span class="metric-value">${trading.total_trades}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Статус</span>
                        <span class="metric-value status-connected">${trading.status}</span>
                    </div>
                `;
                
                return card;
            }
            
            function createAICard(ai) {
                const card = document.createElement('div');
                card.className = 'metric-card';
                
                const statusClass = ai.status === 'Connected' ? 'status-connected' : 
                                  ai.status === 'Error' ? 'status-error' : 'status-disconnected';
                
                card.innerHTML = `
                    <h3>🤖 AI Orchestrator</h3>
                    <div class="metric-row">
                        <span class="metric-label">Статус</span>
                        <span class="metric-value ${statusClass}">${ai.status}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Уверенность AI</span>
                        <span class="metric-value">${ai.ai_confidence || 0}%</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Время ответа</span>
                        <span class="metric-value">${ai.response_time || 0}мс</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Решений принято</span>
                        <span class="metric-value">${ai.decisions_count || 0}</span>
                    </div>
                `;
                
                return card;
            }
            
            function createAPICard(api) {
                const card = document.createElement('div');
                card.className = 'metric-card';
                
                const tradingStatus = api.trading_api ? 
                    (api.trading_api.status === 'Connected' ? 'status-connected' : 
                     api.trading_api.status === 'Error' ? 'status-error' : 'status-disconnected') : 
                    'status-disconnected';
                    
                const webStatus = api.web_api ? 
                    (api.web_api.status === 'Connected' ? 'status-connected' : 
                     api.web_api.status === 'Error' ? 'status-error' : 'status-disconnected') : 
                    'status-disconnected';
                
                card.innerHTML = `
                    <h3>🌐 API Сервисы</h3>
                    <div class="metric-row">
                        <span class="metric-label">Trading API</span>
                        <span class="metric-value ${tradingStatus}">${api.trading_api?.status || 'Unknown'}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Время ответа</span>
                        <span class="metric-value">${api.trading_api?.response_time || 0}мс</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Web API</span>
                        <span class="metric-value ${webStatus}">${api.web_api?.status || 'Unknown'}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Время ответа</span>
                        <span class="metric-value">${api.web_api?.response_time || 0}мс</span>
                    </div>
                `;
                
                return card;
            }
            
            // Автообновление каждые 30 секунд
            setInterval(loadMetrics, 30000);
            
            // Первоначальная загрузка
            loadMetrics();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/metrics")
async def get_metrics():
    """API для получения всех метрик"""
    try:
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": monitor.get_system_metrics(),
            "trading": await monitor.get_trading_metrics(),
            "ai": await monitor.get_ai_metrics(),
            "api": await monitor.get_api_metrics()
        }
        
        return JSONResponse(content=metrics)
        
    except Exception as e:
        return JSONResponse(
            content={"error": str(e), "timestamp": datetime.now().isoformat()},
            status_code=500
        )

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9999)