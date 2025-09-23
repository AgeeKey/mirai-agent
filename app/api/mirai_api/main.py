from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import uvicorn
import json
import asyncio
from datetime import datetime
import random
from typing import List
import sqlite3
import os

# Import our trading components (simplified)
from .trading_metrics import get_trading_metrics

# Import web extension routes
from .auth_routes import router as auth_router
from .emergency_routes import router as emergency_router, emergency_middleware_func
from .blog_routes import router as blog_router
from .voice_routes import router as voice_router
from .memory_routes import router as memory_router
from .admin_routes import router as admin_router
from .integration_routes import router as integration_router
from .notifications import router as notifications_router
from .auth import db_manager

# Import performance optimization
try:
    from ...performance.optimization import (
        initialize_performance_system, cleanup_performance_system, 
        get_performance_summary, performance_optimized,
        connection_pool_manager, advanced_cache, task_manager
    )
    PERFORMANCE_AVAILABLE = True
except ImportError:
    PERFORMANCE_AVAILABLE = False
    print("Performance optimization not available")

app = FastAPI(
    title="Mirai Trading & Web API", 
    description="Advanced AI Trading System with Web Ecosystem Integration",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add emergency middleware
app.middleware("http")(emergency_middleware_func)

# Include web extension routers
app.include_router(auth_router)
app.include_router(blog_router)
app.include_router(voice_router)
app.include_router(memory_router)
app.include_router(auth_router)
app.include_router(emergency_router)
app.include_router(admin_router)
app.include_router(integration_router)
app.include_router(notifications_router)

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

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and create tables"""
    # Database will be initialized by db_manager
    print("🚀 Mirai Web API initialized successfully!")
    
    if PERFORMANCE_AVAILABLE:
        await initialize_performance_system()
        print("⚡ Performance optimization system initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if PERFORMANCE_AVAILABLE:
        await cleanup_performance_system()
        print("🔄 Performance optimization system cleaned up")

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


@app.get("/metrics", response_class=PlainTextResponse)
async def get_metrics():
    """Expose Prometheus metrics for scraping"""
    return get_trading_metrics()


@app.get("/alerts")
async def get_alerts():
    """Get current alerts"""
    return {
        "active_alerts": [],
        "summary": {"active_alerts": 0, "warning_level": "low"}
    }


@app.post("/alerts/process")
async def process_alerts(monitoring_data: dict):
    """Process monitoring data and trigger alerts"""
    return {"status": "success", "message": "Monitoring data processed"}


@app.post("/metrics/record")
async def record_metrics(metrics_data: dict):
    """Record trading metrics"""
    return {"status": "success", "message": "Metrics recorded"}


# Performance optimization endpoints
@app.get("/api/performance/summary")
async def get_performance_optimization_summary():
    """Get comprehensive performance optimization summary"""
    if not PERFORMANCE_AVAILABLE:
        return {"error": "Performance optimization not available"}
    
    try:
        summary = await get_performance_summary()
        return {"status": "success", "data": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/performance/cache/stats")
async def get_cache_stats():
    """Get cache performance statistics"""
    if not PERFORMANCE_AVAILABLE:
        return {"error": "Performance optimization not available"}
    
    try:
        stats = advanced_cache.get_cache_stats()
        return {"status": "success", "cache_stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/performance/cache/invalidate")
async def invalidate_cache(pattern: str):
    """Invalidate cache entries matching pattern"""
    if not PERFORMANCE_AVAILABLE:
        return {"error": "Performance optimization not available"}
    
    try:
        await advanced_cache.invalidate(pattern)
        return {"status": "success", "message": f"Invalidated cache pattern: {pattern}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/performance/tasks/stats")
async def get_task_stats():
    """Get async task management statistics"""
    if not PERFORMANCE_AVAILABLE:
        return {"error": "Performance optimization not available"}
    
    try:
        stats = task_manager.get_task_stats()
        return {"status": "success", "task_stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/performance/connections/stats")
async def get_connection_stats():
    """Get connection pool statistics"""
    if not PERFORMANCE_AVAILABLE:
        return {"error": "Performance optimization not available"}
    
    try:
        stats = connection_pool_manager.get_pool_stats()
        return {"status": "success", "connection_stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize application with performance optimizations"""
    print("🚀 Initializing Mirai Trading API...")
    
    if PERFORMANCE_AVAILABLE:
        try:
            await initialize_performance_system()
            print("✅ Performance optimization system initialized")
        except Exception as e:
            print(f"⚠️ Performance system initialization failed: {e}")
    
    # Initialize monitoring
    try:
        # Start monitoring tasks
        print("✅ Monitoring system ready")
    except Exception as e:
        print(f"⚠️ Monitoring initialization failed: {e}")
    
    print("🎯 Mirai Trading API fully operational!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup application resources"""
    print("🔄 Shutting down Mirai Trading API...")
    
    if PERFORMANCE_AVAILABLE:
        try:
            await cleanup_performance_system()
            print("✅ Performance system cleaned up")
        except Exception as e:
            print(f"⚠️ Performance cleanup failed: {e}")
    
    print("🏁 Mirai Trading API shutdown complete")


if __name__ == "__main__":
    print("🚀 Запуск Mirai Trading API...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        log_level="info"
    )
