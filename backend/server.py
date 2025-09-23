#!/usr/bin/env python3
"""
Mirai Backend API Server Launcher
Запуск полноценного FastAPI сервера для AI торговой платформы
"""

import uvicorn
import os
import sys

# Добавляем пути для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем все роуты
from main import app
import auth_routes
import trading_routes  
import analytics_routes
import websocket_routes

if __name__ == "__main__":
    print("🚀 Starting Mirai Backend API Server...")
    print("📊 Trading API: http://localhost:8001")
    print("📚 Documentation: http://localhost:8001/docs")
    print("🔌 WebSocket: ws://localhost:8001/ws")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
        access_log=True
    )