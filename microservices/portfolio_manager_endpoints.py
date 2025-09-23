"""
Portfolio Manager Endpoints - Advanced Portfolio Management API
"""

from fastapi import HTTPException, BackgroundTasks, Query, Depends
from fastapi.responses import JSONResponse
import asyncio
import logging
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict

# Import from portfolio_manager.py
from portfolio_manager import (
    app, redis_client, Asset, Portfolio, Position, RebalanceAction, 
    RebalancePlan, positions, legacy_portfolio, logger
)

# Portfolio Management Engine
class PortfolioEngine:
    def __init__(self):
        self.portfolios: Dict[str, Portfolio] = {"legacy": legacy_portfolio}
        self.price_cache: Dict[str, float] = {}
        
    async def create_portfolio(self, portfolio_data: Dict) -> Portfolio:
        """Create a new portfolio"""
        try:
            portfolio = Portfolio(**portfolio_data)
            self.portfolios[portfolio.id] = portfolio
            
            # Cache in Redis
            if redis_client:
                redis_client.setex(
                    f"portfolio:{portfolio.id}",
                    3600,
                    json.dumps(portfolio.dict(), default=str)
                )
            
            logger.info(f"✅ Created portfolio {portfolio.id}")
            return portfolio
            
        except Exception as e:
            logger.error(f"❌ Portfolio creation failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def update_portfolio_prices(self, portfolio_id: str) -> Portfolio:
        """Update portfolio with current market prices"""
        try:
            portfolio = self.portfolios.get(portfolio_id)
            if not portfolio:
                raise HTTPException(status_code=404, detail="Portfolio not found")
            
            total_value = portfolio.cash_balance
            
            for asset in portfolio.assets:
                # Simulate price updates (replace with real market data)
                new_price = asset.current_price * (1 + np.random.normal(0, 0.02))
                asset.current_price = max(0.01, new_price)  # Prevent negative prices
                
                asset_value = asset.quantity * asset.current_price
                total_value += asset_value
            
            # Recalculate allocations
            for asset in portfolio.assets:
                asset_value = asset.quantity * asset.current_price
                asset.current_allocation = asset_value / total_value if total_value > 0 else 0
            
            portfolio.total_value = total_value
            return portfolio
            
        except Exception as e:
            logger.error(f"❌ Price update failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def calculate_rebalance_plan(self, portfolio_id: str) -> RebalancePlan:
        """Calculate optimal rebalancing plan"""
        try:
            portfolio = self.portfolios.get(portfolio_id)
            if not portfolio:
                raise HTTPException(status_code=404, detail="Portfolio not found")
            
            # Update prices first
            portfolio = await self.update_portfolio_prices(portfolio_id)
            
            actions = []
            total_deviation = 0
            estimated_cost = 0
            
            for asset in portfolio.assets:
                deviation = abs(asset.current_allocation - asset.target_allocation)
                total_deviation += deviation
                
                if deviation > portfolio.rebalance_threshold:
                    if asset.current_allocation > asset.target_allocation:
                        # Need to sell
                        excess_value = (asset.current_allocation - asset.target_allocation) * portfolio.total_value
                        quantity_to_sell = excess_value / asset.current_price
                        
                        action = RebalanceAction(
                            asset_symbol=asset.symbol,
                            action="SELL",
                            quantity=quantity_to_sell,
                            estimated_cost=quantity_to_sell * asset.current_price * 0.001,  # 0.1% fee
                            priority=int(deviation * 10),
                            reasoning=f"Reduce {asset.symbol} allocation from {asset.current_allocation:.2%} to {asset.target_allocation:.2%}"
                        )
                        actions.append(action)
                        estimated_cost += action.estimated_cost
                        
                    else:
                        # Need to buy
                        needed_value = (asset.target_allocation - asset.current_allocation) * portfolio.total_value
                        quantity_to_buy = needed_value / asset.current_price
                        
                        action = RebalanceAction(
                            asset_symbol=asset.symbol,
                            action="BUY",
                            quantity=quantity_to_buy,
                            estimated_cost=quantity_to_buy * asset.current_price * 0.001,
                            priority=int(deviation * 10),
                            reasoning=f"Increase {asset.symbol} allocation from {asset.current_allocation:.2%} to {asset.target_allocation:.2%}"
                        )
                        actions.append(action)
                        estimated_cost += action.estimated_cost
            
            # Sort actions by priority
            actions.sort(key=lambda x: x.priority, reverse=True)
            
            # Calculate expected impact
            risk_reduction = min(0.2, total_deviation * 0.5)  # Simplified calculation
            return_impact = -estimated_cost / portfolio.total_value  # Cost impact on returns
            
            return RebalancePlan(
                portfolio_id=portfolio_id,
                total_deviation=total_deviation,
                estimated_cost=estimated_cost,
                actions=actions,
                risk_reduction=risk_reduction,
                expected_return_impact=return_impact,
                execution_time_estimate=f"{len(actions) * 2} minutes"
            )
            
        except Exception as e:
            logger.error(f"❌ Rebalance planning failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Initialize engine
portfolio_engine = PortfolioEngine()

# API Endpoints
@app.post("/portfolio/create", response_model=Portfolio)
async def create_portfolio(portfolio_data: Dict[str, Any]):
    """🎯 Create a new portfolio with advanced features"""
    try:
        return await portfolio_engine.create_portfolio(portfolio_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio/{portfolio_id}", response_model=Portfolio)
async def get_portfolio(portfolio_id: str):
    """📊 Get portfolio details with current allocations"""
    try:
        portfolio = portfolio_engine.portfolios.get(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Update with current prices
        return await portfolio_engine.update_portfolio_prices(portfolio_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio/{portfolio_id}/rebalance-plan", response_model=RebalancePlan)
async def get_rebalance_plan(portfolio_id: str):
    """⚖️ Calculate optimal rebalancing plan"""
    try:
        return await portfolio_engine.calculate_rebalance_plan(portfolio_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio/{portfolio_id}/rebalance")
async def execute_rebalance(portfolio_id: str, background_tasks: BackgroundTasks):
    """🔄 Execute portfolio rebalancing"""
    try:
        plan = await portfolio_engine.calculate_rebalance_plan(portfolio_id)
        
        # Add rebalancing to background tasks
        background_tasks.add_task(execute_rebalance_background, portfolio_id, plan)
        
        return {
            "message": "Rebalancing started",
            "portfolio_id": portfolio_id,
            "planned_actions": len(plan.actions),
            "estimated_cost": plan.estimated_cost,
            "execution_time": plan.execution_time_estimate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def execute_rebalance_background(portfolio_id: str, plan: RebalancePlan):
    """Background task for executing rebalancing"""
    try:
        portfolio = portfolio_engine.portfolios.get(portfolio_id)
        if not portfolio:
            return
        
        executed_actions = []
        total_cost = 0
        
        for action in plan.actions:
            # Find the asset
            asset = next((a for a in portfolio.assets if a.symbol == action.asset_symbol), None)
            if not asset:
                continue
            
            if action.action == "SELL":
                if asset.quantity >= action.quantity:
                    asset.quantity -= action.quantity
                    portfolio.cash_balance += action.quantity * asset.current_price * 0.999  # After fees
                    executed_actions.append(action)
                    total_cost += action.estimated_cost
            
            elif action.action == "BUY":
                cost = action.quantity * asset.current_price * 1.001  # Including fees
                if portfolio.cash_balance >= cost:
                    asset.quantity += action.quantity
                    portfolio.cash_balance -= cost
                    executed_actions.append(action)
                    total_cost += action.estimated_cost
        
        # Recalculate allocations
        await portfolio_engine.update_portfolio_prices(portfolio_id)
        portfolio.last_rebalanced = datetime.now()
        
        logger.info(f"✅ Rebalanced portfolio {portfolio_id}: {len(executed_actions)}/{len(plan.actions)} actions")
        
    except Exception as e:
        logger.error(f"❌ Background rebalance failed: {e}")

@app.post("/portfolio/{portfolio_id}/asset")
async def add_asset_to_portfolio(portfolio_id: str, asset: Asset):
    """➕ Add new asset to portfolio"""
    try:
        portfolio = portfolio_engine.portfolios.get(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Check if asset already exists
        existing_asset = next((a for a in portfolio.assets if a.symbol == asset.symbol), None)
        if existing_asset:
            raise HTTPException(status_code=400, detail="Asset already exists in portfolio")
        
        portfolio.assets.append(asset)
        await portfolio_engine.update_portfolio_prices(portfolio_id)
        
        return {"message": f"Asset {asset.symbol} added to portfolio", "portfolio_id": portfolio_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/portfolio/{portfolio_id}/asset/{symbol}")
async def remove_asset_from_portfolio(portfolio_id: str, symbol: str):
    """➖ Remove asset from portfolio"""
    try:
        portfolio = portfolio_engine.portfolios.get(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        asset = next((a for a in portfolio.assets if a.symbol == symbol), None)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found in portfolio")
        
        portfolio.assets.remove(asset)
        await portfolio_engine.update_portfolio_prices(portfolio_id)
        
        return {"message": f"Asset {symbol} removed from portfolio", "portfolio_id": portfolio_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolios")
async def list_portfolios():
    """📋 List all portfolios"""
    try:
        return {
            "portfolios": [
                {
                    "id": p.id,
                    "name": p.name,
                    "total_value": p.total_value,
                    "assets_count": len(p.assets),
                    "last_rebalanced": p.last_rebalanced
                }
                for p in portfolio_engine.portfolios.values()
            ],
            "total_portfolios": len(portfolio_engine.portfolios)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Legacy endpoints compatibility
@app.get("/positions")
async def get_positions():
    """📊 Get all current positions (legacy compatibility)"""
    return {"positions": list(positions.values())}

@app.get("/portfolio")
async def get_legacy_portfolio():
    """💼 Get portfolio overview (legacy compatibility)"""
    portfolio = legacy_portfolio
    return {
        "portfolio": {
            "total_value": portfolio.total_value,
            "available_balance": portfolio.cash_balance,
            "total_pnl": sum(p.pnl for p in positions.values()),
            "total_pnl_percentage": sum(p.pnl_percentage for p in positions.values()) / len(positions) if positions else 0,
            "positions_count": len(positions),
            "timestamp": datetime.now()
        }
    }

@app.post("/position")
async def add_position(position: Position):
    """➕ Add new position (legacy compatibility)"""
    positions[position.symbol] = position
    return {"message": "Position added", "symbol": position.symbol}

@app.delete("/position/{symbol}")
async def remove_position(symbol: str):
    """➖ Remove position (legacy compatibility)"""
    if symbol in positions:
        del positions[symbol]
        return {"message": "Position removed", "symbol": symbol}
    raise HTTPException(status_code=404, detail="Position not found")

# Background auto-rebalancing task
async def auto_rebalance_task():
    """Background task for automatic rebalancing"""
    while True:
        try:
            logger.info("🔄 Running auto-rebalance check...")
            
            for portfolio_id, portfolio in portfolio_engine.portfolios.items():
                if portfolio.auto_rebalance and portfolio_id != "legacy":
                    # Check if rebalancing is needed
                    plan = await portfolio_engine.calculate_rebalance_plan(portfolio_id)
                    
                    if plan.total_deviation > portfolio.rebalance_threshold:
                        logger.info(f"🎯 Auto-rebalancing portfolio {portfolio_id}")
                        await execute_rebalance_background(portfolio_id, plan)
            
            # Sleep for 1 hour
            await asyncio.sleep(3600)
            
        except Exception as e:
            logger.error(f"❌ Auto-rebalance task error: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes on error

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize portfolio manager on startup"""
    logger.info("🚀 Starting Mirai Portfolio Manager...")
    
    # Start background rebalancing task
    asyncio.create_task(auto_rebalance_task())
    
    logger.info("✅ Portfolio Manager startup completed")