#!/usr/bin/env python3
"""
Standalone Portfolio Manager for testing
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mirai Portfolio Manager",
    description="💼 Portfolio Management Service",
    version="2.0.0"
)

class PortfolioRequest(BaseModel):
    portfolio_id: str = "default"

@app.get("/healthz")
async def health_check():
    return {
        "status": "healthy",
        "service": "portfolio_manager",
        "version": "2.0.0", 
        "timestamp": datetime.now().isoformat()
    }

@app.get("/portfolio/{portfolio_id}")
async def get_portfolio(portfolio_id: str = "default"):
    """Get portfolio information"""
    return {
        "portfolio_id": portfolio_id,
        "total_value": 100000.0,
        "daily_pnl": 2.5,
        "positions": [
            {"symbol": "BTCUSDT", "quantity": 1.5, "value": 65000},
            {"symbol": "ETHUSDT", "quantity": 10.0, "value": 35000}
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/portfolio/{portfolio_id}/performance")
async def get_portfolio_performance(portfolio_id: str = "default"):
    """Get portfolio performance metrics"""
    return {
        "portfolio_id": portfolio_id,
        "metrics": {
            "total_return": 15.5,
            "sharpe_ratio": 1.8,
            "max_drawdown": -5.2,
            "win_rate": 0.68
        },
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)