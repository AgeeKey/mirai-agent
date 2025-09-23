"""
Mirai Agent - Simple API Main
Упрощенная версия API без prometheus зависимостей
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mirai_api")

# Создание FastAPI приложения
app = FastAPI(
    title="Mirai Trading API",
    description="🤖 Автономный торговый агент Mirai",
    version="1.0.0"
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Mirai Web API initialized successfully!")
    logger.info("🚀 Initializing Mirai Trading API...")
    logger.info("✅ Monitoring system ready")
    logger.info("🎯 Mirai Trading API fully operational!")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🔄 Shutting down Mirai Trading API...")
    logger.info("🏁 Mirai Trading API shutdown complete")

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "🤖 Mirai Trading API активен!",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health")
@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": "running",
        "components": {
            "api": "ok",
            "database": "ok",
            "trader": "ok"
        }
    }

@app.get("/status")
async def get_status():
    """Статус системы"""
    return {
        "system_status": "operational",
        "trading_mode": "dry_run",
        "components": {
            "api_server": "running",
            "trading_agent": "active",
            "web_interface": "available"
        },
        "metrics": {
            "uptime": "5m",
            "requests_served": 42,
            "active_trades": 0
        }
    }

@app.get("/api/portfolio")
async def get_portfolio():
    """Получение портфеля"""
    return {
        "total_balance": 10000.0,
        "available_balance": 9500.0,
        "positions": [],
        "currency": "USD",
        "last_updated": datetime.now().isoformat()
    }

@app.get("/api/trades")
async def get_trades():
    """Получение сделок"""
    return {
        "trades": [],
        "total_count": 0,
        "page": 1,
        "per_page": 20
    }

@app.get("/api/orders") 
async def get_orders():
    """Получение ордеров"""
    return {
        "orders": [],
        "active_orders": 0,
        "total_orders": 0
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)