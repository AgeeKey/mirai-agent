"""
Portfolio Manager Microservice - Advanced Portfolio Management with AI
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncio
import logging
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import redis
import aiohttp
from scipy.optimize import minimize
try:
    import cvxpy as cp
except ImportError:
    cp = None
    logging.warning("cvxpy not available - portfolio optimization will use simplified methods")
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mirai Portfolio Manager",
    description="🎯 Advanced Portfolio Management with Auto-Rebalancing and Risk Optimization",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        decode_responses=True,
        socket_timeout=5
    )
    redis_client.ping()
    logger.info("✅ Redis connection established")
except Exception as e:
    logger.warning(f"⚠️ Redis connection failed: {e}")
    redis_client = None

# Enhanced Data Models
class Asset(BaseModel):
    symbol: str = Field(..., description="Asset symbol")
    name: str = Field(..., description="Asset name")
    current_price: float = Field(..., gt=0, description="Current price")
    quantity: float = Field(..., ge=0, description="Quantity held")
    target_allocation: float = Field(..., ge=0, le=1, description="Target allocation percentage")
    current_allocation: float = Field(..., ge=0, le=1, description="Current allocation percentage")
    asset_class: str = Field(..., description="Asset class (crypto, stocks, bonds, etc.)")
    risk_score: float = Field(..., ge=0, le=1, description="Risk score 0-1")
    expected_return: float = Field(..., description="Expected annual return")
    volatility: float = Field(..., ge=0, description="Volatility measure")

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
    id: str = Field(..., description="Portfolio ID")
    name: str = Field(..., description="Portfolio name")
    user_id: str = Field(..., description="Owner user ID")
    total_value: float = Field(..., ge=0, description="Total portfolio value")
    cash_balance: float = Field(..., ge=0, description="Available cash")
    assets: List[Asset] = Field(default_factory=list, description="Portfolio assets")
    risk_tolerance: str = Field(..., description="CONSERVATIVE, MODERATE, AGGRESSIVE")
    rebalance_threshold: float = Field(default=0.05, description="Rebalancing threshold")
    auto_rebalance: bool = Field(default=True, description="Auto-rebalancing enabled")
    created_at: datetime = Field(default_factory=datetime.now)
    last_rebalanced: Optional[datetime] = None

class RebalanceAction(BaseModel):
    asset_symbol: str
    action: str = Field(..., description="BUY, SELL")
    quantity: float = Field(..., gt=0)
    estimated_cost: float = Field(..., gt=0)
    priority: int = Field(..., ge=1, le=10, description="Execution priority")
    reasoning: str = Field(..., description="Why this action is recommended")

class RebalancePlan(BaseModel):
    portfolio_id: str
    total_deviation: float = Field(..., description="Total allocation deviation")
    estimated_cost: float = Field(..., description="Estimated rebalancing cost")
    actions: List[RebalanceAction] = Field(default_factory=list)
    risk_reduction: float = Field(..., description="Expected risk reduction")
    expected_return_impact: float = Field(..., description="Impact on expected returns")
    execution_time_estimate: str = Field(..., description="Estimated execution time")
    created_at: datetime = Field(default_factory=datetime.now)

# Cache and state
positions: Dict[str, Position] = {}
legacy_portfolio = Portfolio(
    id="legacy",
    name="Legacy Portfolio",
    user_id="system",
    total_value=100000.0,
    cash_balance=80000.0,
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
