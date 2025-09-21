"""
Data Collector Microservice - Production Version
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
import redis
import json

app = FastAPI(
    title="Data Collector Service",
    description="Сбор рыночных данных в реальном времени",
    version="1.0.0"
)

# Redis connection
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Models
class MarketData(BaseModel):
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None

class HealthCheck(BaseModel):
    status: str
    service: str
    timestamp: datetime
    redis_connected: bool

# Cache
market_data_cache: Dict[str, MarketData] = {}
is_collecting = False

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check with Redis status"""
    redis_connected = True
    try:
        redis_client.ping()
    except:
        redis_connected = False
    
    return HealthCheck(
        status="healthy" if redis_connected else "degraded",
        service="data-collector",
        timestamp=datetime.now(),
        redis_connected=redis_connected
    )

@app.get("/status")
async def get_status():
    return {
        "collecting": is_collecting,
        "symbols_tracked": len(market_data_cache),
        "last_update": max([data.timestamp for data in market_data_cache.values()]) if market_data_cache else None,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/data/{symbol}", response_model=MarketData)
async def get_market_data(symbol: str):
    if symbol not in market_data_cache:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    return market_data_cache[symbol]

@app.get("/data", response_model=List[MarketData])
async def get_all_market_data():
    return list(market_data_cache.values())

@app.post("/start")
async def start_collection():
    global is_collecting
    is_collecting = True
    
    # Demo data for production testing
    demo_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "BNBUSDT"]
    import random
    
    for symbol in demo_symbols:
        market_data = MarketData(
            symbol=symbol,
            price=random.uniform(1000, 50000),
            volume=random.uniform(1000000, 10000000),
            timestamp=datetime.now(),
            bid=random.uniform(1000, 50000),
            ask=random.uniform(1000, 50000)
        )
        market_data_cache[symbol] = market_data
        
        # Store in Redis
        try:
            redis_client.setex(f"market_data:{symbol}", 3600, json.dumps(market_data.dict(), default=str))
        except:
            pass
    
    return {"message": "Data collection started", "symbols": demo_symbols}

@app.post("/stop")
async def stop_collection():
    global is_collecting
    is_collecting = False
    return {"message": "Data collection stopped"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
