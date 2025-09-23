"""
Mirai Agent - Веб-панель управления алертами
Интерфейс для мониторинга и управления системой алертов
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import asyncio
import httpx
from datetime import datetime
from typing import Dict, List

app = FastAPI(title="Mirai Alert Dashboard", description="Панель управления алертами")

@app.get("/", response_class=HTMLResponse)
async def alert_dashboard():
    """Главная страница панели алертов"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mirai Agent - Alert Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                color: white;
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1600px;
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
            
            .controls {
                display: flex;
                justify-content: center;
                gap: 15px;
                margin-bottom: 30px;
                flex-wrap: wrap;
            }
            
            .btn {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1em;
                transition: all 0.3s ease;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            
            .btn:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: translateY(-2px);
            }
            
            .btn-danger { background: rgba(231, 76, 60, 0.8); }
            .btn-warning { background: rgba(243, 156, 18, 0.8); }
            .btn-success { background: rgba(46, 204, 113, 0.8); }
            .btn-info { background: rgba(52, 152, 219, 0.8); }
            
            .dashboard-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 30px;
            }
            
            @media (max-width: 1024px) {
                .dashboard-grid {
                    grid-template-columns: 1fr;
                }
            }
            
            .alert-panel {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                padding: 20px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .alert-panel h3 {
                font-size: 1.4em;
                margin-bottom: 20px;
                color: #f1c40f;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .alert-item {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                border-left: 4px solid;
                transition: transform 0.2s ease;
            }
            
            .alert-item:hover {
                transform: translateX(5px);
            }
            
            .alert-item.critical { border-left-color: #e74c3c; }
            .alert-item.warning { border-left-color: #f39c12; }
            .alert-item.info { border-left-color: #3498db; }
            .alert-item.emergency { border-left-color: #8e44ad; animation: pulse 1.5s infinite; }
            
            .alert-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            
            .alert-title {
                font-weight: bold;
                font-size: 1.1em;
            }
            
            .alert-time {
                font-size: 0.9em;
                opacity: 0.8;
            }
            
            .alert-message {
                font-size: 0.95em;
                opacity: 0.9;
                line-height: 1.4;
            }
            
            .alert-meta {
                margin-top: 10px;
                font-size: 0.85em;
                opacity: 0.7;
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .stat-value {
                font-size: 2em;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .stat-label {
                font-size: 0.9em;
                opacity: 0.8;
            }
            
            .rules-list {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
            }
            
            .rule-card {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 8px;
                padding: 15px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .rule-name {
                font-weight: bold;
                margin-bottom: 10px;
                font-size: 1.1em;
            }
            
            .rule-details {
                font-size: 0.9em;
                opacity: 0.8;
                line-height: 1.4;
            }
            
            .status-online { color: #2ecc71; }
            .status-offline { color: #e74c3c; }
            
            .no-alerts {
                text-align: center;
                padding: 40px;
                font-size: 1.1em;
                opacity: 0.7;
            }
            
            .update-info {
                text-align: center;
                margin-top: 20px;
                padding: 15px;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 8px;
                font-size: 0.9em;
                opacity: 0.8;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            
            .loading {
                animation: pulse 1.5s infinite;
            }
            
            .modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
            }
            
            .modal-content {
                background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                margin: 15% auto;
                padding: 20px;
                border-radius: 12px;
                width: 80%;
                max-width: 500px;
                color: white;
            }
            
            .close {
                color: #aaa;
                float: right;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
            }
            
            .close:hover {
                color: white;
            }
            
            .form-group {
                margin-bottom: 15px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            
            .form-group input,
            .form-group select,
            .form-group textarea {
                width: 100%;
                padding: 10px;
                border: none;
                border-radius: 4px;
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            
            .form-group input::placeholder,
            .form-group textarea::placeholder {
                color: rgba(255, 255, 255, 0.6);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 Mirai Alert Center</h1>
                <p>Центр управления системой алертов и уведомлений</p>
            </div>
            
            <div class="controls">
                <button class="btn btn-info" onclick="loadData()">🔄 Обновить</button>
                <button class="btn btn-success" onclick="testAlert()">🧪 Тест алерта</button>
                <button class="btn btn-warning" onclick="openManualAlert()">➕ Создать алерт</button>
                <button class="btn btn-danger" onclick="resolveAllAlerts()">✅ Закрыть все</button>
            </div>
            
            <div id="statsContainer" class="stats-grid">
                <div class="stat-card loading">
                    <div class="stat-value">-</div>
                    <div class="stat-label">Загрузка...</div>
                </div>
            </div>
            
            <div class="dashboard-grid">
                <div class="alert-panel">
                    <h3>🔥 Активные алерты</h3>
                    <div id="activeAlerts" class="loading">
                        <div class="no-alerts">Загрузка активных алертов...</div>
                    </div>
                </div>
                
                <div class="alert-panel">
                    <h3>📋 Правила мониторинга</h3>
                    <div id="alertRules" class="loading">
                        <div class="no-alerts">Загрузка правил...</div>
                    </div>
                </div>
            </div>
            
            <div class="alert-panel">
                <h3>📊 История алертов (24ч)</h3>
                <div id="alertHistory">
                    <div class="no-alerts loading">Загрузка истории...</div>
                </div>
            </div>
            
            <div class="update-info">
                <span id="lastUpdate">Загрузка данных...</span>
                <span id="serviceStatus" class="status-offline">● Проверка соединения...</span>
            </div>
        </div>
        
        <!-- Модальное окно для создания алерта -->
        <div id="manualAlertModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeManualAlert()">&times;</span>
                <h2>Создать алерт вручную</h2>
                <form id="manualAlertForm">
                    <div class="form-group">
                        <label>Заголовок:</label>
                        <input type="text" id="alertTitle" placeholder="Заголовок алерта" required>
                    </div>
                    <div class="form-group">
                        <label>Сообщение:</label>
                        <textarea id="alertMessage" rows="3" placeholder="Описание проблемы" required></textarea>
                    </div>
                    <div class="form-group">
                        <label>Уровень:</label>
                        <select id="alertLevel">
                            <option value="info">Информация</option>
                            <option value="warning" selected>Предупреждение</option>
                            <option value="critical">Критично</option>
                            <option value="emergency">Экстренно</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Тип:</label>
                        <select id="alertType">
                            <option value="system" selected>Система</option>
                            <option value="trading">Торговля</option>
                            <option value="ai">AI</option>
                            <option value="security">Безопасность</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-warning">Создать алерт</button>
                </form>
            </div>
        </div>
        
        <script>
            let alertData = {};
            
            async function loadData() {
                try {
                    // Загружаем все данные параллельно
                    const [activeResponse, historyResponse, rulesResponse, statsResponse] = await Promise.all([
                        fetch('/api/alerts/active'),
                        fetch('/api/alerts/history'),
                        fetch('/api/alerts/rules'),
                        fetch('/api/alerts/stats')
                    ]);
                    
                    const activeAlerts = await activeResponse.json();
                    const alertHistory = await historyResponse.json();
                    const alertRules = await rulesResponse.json();
                    const alertStats = await statsResponse.json();
                    
                    alertData = { activeAlerts, alertHistory, alertRules, alertStats };
                    
                    renderActiveAlerts(activeAlerts);
                    renderAlertHistory(alertHistory);
                    renderAlertRules(alertRules);
                    renderStats(alertStats);
                    
                    document.getElementById('lastUpdate').textContent = 
                        `Обновлено: ${new Date().toLocaleString('ru-RU')}`;
                    document.getElementById('serviceStatus').textContent = '● Подключено';
                    document.getElementById('serviceStatus').className = 'status-online';
                    
                } catch (error) {
                    console.error('Error loading data:', error);
                    document.getElementById('serviceStatus').textContent = '● Ошибка соединения';
                    document.getElementById('serviceStatus').className = 'status-offline';
                }
            }
            
            function renderStats(stats) {
                const container = document.getElementById('statsContainer');
                if (!stats.stats) return;
                
                const s = stats.stats;
                container.innerHTML = `
                    <div class="stat-card">
                        <div class="stat-value">${s.active_alerts}</div>
                        <div class="stat-label">Активные</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${s.alerts_24h}</div>
                        <div class="stat-label">За 24ч</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${s.by_level_24h?.critical || 0}</div>
                        <div class="stat-label">Критичные</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${s.by_level_24h?.warning || 0}</div>
                        <div class="stat-label">Предупреждения</div>
                    </div>
                `;
            }
            
            function renderActiveAlerts(data) {
                const container = document.getElementById('activeAlerts');
                
                if (!data.alerts || data.alerts.length === 0) {
                    container.innerHTML = '<div class="no-alerts">✅ Активных алертов нет</div>';
                    return;
                }
                
                container.innerHTML = data.alerts.map(alert => {
                    const time = new Date(alert.timestamp).toLocaleTimeString('ru-RU');
                    const levelClass = alert.level;
                    
                    return `
                        <div class="alert-item ${levelClass}">
                            <div class="alert-header">
                                <div class="alert-title">${alert.title}</div>
                                <div class="alert-time">${time}</div>
                            </div>
                            <div class="alert-message">${alert.message}</div>
                            <div class="alert-meta">
                                <span>Тип: ${alert.type}</span>
                                <span>Уровень: ${alert.level}</span>
                                <button class="btn" onclick="resolveAlert('${alert.id}')">Закрыть</button>
                            </div>
                        </div>
                    `;
                }).join('');
            }
            
            function renderAlertRules(data) {
                const container = document.getElementById('alertRules');
                
                if (!data.rules || data.rules.length === 0) {
                    container.innerHTML = '<div class="no-alerts">Правила не найдены</div>';
                    return;
                }
                
                container.innerHTML = `
                    <div class="rules-list">
                        ${data.rules.map(rule => `
                            <div class="rule-card">
                                <div class="rule-name">${rule.name}</div>
                                <div class="rule-details">
                                    Тип: ${rule.type}<br>
                                    Уровень: ${rule.level}<br>
                                    Cooldown: ${rule.cooldown}с<br>
                                    ${rule.last_triggered ? 
                                        `Последний: ${new Date(rule.last_triggered).toLocaleString('ru-RU')}` : 
                                        'Не срабатывал'
                                    }
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }
            
            function renderAlertHistory(data) {
                const container = document.getElementById('alertHistory');
                
                if (!data.alerts || data.alerts.length === 0) {
                    container.innerHTML = '<div class="no-alerts">История пуста</div>';
                    return;
                }
                
                // Показываем только последние 10 алертов
                const recentAlerts = data.alerts.slice(0, 10);
                
                container.innerHTML = recentAlerts.map(alert => {
                    const time = new Date(alert.timestamp).toLocaleTimeString('ru-RU');
                    const date = new Date(alert.timestamp).toLocaleDateString('ru-RU');
                    const levelClass = alert.level;
                    
                    return `
                        <div class="alert-item ${levelClass}">
                            <div class="alert-header">
                                <div class="alert-title">${alert.title}</div>
                                <div class="alert-time">${date} ${time}</div>
                            </div>
                            <div class="alert-message">${alert.message}</div>
                            <div class="alert-meta">
                                <span>Тип: ${alert.type}</span>
                                <span>Уровень: ${alert.level}</span>
                                ${alert.resolved ? '<span style="color: #2ecc71;">✅ Закрыт</span>' : ''}
                            </div>
                        </div>
                    `;
                }).join('');
            }
            
            async function testAlert() {
                try {
                    const response = await fetch('/api/alerts/test', { method: 'POST' });
                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        alert('Тестовый алерт отправлен!');
                        setTimeout(loadData, 2000); // Обновляем через 2 секунды
                    } else {
                        alert('Ошибка отправки тестового алерта');
                    }
                } catch (error) {
                    alert('Ошибка: ' + error.message);
                }
            }
            
            async function resolveAlert(alertId) {
                try {
                    const response = await fetch(`/api/alerts/resolve/${alertId}`, { method: 'POST' });
                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        loadData(); // Обновляем данные
                    } else {
                        alert('Ошибка закрытия алерта');
                    }
                } catch (error) {
                    alert('Ошибка: ' + error.message);
                }
            }
            
            async function resolveAllAlerts() {
                if (!confirm('Закрыть все активные алерты?')) return;
                
                const activeAlerts = alertData.activeAlerts?.alerts || [];
                for (const alert of activeAlerts) {
                    await resolveAlert(alert.id);
                }
            }
            
            function openManualAlert() {
                document.getElementById('manualAlertModal').style.display = 'block';
            }
            
            function closeManualAlert() {
                document.getElementById('manualAlertModal').style.display = 'none';
            }
            
            document.getElementById('manualAlertForm').onsubmit = async function(e) {
                e.preventDefault();
                
                const alertData = {
                    title: document.getElementById('alertTitle').value,
                    message: document.getElementById('alertMessage').value,
                    level: document.getElementById('alertLevel').value,
                    alert_type: document.getElementById('alertType').value
                };
                
                try {
                    const response = await fetch('/api/alerts/manual', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(alertData)
                    });
                    
                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        alert('Алерт создан!');
                        closeManualAlert();
                        loadData();
                        document.getElementById('manualAlertForm').reset();
                    } else {
                        alert('Ошибка создания алерта: ' + result.detail);
                    }
                } catch (error) {
                    alert('Ошибка: ' + error.message);
                }
            };
            
            // Автообновление каждые 30 секунд
            setInterval(loadData, 30000);
            
            // Первоначальная загрузка
            loadData();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Proxy endpoints для Alert API
@app.get("/api/alerts/active")
async def proxy_active_alerts():
    """Прокси для активных алертов"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:9998/alerts/active", timeout=10)
            return response.json()
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/alerts/history")
async def proxy_alert_history():
    """Прокси для истории алертов"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:9998/alerts/history", timeout=10)
            return response.json()
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/alerts/rules")
async def proxy_alert_rules():
    """Прокси для правил алертов"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:9998/alerts/rules", timeout=10)
            return response.json()
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/alerts/stats")
async def proxy_alert_stats():
    """Прокси для статистики алертов"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:9998/alerts/stats", timeout=10)
            return response.json()
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/alerts/test")
async def proxy_test_alert():
    """Прокси для тестового алерта"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://localhost:9998/alerts/test", timeout=10)
            return response.json()
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/alerts/resolve/{alert_id}")
async def proxy_resolve_alert(alert_id: str):
    """Прокси для разрешения алерта"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"http://localhost:9998/alerts/resolve/{alert_id}", timeout=10)
            return response.json()
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/alerts/manual")
async def proxy_manual_alert(request: Request):
    """Прокси для создания ручного алерта"""
    try:
        body = await request.json()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:9998/alerts/manual",
                json=body,
                timeout=10
            )
            return response.json()
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/health")
async def health_check():
    """Проверка здоровья веб-панели"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9997)