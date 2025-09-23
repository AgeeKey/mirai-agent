"""
Risk Engine Microservice - Advanced Risk Management with Predictive Analytics
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncio
import logging
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import redis
import aiohttp
from dataclasses import dataclass
from scipy import stats
from sklearn.ensemble import IsolationForest
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mirai Risk Engine",
    description="🛡️ Advanced Risk Management with Predictive Analytics & Real-time Monitoring",
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
class RiskAssessment(BaseModel):
    assessment_id: str = Field(..., description="Unique assessment ID")
    symbol: str = Field(..., description="Trading symbol")
    action: str = Field(..., description="BUY, SELL, HOLD")
    approved: bool = Field(..., description="Risk approval status")
    risk_score: float = Field(..., ge=0, le=1, description="Overall risk score 0-1")
    confidence_score: float = Field(..., ge=0, le=1, description="Assessment confidence")
    max_position_size: float = Field(..., gt=0, description="Maximum allowed position size")
    recommended_size: float = Field(..., gt=0, description="Recommended position size")
    stop_loss: Optional[float] = Field(None, description="Recommended stop loss")
    take_profit: Optional[float] = Field(None, description="Recommended take profit")
    risk_reward_ratio: float = Field(..., description="Risk/Reward ratio")
    portfolio_impact: float = Field(..., description="Expected portfolio impact %")
    correlation_risk: float = Field(..., ge=0, le=1, description="Correlation risk score")
    liquidity_risk: float = Field(..., ge=0, le=1, description="Liquidity risk score")
    volatility_risk: float = Field(..., ge=0, le=1, description="Volatility risk score")
    market_risk: float = Field(..., ge=0, le=1, description="Market risk score")
    concentration_risk: float = Field(..., ge=0, le=1, description="Concentration risk score")
    reason: str = Field(..., description="Assessment reasoning")
    recommendations: List[str] = Field(default_factory=list, description="Risk recommendations")
    timestamp: datetime = Field(default_factory=datetime.now)

class RiskConfig(BaseModel):
    max_portfolio_risk: float = Field(0.02, ge=0, le=1, description="Max portfolio risk %")
    max_position_risk: float = Field(0.01, ge=0, le=1, description="Max single position risk %")
    max_daily_loss: float = Field(0.05, ge=0, le=1, description="Max daily loss %")
    max_drawdown: float = Field(0.10, ge=0, le=1, description="Max drawdown %")
    max_correlation: float = Field(0.7, ge=0, le=1, description="Max correlation between positions")
    max_leverage: float = Field(3.0, ge=1, description="Maximum leverage allowed")
    min_liquidity_score: float = Field(0.5, ge=0, le=1, description="Minimum liquidity score")
    volatility_threshold: float = Field(0.1, ge=0, description="Volatility threshold")
    var_confidence: float = Field(0.95, ge=0.9, le=0.99, description="VaR confidence level")
    stress_test_enabled: bool = Field(True, description="Enable stress testing")
    real_time_monitoring: bool = Field(True, description="Enable real-time monitoring")
    enabled: bool = Field(True, description="Risk engine enabled")
    emergency_stop: bool = Field(False, description="Emergency stop all trading")

class PortfolioRiskMetrics(BaseModel):
    portfolio_id: str = Field(..., description="Portfolio identifier")
    total_value: float = Field(..., gt=0, description="Total portfolio value")
    daily_pnl: float = Field(..., description="Daily P&L")
    daily_pnl_pct: float = Field(..., description="Daily P&L percentage")
    weekly_pnl: float = Field(..., description="Weekly P&L")
    monthly_pnl: float = Field(..., description="Monthly P&L")
    current_drawdown: float = Field(..., description="Current drawdown %")
    max_drawdown: float = Field(..., description="Maximum drawdown %")
    risk_exposure: float = Field(..., ge=0, le=1, description="Current risk exposure")
    total_leverage: float = Field(..., ge=0, description="Total leverage")
    positions_count: int = Field(..., ge=0, description="Number of positions")
    concentration_score: float = Field(..., ge=0, le=1, description="Portfolio concentration")
    correlation_matrix: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Asset correlations")
    var_1d: float = Field(..., description="1-day Value at Risk")
    var_7d: float = Field(..., description="7-day Value at Risk")
    expected_shortfall: float = Field(..., description="Expected Shortfall (CVaR)")
    beta: float = Field(..., description="Portfolio beta")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: float = Field(..., description="Sortino ratio")
    calmar_ratio: float = Field(..., description="Calmar ratio")
    risk_budget_utilization: float = Field(..., ge=0, le=1, description="Risk budget used")
    timestamp: datetime = Field(default_factory=datetime.now)

class StressTestResult(BaseModel):
    scenario_name: str = Field(..., description="Stress test scenario name")
    portfolio_id: str = Field(..., description="Portfolio identifier")
    baseline_value: float = Field(..., description="Current portfolio value")
    stressed_value: float = Field(..., description="Portfolio value under stress")
    loss_amount: float = Field(..., description="Absolute loss amount")
    loss_percentage: float = Field(..., description="Loss percentage")
    worst_asset: str = Field(..., description="Worst performing asset")
    worst_asset_loss: float = Field(..., description="Worst asset loss %")
    recovery_time_estimate: str = Field(..., description="Estimated recovery time")
    risk_measures: Dict[str, float] = Field(default_factory=dict, description="Various risk measures")
    recommendations: List[str] = Field(default_factory=list, description="Stress test recommendations")
    severity: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    timestamp: datetime = Field(default_factory=datetime.now)

class RiskAlert(BaseModel):
    alert_id: str = Field(..., description="Unique alert ID")
    alert_type: str = Field(..., description="Alert type")
    severity: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    symbol: Optional[str] = Field(None, description="Related symbol")
    portfolio_id: Optional[str] = Field(None, description="Related portfolio")
    message: str = Field(..., description="Alert message")
    metric_name: str = Field(..., description="Risk metric name")
    current_value: float = Field(..., description="Current metric value")
    threshold_value: float = Field(..., description="Threshold value")
    recommended_action: str = Field(..., description="Recommended action")
    auto_action_taken: bool = Field(False, description="Automatic action taken")
    acknowledged: bool = Field(False, description="Alert acknowledged")
    timestamp: datetime = Field(default_factory=datetime.now)

# Risk Engine
class RiskEngine:
    def __init__(self):
        self.risk_config = RiskConfig()
        self.portfolio_metrics: Dict[str, PortfolioRiskMetrics] = {}
        self.stress_test_results: List[StressTestResult] = []
        self.active_alerts: Dict[str, RiskAlert] = {}
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.is_monitoring = False
        
    async def assess_trade_risk(self, 
                               symbol: str, 
                               action: str, 
                               quantity: float, 
                               price: float,
                               portfolio_data: Dict = None) -> RiskAssessment:
        """Comprehensive trade risk assessment"""
        try:
            assessment_id = f"risk_{symbol}_{action}_{int(datetime.now().timestamp())}"
            
            # Get market data and portfolio information
            market_data = await self._get_market_data(symbol)
            current_portfolio = portfolio_data or await self._get_portfolio_data()
            
            # Calculate individual risk components
            volatility_risk = await self._calculate_volatility_risk(symbol, market_data)
            liquidity_risk = await self._calculate_liquidity_risk(symbol, market_data)
            correlation_risk = await self._calculate_correlation_risk(symbol, current_portfolio)
            concentration_risk = await self._calculate_concentration_risk(symbol, quantity, current_portfolio)
            market_risk = await self._calculate_market_risk(symbol, market_data)
            
            # Calculate position sizing
            max_position_size = await self._calculate_max_position_size(symbol, current_portfolio)
            recommended_size = min(quantity, max_position_size * 0.8)  # Conservative sizing
            
            # Calculate stop loss and take profit
            volatility = market_data.get('volatility', 0.02)
            if action == "BUY":
                stop_loss = price * (1 - 2 * volatility)
                take_profit = price * (1 + 3 * volatility)
            else:
                stop_loss = price * (1 + 2 * volatility)
                take_profit = price * (1 - 3 * volatility)
            
            # Calculate risk/reward ratio
            risk_amount = abs(price - stop_loss)
            reward_amount = abs(take_profit - price)
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            
            # Portfolio impact calculation
            portfolio_value = current_portfolio.get('total_value', 100000)
            position_value = quantity * price
            portfolio_impact = (position_value / portfolio_value) * 100
            
            # Overall risk score calculation
            risk_components = [
                volatility_risk * 0.25,
                liquidity_risk * 0.15,
                correlation_risk * 0.20,
                concentration_risk * 0.20,
                market_risk * 0.20
            ]
            overall_risk_score = sum(risk_components)
            
            # Risk approval logic
            approved = True
            reasons = []
            recommendations = []
            
            if overall_risk_score > 0.8:
                approved = False
                reasons.append("Overall risk score too high")
            
            if portfolio_impact > self.risk_config.max_position_risk * 100:
                approved = False
                reasons.append(f"Position size exceeds limit ({portfolio_impact:.1f}% > {self.risk_config.max_position_risk*100}%)")
            
            if volatility_risk > 0.9:
                recommendations.append("Consider reducing position size due to high volatility")
            
            if correlation_risk > 0.8:
                recommendations.append("High correlation with existing positions")
            
            if risk_reward_ratio < 1.0:
                recommendations.append("Poor risk/reward ratio - consider better entry point")
            
            # AI-powered risk prediction
            ai_risk_score = await self._get_ai_risk_assessment(symbol, action, market_data)
            confidence_score = 1.0 - overall_risk_score * 0.5  # Higher risk = lower confidence
            
            return RiskAssessment(
                assessment_id=assessment_id,
                symbol=symbol,
                action=action,
                approved=approved and not self.risk_config.emergency_stop,
                risk_score=overall_risk_score,
                confidence_score=confidence_score,
                max_position_size=max_position_size,
                recommended_size=recommended_size,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward_ratio=risk_reward_ratio,
                portfolio_impact=portfolio_impact,
                correlation_risk=correlation_risk,
                liquidity_risk=liquidity_risk,
                volatility_risk=volatility_risk,
                market_risk=market_risk,
                concentration_risk=concentration_risk,
                reason="; ".join(reasons) if reasons else "Risk assessment passed",
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"❌ Trade risk assessment failed: {e}")
            # Return conservative assessment on error
            return RiskAssessment(
                assessment_id=f"error_{symbol}_{int(datetime.now().timestamp())}",
                symbol=symbol,
                action=action,
                approved=False,
                risk_score=1.0,
                confidence_score=0.1,
                max_position_size=0,
                recommended_size=0,
                stop_loss=price * 0.98 if action == "BUY" else price * 1.02,
                take_profit=price * 1.02 if action == "BUY" else price * 0.98,
                risk_reward_ratio=1.0,
                portfolio_impact=0,
                correlation_risk=1.0,
                liquidity_risk=1.0,
                volatility_risk=1.0,
                market_risk=1.0,
                concentration_risk=1.0,
                reason="Risk assessment error - trade rejected for safety",
                recommendations=["Manual review required"]
            )

# Initialize risk engine
risk_engine = RiskEngine()

# Cache and state
current_config = RiskConfig()
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
