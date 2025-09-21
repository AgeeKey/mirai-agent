"""
Analytics Microservice - Production Version
"""

from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import redis
import json

app = FastAPI(
    title="Analytics Service",
    description="Аналитика и метрики торговой системы",
    version="1.0.0"
)

# Redis connection
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Models
class PerformanceMetrics(BaseModel):
    total_return: float
    daily_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    timestamp: datetime

class TradeAnalytics(BaseModel):
    symbol: str
    profit_loss: float
    duration_minutes: int
    return_percentage: float
    category: str  # winning/losing

# Cache
performance_history: List[PerformanceMetrics] = []
trade_analytics: List[TradeAnalytics] = []

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "analytics",
        "timestamp": datetime.now()
    }

@app.get("/performance", response_model=PerformanceMetrics)
async def get_performance():
    # Generate demo performance metrics
    import random
    
    metrics = PerformanceMetrics(
        total_return=random.uniform(-5.0, 15.0),
        daily_return=random.uniform(-2.0, 3.0),
        sharpe_ratio=random.uniform(0.5, 2.5),
        max_drawdown=random.uniform(2.0, 8.0),
        win_rate=random.uniform(45.0, 75.0),
        total_trades=random.randint(50, 200),
        timestamp=datetime.now()
    )
    
    performance_history.append(metrics)
    if len(performance_history) > 100:
        performance_history.pop(0)
    
    return metrics

@app.get("/trades", response_model=List[TradeAnalytics])
async def get_trade_analytics():
    return trade_analytics

@app.post("/trades/add")
async def add_trade_analytics(
    symbol: str,
    profit_loss: float,
    duration_minutes: int
):
    return_percentage = (profit_loss / 1000) * 100  # Assuming base of 1000
    category = "winning" if profit_loss > 0 else "losing"
    
    analytics = TradeAnalytics(
        symbol=symbol,
        profit_loss=profit_loss,
        duration_minutes=duration_minutes,
        return_percentage=return_percentage,
        category=category
    )
    
    trade_analytics.append(analytics)
    if len(trade_analytics) > 1000:
        trade_analytics.pop(0)
    
    return {"message": "Trade analytics added", "analytics": analytics}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
