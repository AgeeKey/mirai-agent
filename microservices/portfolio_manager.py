"""
Portfolio Manager Microservice - Production Version
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
    title="Portfolio Manager Service",
    description="Управление портфелем и позициями",
    version="1.0.0"
)

# Redis connection
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Models
class Position(BaseModel):
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    pnl: float
    pnl_percentage: float
    side: str  # LONG, SHORT
    timestamp: datetime

class Portfolio(BaseModel):
    total_value: float
    available_balance: float
    total_pnl: float
    total_pnl_percentage: float
    positions_count: int
    timestamp: datetime

# Cache
positions: Dict[str, Position] = {}
portfolio = Portfolio(
    total_value=100000.0,
    available_balance=80000.0,
    total_pnl=0.0,
    total_pnl_percentage=0.0,
    positions_count=0,
    timestamp=datetime.now()
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "portfolio-manager",
        "timestamp": datetime.now()
    }

@app.get("/portfolio", response_model=Portfolio)
async def get_portfolio():
    # Update portfolio metrics
    global portfolio
    
    total_position_value = sum(pos.quantity * pos.current_price for pos in positions.values())
    total_pnl = sum(pos.pnl for pos in positions.values())
    
    portfolio.total_value = portfolio.available_balance + total_position_value
    portfolio.total_pnl = total_pnl
    portfolio.total_pnl_percentage = (total_pnl / 100000.0) * 100 if total_pnl else 0
    portfolio.positions_count = len(positions)
    portfolio.timestamp = datetime.now()
    
    return portfolio

@app.get("/positions", response_model=List[Position])
async def get_positions():
    return list(positions.values())

@app.get("/positions/{symbol}", response_model=Position)
async def get_position(symbol: str):
    if symbol not in positions:
        raise HTTPException(status_code=404, detail=f"Position for {symbol} not found")
    return positions[symbol]

@app.post("/positions/open")
async def open_position(
    symbol: str,
    quantity: float,
    entry_price: float,
    side: str = "LONG"
):
    # Update current price (demo)
    import random
    current_price = entry_price * random.uniform(0.95, 1.05)
    
    pnl = (current_price - entry_price) * quantity if side == "LONG" else (entry_price - current_price) * quantity
    pnl_percentage = (pnl / (entry_price * quantity)) * 100
    
    position = Position(
        symbol=symbol,
        quantity=quantity,
        entry_price=entry_price,
        current_price=current_price,
        pnl=pnl,
        pnl_percentage=pnl_percentage,
        side=side,
        timestamp=datetime.now()
    )
    
    positions[symbol] = position
    
    # Update available balance
    global portfolio
    portfolio.available_balance -= entry_price * quantity
    
    # Store in Redis
    try:
        redis_client.setex(f"position:{symbol}", 3600, json.dumps(position.dict(), default=str))
    except:
        pass
    
    return {"message": f"Position opened for {symbol}", "position": position}

@app.post("/positions/{symbol}/close")
async def close_position(symbol: str, close_price: Optional[float] = None):
    if symbol not in positions:
        raise HTTPException(status_code=404, detail=f"Position for {symbol} not found")
    
    position = positions[symbol]
    
    if close_price is None:
        close_price = position.current_price
    
    # Calculate final PnL
    final_pnl = (close_price - position.entry_price) * position.quantity if position.side == "LONG" else (position.entry_price - close_price) * position.quantity
    
    # Update available balance
    global portfolio
    portfolio.available_balance += close_price * position.quantity
    
    # Remove position
    del positions[symbol]
    
    # Remove from Redis
    try:
        redis_client.delete(f"position:{symbol}")
    except:
        pass
    
    return {
        "message": f"Position closed for {symbol}",
        "final_pnl": final_pnl,
        "close_price": close_price
    }

@app.post("/positions/update_prices")
async def update_positions_prices():
    """Update current prices for all positions"""
    import random
    
    updated_positions = []
    
    for symbol, position in positions.items():
        # Simulate price movement
        price_change = random.uniform(-0.05, 0.05)  # ±5%
        new_price = position.current_price * (1 + price_change)
        
        # Update position
        position.current_price = new_price
        
        if position.side == "LONG":
            position.pnl = (new_price - position.entry_price) * position.quantity
        else:
            position.pnl = (position.entry_price - new_price) * position.quantity
            
        position.pnl_percentage = (position.pnl / (position.entry_price * position.quantity)) * 100
        
        updated_positions.append(position)
        
        # Update in Redis
        try:
            redis_client.setex(f"position:{symbol}", 3600, json.dumps(position.dict(), default=str))
        except:
            pass
    
    return {
        "message": "Positions updated",
        "updated_count": len(updated_positions),
        "positions": updated_positions
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
