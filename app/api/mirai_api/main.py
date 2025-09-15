from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import asyncio
from datetime import datetime
import random
from typing import List
import sqlite3
import os

app = FastAPI(title="Mirai Trading API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                self.active_connections.remove(connection)

manager = ConnectionManager()

def get_db_connection():
    """Get database connection"""
    db_path = "/workspaces/mirai-agent/state/mirai.db"
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    return None

@app.get("/")
async def root():
    return {"message": "🤖 Mirai Trading API активен!", "status": "running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/trading/status")
async def get_trading_status():
    """Получить текущий статус торговли"""
    return {
        "is_active": True,
        "mode": "simulation",
        "balance": {
            "total": 10450.75,
            "available": 9200.30,
            "used": 1250.45
        },
        "daily_pnl": 450.75,
        "win_rate": 68.4,
        "risk_level": "medium",
        "ai_confidence": 0.85,
        "strategies": {
            "momentum_breakout": {"status": "active", "win_rate": 72},
            "mean_reversion": {"status": "standby", "win_rate": 65},
            "grid_trading": {"status": "paused", "win_rate": 58}
        }
    }

@app.get("/api/trading/performance")
async def get_performance_data():
    """Получить данные производительности"""
    # Генерируем симуляцию данных
    data = []
    base_equity = 10000
    pnl = 0
    
    for i in range(24):  # 24 часа
        pnl_change = random.uniform(-50, 100)
        pnl += pnl_change
        equity = base_equity + pnl
        
        hour = f"{i:02d}:00"
        data.append({
            "time": hour,
            "pnl": round(pnl, 2),
            "equity": round(equity, 2),
            "trades": random.randint(0, 3)
        })
    
    return {"performance": data}

@app.get("/api/trading/trades")
async def get_recent_trades():
    """Получить последние сделки"""
    # Симуляция последних сделок
    trades = [
        {
            "id": 1,
            "symbol": "BTCUSDT",
            "action": "BUY",
            "price": 58450.00,
            "quantity": 0.1,
            "pnl": 125.50,
            "timestamp": "2024-01-15T14:32:00Z",
            "strategy": "momentum_breakout"
        },
        {
            "id": 2,
            "symbol": "ETHUSDT",
            "action": "SELL",
            "price": 3250.00,
            "quantity": 1.5,
            "pnl": -50.25,
            "timestamp": "2024-01-15T14:15:00Z",
            "strategy": "mean_reversion"
        },
        {
            "id": 3,
            "symbol": "BTCUSDT",
            "action": "BUY",
            "price": 58200.00,
            "quantity": 0.15,
            "pnl": 200.75,
            "timestamp": "2024-01-15T13:45:00Z",
            "strategy": "momentum_breakout"
        }
    ]
    
    return {"trades": trades}

@app.get("/api/trading/risk")
async def get_risk_metrics():
    """Получить метрики риска"""
    return {
        "daily_trades_used": 3,
        "daily_trades_limit": 6,
        "max_drawdown": 2.5,
        "var_95": 150.0,
        "sharpe_ratio": 1.8,
        "risk_score": 0.4,
        "position_size": 0.02,
        "stop_loss": 1.5,
        "take_profit": 3.0
    }

@app.websocket("/ws/trading")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для обновлений в реальном времени"""
    await manager.connect(websocket)
    try:
        while True:
            # Отправляем обновления каждые 5 секунд
            update_data = {
                "type": "price_update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "BTCUSDT": round(58000 + random.uniform(-500, 500), 2),
                    "ETHUSDT": round(3200 + random.uniform(-100, 100), 2),
                    "current_pnl": round(450 + random.uniform(-50, 50), 2),
                    "ai_confidence": round(0.8 + random.uniform(-0.1, 0.1), 2)
                }
            }
            
            await manager.send_personal_message(json.dumps(update_data), websocket)
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    print("🚀 Запуск Mirai Trading API...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        log_level="info"
    )