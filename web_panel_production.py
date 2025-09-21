"""
Production Web Panel - Mirai Agent
Integration with all microservices
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import httpx
import secrets
import os
from datetime import datetime
from typing import Optional, Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mirai Agent - Production Panel",
    description="Панель управления торговым ботом с микросервисами",
    version="2.0.0"
)

security = HTTPBasic()

# Credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Agee1234"

# Microservices URLs
MICROSERVICES = {
    "data-collector": "http://data-collector:8001",
    "strategy-engine": "http://strategy-engine:8002", 
    "risk-engine": "http://risk-engine:8003",
    "analytics": "http://analytics:8004",
    "notifications": "http://notifications:8005",
    "portfolio-manager": "http://portfolio-manager:8006",
    "ai-engine": "http://ai-engine:8007"
}

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = ADMIN_USERNAME.encode("utf8")
    is_correct_username = secrets.compare_digest(current_username_bytes, correct_username_bytes)
    
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = ADMIN_PASSWORD.encode("utf8")
    is_correct_password = secrets.compare_digest(current_password_bytes, correct_password_bytes)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

async def call_microservice(service: str, endpoint: str, method: str = "GET", data: Optional[Dict] = None):
    """Helper function to call microservices"""
    if service not in MICROSERVICES:
        raise HTTPException(status_code=404, detail=f"Service {service} not found")
    
    url = f"{MICROSERVICES[service]}{endpoint}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json=data if data else {})
            else:
                raise HTTPException(status_code=400, detail="Method not supported")
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Service returned {response.status_code}", "detail": response.text}
                
    except httpx.TimeoutException:
        return {"error": "Service timeout", "service": service}
    except httpx.ConnectError:
        return {"error": "Service unavailable", "service": service}
    except Exception as e:
        return {"error": str(e), "service": service}

@app.get("/", response_class=HTMLResponse)
async def dashboard(username: str = Depends(authenticate)):
    """Main dashboard with microservices integration"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mirai Agent - Production Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }}
            .header {{
                background: rgba(255,255,255,0.95);
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                border-bottom: 3px solid #4CAF50;
            }}
            .container {{
                max-width: 1400px;
                margin: 20px auto;
                padding: 0 20px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 20px;
            }}
            .service-card {{
                background: rgba(255,255,255,0.95);
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
                border: 2px solid transparent;
            }}
            .service-card:hover {{
                transform: translateY(-5px);
                border-color: #4CAF50;
            }}
            .service-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 2px solid #eee;
            }}
            .service-title {{
                font-size: 1.4em;
                font-weight: bold;
                color: #2c3e50;
            }}
            .status-indicator {{
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-left: 10px;
            }}
            .status-healthy {{ background: #4CAF50; }}
            .status-warning {{ background: #FF9800; }}
            .status-error {{ background: #F44336; }}
            .controls {{
                display: flex;
                gap: 10px;
                margin: 15px 0;
                flex-wrap: wrap;
            }}
            .btn {{
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: bold;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-block;
                text-align: center;
                font-size: 14px;
            }}
            .btn-primary {{ background: #4CAF50; color: white; }}
            .btn-secondary {{ background: #2196F3; color: white; }}
            .btn-warning {{ background: #FF9800; color: white; }}
            .btn-danger {{ background: #F44336; color: white; }}
            .btn:hover {{ opacity: 0.8; transform: scale(1.05); }}
            .metrics {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-top: 20px;
            }}
            .metric {{
                text-align: center;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 8px;
                border-left: 4px solid #4CAF50;
            }}
            .metric-value {{
                font-size: 1.5em;
                font-weight: bold;
                color: #2c3e50;
            }}
            .metric-label {{
                font-size: 0.9em;
                color: #666;
                margin-top: 5px;
            }}
            .footer {{
                text-align: center;
                padding: 30px;
                color: white;
                font-size: 0.9em;
            }}
            .log-container {{
                margin-top: 20px;
                max-height: 200px;
                overflow-y: auto;
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #ddd;
            }}
            .system-overview {{
                grid-column: 1 / -1;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-align: center;
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 Mirai Agent - Production Dashboard</h1>
            <p>Продуктивная торговая система с микросервисной архитектурой</p>
            <p>Пользователь: <strong>{username}</strong> | Время: <span id="currentTime"></span></p>
        </div>

        <div class="container">
            <div class="system-overview">
                <h2>📊 Обзор системы</h2>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value" id="totalServices">8</div>
                        <div class="metric-label">Активных сервисов</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="systemStatus">RUNNING</div>
                        <div class="metric-label">Статус системы</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="uptime">--</div>
                        <div class="metric-label">Время работы</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="environment">PRODUCTION</div>
                        <div class="metric-label">Окружение</div>
                    </div>
                </div>
            </div>

            <!-- Data Collector Service -->
            <div class="service-card">
                <div class="service-header">
                    <span class="service-title">📡 Data Collector</span>
                    <span class="status-indicator status-healthy" id="data-collector-status"></span>
                </div>
                <p>Сбор рыночных данных в реальном времени</p>
                <div class="controls">
                    <button class="btn btn-primary" onclick="startDataCollection()">Запустить сбор</button>
                    <button class="btn btn-warning" onclick="stopDataCollection()">Остановить</button>
                    <button class="btn btn-secondary" onclick="viewData()">Просмотр данных</button>
                </div>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value" id="symbols-tracked">--</div>
                        <div class="metric-label">Символов отслеживается</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="last-update">--</div>
                        <div class="metric-label">Последнее обновление</div>
                    </div>
                </div>
            </div>

            <!-- Strategy Engine Service -->
            <div class="service-card">
                <div class="service-header">
                    <span class="service-title">🧠 Strategy Engine</span>
                    <span class="status-indicator status-healthy" id="strategy-engine-status"></span>
                </div>
                <p>Генерация торговых сигналов и стратегий</p>
                <div class="controls">
                    <button class="btn btn-primary" onclick="analyzeMarket()">Анализ рынка</button>
                    <button class="btn btn-secondary" onclick="viewSignals()">Сигналы</button>
                    <button class="btn btn-warning" onclick="viewStrategies()">Стратегии</button>
                </div>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value" id="active-signals">--</div>
                        <div class="metric-label">Активных сигналов</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="strategies-enabled">--</div>
                        <div class="metric-label">Стратегий включено</div>
                    </div>
                </div>
            </div>

            <!-- Risk Engine Service -->
            <div class="service-card">
                <div class="service-header">
                    <span class="service-title">🛡️ Risk Engine</span>
                    <span class="status-indicator status-healthy" id="risk-engine-status"></span>
                </div>
                <p>Управление рисками и валидация операций</p>
                <div class="controls">
                    <button class="btn btn-secondary" onclick="viewRiskConfig()">Конфигурация</button>
                    <button class="btn btn-warning" onclick="viewAssessments()">Оценки рисков</button>
                    <button class="btn btn-primary" onclick="viewPortfolioMetrics()">Метрики портфеля</button>
                </div>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value" id="portfolio-value">--</div>
                        <div class="metric-label">Стоимость портфеля</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="current-risk">--</div>
                        <div class="metric-label">Текущий риск</div>
                    </div>
                </div>
            </div>

            <!-- Analytics Service -->
            <div class="service-card">
                <div class="service-header">
                    <span class="service-title">📈 Analytics</span>
                    <span class="status-indicator status-healthy" id="analytics-status"></span>
                </div>
                <p>Аналитика и метрики торговой системы</p>
                <div class="controls">
                    <button class="btn btn-primary" onclick="viewPerformance()">Производительность</button>
                    <button class="btn btn-secondary" onclick="viewTradeAnalytics()">Анализ сделок</button>
                </div>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value" id="total-return">--</div>
                        <div class="metric-label">Общая доходность</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="win-rate">--</div>
                        <div class="metric-label">Процент прибыльных</div>
                    </div>
                </div>
            </div>

            <!-- Notifications Service -->
            <div class="service-card">
                <div class="service-header">
                    <span class="service-title">🔔 Notifications</span>
                    <span class="status-indicator status-healthy" id="notifications-status"></span>
                </div>
                <p>Система уведомлений и алертов</p>
                <div class="controls">
                    <button class="btn btn-secondary" onclick="viewNotifications()">Уведомления</button>
                    <button class="btn btn-primary" onclick="testNotification()">Тестовое уведомление</button>
                </div>
                <div class="log-container" id="notifications-log">
                    <div>Загрузка уведомлений...</div>
                </div>
            </div>

            <!-- Portfolio Manager Service -->
            <div class="service-card">
                <div class="service-header">
                    <span class="service-title">💼 Portfolio Manager</span>
                    <span class="status-indicator status-healthy" id="portfolio-manager-status"></span>
                </div>
                <p>Управление портфелем и позициями</p>
                <div class="controls">
                    <button class="btn btn-primary" onclick="viewPortfolio()">Портфель</button>
                    <button class="btn btn-secondary" onclick="viewPositions()">Позиции</button>
                    <button class="btn btn-warning" onclick="updatePrices()">Обновить цены</button>
                </div>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value" id="total-portfolio-value">--</div>
                        <div class="metric-label">Общая стоимость</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="positions-count">--</div>
                        <div class="metric-label">Открытых позиций</div>
                    </div>
                </div>
            </div>

            <!-- AI Engine Service -->
            <div class="service-card">
                <div class="service-header">
                    <span class="service-title">🤖 AI Engine</span>
                    <span class="status-indicator status-healthy" id="ai-engine-status"></span>
                </div>
                <p>Искусственный интеллект и машинное обучение</p>
                <div class="controls">
                    <button class="btn btn-primary" onclick="makePrediction()">Создать прогноз</button>
                    <button class="btn btn-secondary" onclick="analyzeSentiment()">Анализ настроений</button>
                    <button class="btn btn-warning" onclick="viewModels()">AI модели</button>
                </div>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value" id="models-ready">--</div>
                        <div class="metric-label">Моделей готово</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="predictions-count">--</div>
                        <div class="metric-label">Прогнозов создано</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>🚀 Mirai Agent Production System | Powered by FastAPI & Docker | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <script>
            // Update current time
            function updateTime() {{
                document.getElementById('currentTime').textContent = new Date().toLocaleString('ru-RU');
            }}
            updateTime();
            setInterval(updateTime, 1000);

            // API Helper function
            async function apiCall(endpoint, method = 'GET', data = null) {{
                const options = {{
                    method: method,
                    headers: {{
                        'Content-Type': 'application/json',
                    }}
                }};
                
                if (data) {{
                    options.body = JSON.stringify(data);
                }}
                
                try {{
                    const response = await fetch(endpoint, options);
                    return await response.json();
                }} catch (error) {{
                    console.error('API Error:', error);
                    alert('Ошибка связи с сервером: ' + error.message);
                    return null;
                }}
            }}

            // Data Collector functions
            async function startDataCollection() {{
                const result = await apiCall('/api/data-collector/start', 'POST');
                if (result) {{
                    alert('Сбор данных запущен: ' + result.message);
                    loadServiceStatus();
                }}
            }}

            async function stopDataCollection() {{
                const result = await apiCall('/api/data-collector/stop', 'POST');
                if (result) {{
                    alert('Сбор данных остановлен: ' + result.message);
                    loadServiceStatus();
                }}
            }}

            async function viewData() {{
                const result = await apiCall('/api/data-collector/data');
                if (result) {{
                    const dataStr = JSON.stringify(result, null, 2);
                    const newWindow = window.open('', '_blank');
                    newWindow.document.write(`<pre>${{dataStr}}</pre>`);
                }}
            }}

            // Strategy Engine functions
            async function analyzeMarket() {{
                const result = await apiCall('/api/strategy-engine/analyze', 'POST');
                if (result) {{
                    alert(`Анализ завершен. Сигналов создано: ${{result.signals_generated}}`);
                    loadServiceStatus();
                }}
            }}

            async function viewSignals() {{
                const result = await apiCall('/api/strategy-engine/signals');
                if (result) {{
                    const dataStr = JSON.stringify(result, null, 2);
                    const newWindow = window.open('', '_blank');
                    newWindow.document.write(`<pre>${{dataStr}}</pre>`);
                }}
            }}

            async function viewStrategies() {{
                const result = await apiCall('/api/strategy-engine/strategies');
                if (result) {{
                    const dataStr = JSON.stringify(result, null, 2);
                    const newWindow = window.open('', '_blank');
                    newWindow.document.write(`<pre>${{dataStr}}</pre>`);
                }}
            }}

            // Risk Engine functions
            async function viewRiskConfig() {{
                const result = await apiCall('/api/risk-engine/config');
                if (result) {{
                    const dataStr = JSON.stringify(result, null, 2);
                    const newWindow = window.open('', '_blank');
                    newWindow.document.write(`<pre>${{dataStr}}</pre>`);
                }}
            }}

            async function viewAssessments() {{
                const result = await apiCall('/api/risk-engine/assessments');
                if (result) {{
                    const dataStr = JSON.stringify(result, null, 2);
                    const newWindow = window.open('', '_blank');
                    newWindow.document.write(`<pre>${{dataStr}}</pre>`);
                }}
            }}

            async function viewPortfolioMetrics() {{
                const result = await apiCall('/api/risk-engine/portfolio');
                if (result) {{
                    const dataStr = JSON.stringify(result, null, 2);
                    const newWindow = window.open('', '_blank');
                    newWindow.document.write(`<pre>${{dataStr}}</pre>`);
                }}
            }}

            // Analytics functions
            async function viewPerformance() {{
                const result = await apiCall('/api/analytics/performance');
                if (result) {{
                    const dataStr = JSON.stringify(result, null, 2);
                    const newWindow = window.open('', '_blank');
                    newWindow.document.write(`<pre>${{dataStr}}</pre>`);
                }}
            }}

            async function viewTradeAnalytics() {{
                const result = await apiCall('/api/analytics/trades');
                if (result) {{
                    const dataStr = JSON.stringify(result, null, 2);
                    const newWindow = window.open('', '_blank');
                    newWindow.document.write(`<pre>${{dataStr}}</pre>`);
                }}
            }}

            // Notifications functions
            async function viewNotifications() {{
                const result = await apiCall('/api/notifications/notifications');
                if (result) {{
                    const dataStr = JSON.stringify(result, null, 2);
                    const newWindow = window.open('', '_blank');
                    newWindow.document.write(`<pre>${{dataStr}}</pre>`);
                }}
            }}

            async function testNotification() {{
                const result = await apiCall('/api/notifications/notify', 'POST', {{
                    type: 'INFO',
                    title: 'Тестовое уведомление',
                    message: 'Система уведомлений работает корректно',
                    channel: 'web'
                }});
                if (result) {{
                    alert('Тестовое уведомление отправлено');
                    loadNotifications();
                }}
            }}

            // Portfolio Manager functions
            async function viewPortfolio() {{
                const result = await apiCall('/api/portfolio-manager/portfolio');
                if (result) {{
                    const dataStr = JSON.stringify(result, null, 2);
                    const newWindow = window.open('', '_blank');
                    newWindow.document.write(`<pre>${{dataStr}}</pre>`);
                }}
            }}

            async function viewPositions() {{
                const result = await apiCall('/api/portfolio-manager/positions');
                if (result) {{
                    const dataStr = JSON.stringify(result, null, 2);
                    const newWindow = window.open('', '_blank');
                    newWindow.document.write(`<pre>${{dataStr}}</pre>`);
                }}
            }}

            async function updatePrices() {{
                const result = await apiCall('/api/portfolio-manager/positions/update_prices', 'POST');
                if (result) {{
                    alert(`Цены обновлены для ${{result.updated_count}} позиций`);
                    loadServiceStatus();
                }}
            }}

            // AI Engine functions
            async function makePrediction() {{
                const symbol = prompt('Введите символ для прогноза:', 'BTCUSDT');
                if (symbol) {{
                    const result = await apiCall(`/api/ai-engine/predict?symbol=${{symbol}}`, 'POST');
                    if (result) {{
                        alert(`Прогноз для ${{symbol}}: ${{result.direction}} с уверенностью ${{(result.confidence * 100).toFixed(1)}}%`);
                    }}
                }}
            }}

            async function analyzeSentiment() {{
                const result = await apiCall('/api/ai-engine/analyze_sentiment', 'POST');
                if (result) {{
                    alert(`Настроение рынка: ${{result.sentiment}} (уверенность: ${{(result.confidence * 100).toFixed(1)}}%)`);
                }}
            }}

            async function viewModels() {{
                const result = await apiCall('/api/ai-engine/models');
                if (result) {{
                    const dataStr = JSON.stringify(result, null, 2);
                    const newWindow = window.open('', '_blank');
                    newWindow.document.write(`<pre>${{dataStr}}</pre>`);
                }}
            }}

            // Load service status and metrics
            async function loadServiceStatus() {{
                // This function would make multiple API calls to get status from all services
                // For demo purposes, we'll simulate some data updates
                console.log('Loading service status...');
                
                // Simulate some metric updates
                const metricsUpdates = {{
                    'symbols-tracked': Math.floor(Math.random() * 10) + 5,
                    'active-signals': Math.floor(Math.random() * 8) + 2,
                    'strategies-enabled': 2,
                    'portfolio-value': '100,000.00',
                    'current-risk': (Math.random() * 5).toFixed(2) + '%',
                    'total-return': (Math.random() * 20 - 5).toFixed(2) + '%',
                    'win-rate': (50 + Math.random() * 30).toFixed(1) + '%',
                    'total-portfolio-value': '100,000.00',
                    'positions-count': Math.floor(Math.random() * 5),
                    'models-ready': 2,
                    'predictions-count': Math.floor(Math.random() * 10) + 5
                }};
                
                Object.entries(metricsUpdates).forEach(([id, value]) => {{
                    const element = document.getElementById(id);
                    if (element) {{
                        element.textContent = value;
                    }}
                }});
            }}

            async function loadNotifications() {{
                const result = await apiCall('/api/notifications/notifications?limit=5');
                if (result && Array.isArray(result)) {{
                    const logContainer = document.getElementById('notifications-log');
                    logContainer.innerHTML = result.map(notif => 
                        `<div>[${{notif.timestamp}}] ${{notif.type}}: ${{notif.title}}</div>`
                    ).join('') || '<div>Нет уведомлений</div>';
                }}
            }}

            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', function() {{
                loadServiceStatus();
                loadNotifications();
                
                // Auto-refresh every 30 seconds
                setInterval(() => {{
                    loadServiceStatus();
                    loadNotifications();
                }}, 30000);
            }});
        </script>
    </body>
    </html>
    """
    
    return html_content

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "web-panel",
        "timestamp": datetime.now(),
        "environment": os.getenv("ENVIRONMENT", "production")
    }

# System status endpoint
@app.get("/api/system/status")
async def system_status(username: str = Depends(authenticate)):
    """Get overall system status"""
    status_results = {}
    
    for service_name, service_url in MICROSERVICES.items():
        result = await call_microservice(service_name, "/health")
        status_results[service_name] = result
    
    healthy_services = sum(1 for result in status_results.values() if result.get("status") == "healthy")
    
    return {
        "system_status": "HEALTHY" if healthy_services >= 6 else "DEGRADED",
        "healthy_services": healthy_services,
        "total_services": len(MICROSERVICES),
        "services": status_results,
        "timestamp": datetime.now()
    }

# Microservice proxy endpoints
@app.get("/api/{service_name}/{path:path}")
async def proxy_get(service_name: str, path: str, username: str = Depends(authenticate)):
    """Proxy GET requests to microservices"""
    return await call_microservice(service_name, f"/{path}")

@app.post("/api/{service_name}/{path:path}")
async def proxy_post(service_name: str, path: str, request: Request, username: str = Depends(authenticate)):
    """Proxy POST requests to microservices"""
    try:
        data = await request.json()
    except:
        data = None
    
    return await call_microservice(service_name, f"/{path}", "POST", data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
