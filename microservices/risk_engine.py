"""
Risk Engine Microservice - Production Version
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
    title="Risk Engine Service",
    description="Управление рисками и валидация торговых операций",
    version="1.0.0"
)

# Redis connection
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Models
class RiskAssessment(BaseModel):
    symbol: str
    approved: bool
    risk_score: float
    max_position_size: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: str
    timestamp: datetime

class RiskConfig(BaseModel):
    max_portfolio_risk: float = 0.02
    max_position_risk: float = 0.01
    max_daily_loss: float = 0.05
    max_drawdown: float = 0.10
    enabled: bool = True

class PortfolioMetrics(BaseModel):
    total_value: float
    daily_pnl: float
    drawdown: float
    risk_exposure: float
    positions_count: int

# Cache
risk_assessments: Dict[str, RiskAssessment] = {}
risk_config = RiskConfig()
portfolio_metrics = PortfolioMetrics(
    total_value=100000.0,
    daily_pnl=0.0,
    drawdown=0.0,
    risk_exposure=0.0,
    positions_count=0
)

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "risk-engine",
        "timestamp": datetime.now(),
        "risk_enabled": risk_config.enabled
    }

@app.get("/status")
async def get_status():
    return {
        "risk_enabled": risk_config.enabled,
        "assessments_count": len(risk_assessments),
        "portfolio_value": portfolio_metrics.total_value,
        "current_risk": portfolio_metrics.risk_exposure,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/config", response_model=RiskConfig)
async def get_risk_config():
    return risk_config

@app.post("/config")
async def update_risk_config(config: RiskConfig):
    global risk_config
    risk_config = config
    return {"message": "Risk configuration updated"}

@app.get("/portfolio", response_model=PortfolioMetrics)
async def get_portfolio_metrics():
    return portfolio_metrics

@app.post("/assess")
async def assess_trading_signal(symbol: str, action: str, quantity: float, price: float):
    """Оценка торгового сигнала на предмет рисков"""
    
    if not risk_config.enabled:
        assessment = RiskAssessment(
            symbol=symbol,
            approved=True,
            risk_score=0.0,
            max_position_size=quantity,
            reason="Risk management disabled",
            timestamp=datetime.now()
        )
        risk_assessments[symbol] = assessment
        return assessment
    
    # Calculate risk metrics
    position_value = quantity * price
    position_risk = position_value / portfolio_metrics.total_value
    
    # Risk assessment logic
    risk_score = min(position_risk / risk_config.max_position_risk, 1.0)
    
    # Check portfolio limits
    approved = True
    reason = "Approved"
    
    if position_risk > risk_config.max_position_risk:
        approved = False
        reason = f"Position risk {position_risk:.2%} exceeds limit {risk_config.max_position_risk:.2%}"
    elif portfolio_metrics.risk_exposure + position_risk > risk_config.max_portfolio_risk:
        approved = False
        reason = f"Portfolio risk would exceed limit {risk_config.max_portfolio_risk:.2%}"
    elif portfolio_metrics.drawdown > risk_config.max_drawdown:
        approved = False
        reason = f"Maximum drawdown {risk_config.max_drawdown:.2%} exceeded"
    
    # Calculate stop loss and take profit
    stop_loss = None
    take_profit = None
    
    if action == "BUY":
        stop_loss = price * 0.98  # 2% stop loss
        take_profit = price * 1.04  # 4% take profit
    elif action == "SELL":
        stop_loss = price * 1.02
        take_profit = price * 0.96
    
    # Adjust position size if needed
    max_position_size = quantity
    if approved and position_risk > risk_config.max_position_risk * 0.8:
        max_position_size = quantity * 0.5  # Reduce position size
    
    assessment = RiskAssessment(
        symbol=symbol,
        approved=approved,
        risk_score=risk_score,
        max_position_size=max_position_size,
        stop_loss=stop_loss,
        take_profit=take_profit,
        reason=reason,
        timestamp=datetime.now()
    )
    
    risk_assessments[symbol] = assessment
    
    # Store in Redis
    try:
        redis_client.setex(f"risk_assessment:{symbol}", 3600, json.dumps(assessment.dict(), default=str))
    except:
        pass
    
    return assessment

@app.get("/assessments", response_model=List[RiskAssessment])
async def get_assessments():
    return list(risk_assessments.values())

@app.get("/assessments/{symbol}", response_model=RiskAssessment)
async def get_assessment(symbol: str):
    if symbol not in risk_assessments:
        raise HTTPException(status_code=404, detail=f"No assessment found for {symbol}")
    return risk_assessments[symbol]

@app.post("/portfolio/update")
async def update_portfolio_metrics(
    total_value: float,
    daily_pnl: float,
    positions_count: int
):
    """Обновление метрик портфеля"""
    global portfolio_metrics
    
    # Calculate drawdown
    if daily_pnl < 0:
        portfolio_metrics.drawdown = abs(daily_pnl) / total_value
    else:
        portfolio_metrics.drawdown = max(0, portfolio_metrics.drawdown * 0.9)  # Recovery
    
    # Calculate risk exposure (simplified)
    portfolio_metrics.risk_exposure = positions_count * 0.01  # 1% per position
    
    portfolio_metrics.total_value = total_value
    portfolio_metrics.daily_pnl = daily_pnl
    portfolio_metrics.positions_count = positions_count
    
    return {"message": "Portfolio metrics updated", "metrics": portfolio_metrics}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
