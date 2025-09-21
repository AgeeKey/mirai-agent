"""
Strategy Engine Microservice - Production Version
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
import httpx

app = FastAPI(
    title="Strategy Engine Service",
    description="Генерация торговых сигналов и стратегий",
    version="1.0.0"
)

# Redis connection
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Models
class TradingSignal(BaseModel):
    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    price: float
    quantity: float
    timestamp: datetime
    strategy: str

class StrategyConfig(BaseModel):
    name: str
    enabled: bool
    parameters: dict
    risk_level: str

class HealthCheck(BaseModel):
    status: str
    service: str
    timestamp: datetime
    data_collector_connected: bool

# Cache
active_signals: Dict[str, TradingSignal] = {}
strategies: Dict[str, StrategyConfig] = {
    "ma_crossover": StrategyConfig(
        name="MA Crossover",
        enabled=True,
        parameters={"fast_period": 10, "slow_period": 20},
        risk_level="medium"
    ),
    "rsi_oversold": StrategyConfig(
        name="RSI Oversold",
        enabled=True,
        parameters={"rsi_period": 14, "oversold_level": 30},
        risk_level="low"
    )
}

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check with data collector connectivity"""
    data_collector_connected = True
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://data-collector:8001/health", timeout=5.0)
            data_collector_connected = response.status_code == 200
    except:
        data_collector_connected = False
    
    return HealthCheck(
        status="healthy" if data_collector_connected else "degraded",
        service="strategy-engine",
        timestamp=datetime.now(),
        data_collector_connected=data_collector_connected
    )

@app.get("/status")
async def get_status():
    return {
        "active_signals": len(active_signals),
        "strategies_enabled": len([s for s in strategies.values() if s.enabled]),
        "last_signal": max([signal.timestamp for signal in active_signals.values()]) if active_signals else None,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/signals", response_model=List[TradingSignal])
async def get_signals():
    return list(active_signals.values())

@app.get("/signals/{symbol}", response_model=TradingSignal)
async def get_signal(symbol: str):
    if symbol not in active_signals:
        raise HTTPException(status_code=404, detail=f"No active signal for {symbol}")
    return active_signals[symbol]

@app.get("/strategies", response_model=List[StrategyConfig])
async def get_strategies():
    return list(strategies.values())

@app.post("/analyze")
async def analyze_market():
    """Анализ рынка и генерация сигналов"""
    try:
        # Get market data from data collector
        async with httpx.AsyncClient() as client:
            response = await client.get("http://data-collector:8001/data", timeout=10.0)
            if response.status_code != 200:
                raise HTTPException(status_code=503, detail="Data collector unavailable")
            
            market_data = response.json()
        
        # Generate signals for each symbol
        signals_generated = []
        import random
        
        for data in market_data:
            symbol = data["symbol"]
            price = data["price"]
            
            # Simple strategy logic (demo)
            confidence = random.uniform(0.6, 0.95)
            action = random.choice(["BUY", "SELL", "HOLD"])
            quantity = random.uniform(0.1, 1.0)
            
            signal = TradingSignal(
                symbol=symbol,
                action=action,
                confidence=confidence,
                price=price,
                quantity=quantity,
                timestamp=datetime.now(),
                strategy="ma_crossover"
            )
            
            active_signals[symbol] = signal
            signals_generated.append(signal)
            
            # Store in Redis
            try:
                redis_client.setex(f"signal:{symbol}", 3600, json.dumps(signal.dict(), default=str))
            except:
                pass
        
        return {
            "message": "Market analysis completed",
            "signals_generated": len(signals_generated),
            "signals": signals_generated
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/strategies/{strategy_name}/toggle")
async def toggle_strategy(strategy_name: str):
    if strategy_name not in strategies:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    strategies[strategy_name].enabled = not strategies[strategy_name].enabled
    return {"message": f"Strategy {strategy_name} {'enabled' if strategies[strategy_name].enabled else 'disabled'}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
