"""
Risk Engine API Endpoints - Advanced Risk Management Services
"""

from risk_engine import app, risk_engine, RiskAssessment, RiskConfig, PortfolioRiskMetrics, StressTestResult, RiskAlert
from fastapi import HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# WebSocket connection manager
class RiskConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"🔌 Risk WebSocket client connected. Total: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"❌ Risk WebSocket client disconnected. Total: {len(self.active_connections)}")
        
    async def broadcast_alert(self, alert: RiskAlert):
        """Broadcast risk alert to all connected clients"""
        if self.active_connections:
            message = {
                "type": "risk_alert",
                "data": alert.dict(),
                "timestamp": datetime.now().isoformat()
            }
            dead_connections = []
            
            for connection in self.active_connections:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    dead_connections.append(connection)
            
            # Remove dead connections
            for dead_conn in dead_connections:
                self.disconnect(dead_conn)

manager = RiskConnectionManager()

# Request/Response Models
class TradeRiskRequest(BaseModel):
    symbol: str
    action: str  # BUY, SELL
    quantity: float
    price: float
    portfolio_id: Optional[str] = "default"
    force_override: bool = False

class PortfolioRiskRequest(BaseModel):
    portfolio_id: str = "default"
    include_correlations: bool = True
    calculate_var: bool = True

class StressTestRequest(BaseModel):
    portfolio_id: str = "default"
    scenarios: List[str] = ["market_crash", "volatility_spike", "liquidity_crisis"]
    confidence_level: float = 0.95

class RiskConfigUpdate(BaseModel):
    max_portfolio_risk: Optional[float] = None
    max_position_risk: Optional[float] = None
    max_daily_loss: Optional[float] = None
    max_drawdown: Optional[float] = None
    max_correlation: Optional[float] = None
    max_leverage: Optional[float] = None
    emergency_stop: Optional[bool] = None
    enabled: Optional[bool] = None

# Health Check
@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        if risk_engine.redis_client:
            risk_engine.redis_client.ping()
        
        return {
            "status": "healthy",
            "service": "risk_engine",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "config": {
                "monitoring_enabled": risk_engine.risk_config.real_time_monitoring,
                "emergency_stop": risk_engine.risk_config.emergency_stop,
                "max_portfolio_risk": risk_engine.risk_config.max_portfolio_risk
            }
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Core Risk Assessment Endpoints
@app.post("/assess/trade", response_model=RiskAssessment)
async def assess_trade_risk(request: TradeRiskRequest):
    """
    Comprehensive trade risk assessment
    
    Analyzes:
    - Position sizing and portfolio impact
    - Volatility and liquidity risks
    - Correlation with existing positions
    - Market conditions and sentiment
    - AI-powered risk prediction
    """
    try:
        logger.info(f"🔍 Assessing trade risk: {request.symbol} {request.action} {request.quantity}")
        
        # Get portfolio data
        portfolio_data = await risk_engine._get_portfolio_data(request.portfolio_id)
        
        # Perform risk assessment
        assessment = await risk_engine.assess_trade_risk(
            symbol=request.symbol,
            action=request.action,
            quantity=request.quantity,
            price=request.price,
            portfolio_data=portfolio_data
        )
        
        # Cache assessment
        if risk_engine.redis_client:
            try:
                cache_key = f"risk_assessment:{assessment.assessment_id}"
                risk_engine.redis_client.setex(
                    cache_key, 
                    3600,  # 1 hour TTL
                    json.dumps(assessment.dict(), default=str)
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to cache assessment: {e}")
        
        # Create alert if high risk
        if assessment.risk_score > 0.8:
            alert = RiskAlert(
                alert_id=f"high_risk_{assessment.assessment_id}",
                alert_type="HIGH_RISK_TRADE",
                severity="HIGH",
                symbol=request.symbol,
                portfolio_id=request.portfolio_id,
                message=f"High risk trade detected: {request.symbol} with risk score {assessment.risk_score:.2f}",
                metric_name="risk_score",
                current_value=assessment.risk_score,
                threshold_value=0.8,
                recommended_action="Reduce position size or avoid trade"
            )
            await manager.broadcast_alert(alert)
        
        logger.info(f"✅ Risk assessment completed: {assessment.assessment_id}")
        return assessment
        
    except Exception as e:
        logger.error(f"❌ Trade risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")

@app.get("/portfolio/{portfolio_id}/metrics", response_model=PortfolioRiskMetrics)
async def get_portfolio_risk_metrics(
    portfolio_id: str = "default",
    include_correlations: bool = True,
    calculate_var: bool = True
):
    """
    Get comprehensive portfolio risk metrics
    
    Includes:
    - P&L analysis and drawdown metrics
    - Risk exposure and leverage analysis
    - Value at Risk (VaR) calculations
    - Correlation matrix and concentration
    - Performance ratios (Sharpe, Sortino, Calmar)
    """
    try:
        logger.info(f"📊 Calculating portfolio risk metrics for: {portfolio_id}")
        
        # Get portfolio data from Portfolio Manager
        portfolio_data = await risk_engine._get_portfolio_data(portfolio_id)
        if not portfolio_data:
            raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")
        
        # Calculate comprehensive metrics
        metrics = await risk_engine._calculate_portfolio_metrics(
            portfolio_id=portfolio_id,
            portfolio_data=portfolio_data,
            include_correlations=include_correlations,
            calculate_var=calculate_var
        )
        
        # Cache metrics
        risk_engine.portfolio_metrics[portfolio_id] = metrics
        
        if risk_engine.redis_client:
            try:
                cache_key = f"portfolio_metrics:{portfolio_id}"
                risk_engine.redis_client.setex(
                    cache_key,
                    300,  # 5 minutes TTL
                    json.dumps(metrics.dict(), default=str)
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to cache portfolio metrics: {e}")
        
        logger.info(f"✅ Portfolio metrics calculated for: {portfolio_id}")
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Portfolio metrics calculation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics calculation failed: {str(e)}")

@app.post("/stress-test", response_model=List[StressTestResult])
async def run_stress_test(request: StressTestRequest):
    """
    Run comprehensive stress tests on portfolio
    
    Scenarios:
    - Market crash (-20% market drop)
    - Volatility spike (3x volatility increase)
    - Liquidity crisis (50% liquidity reduction)
    - Correlation breakdown (correlations → 1.0)
    - Interest rate shock (+200 bps)
    """
    try:
        logger.info(f"🧪 Running stress tests for portfolio: {request.portfolio_id}")
        
        results = []
        portfolio_data = await risk_engine._get_portfolio_data(request.portfolio_id)
        
        if not portfolio_data:
            raise HTTPException(status_code=404, detail=f"Portfolio {request.portfolio_id} not found")
        
        baseline_value = portfolio_data.get('total_value', 0)
        
        for scenario in request.scenarios:
            logger.info(f"📉 Running stress test scenario: {scenario}")
            
            result = await risk_engine._run_stress_scenario(
                portfolio_id=request.portfolio_id,
                scenario=scenario,
                portfolio_data=portfolio_data,
                confidence_level=request.confidence_level
            )
            
            results.append(result)
            
            # Create alert for severe stress test results
            if result.loss_percentage > 0.15:  # >15% loss
                alert = RiskAlert(
                    alert_id=f"stress_test_{scenario}_{int(datetime.now().timestamp())}",
                    alert_type="STRESS_TEST_FAILURE",
                    severity="CRITICAL",
                    portfolio_id=request.portfolio_id,
                    message=f"Stress test {scenario} shows {result.loss_percentage:.1%} loss",
                    metric_name="stress_test_loss",
                    current_value=result.loss_percentage,
                    threshold_value=0.15,
                    recommended_action="Review portfolio composition and hedging strategies"
                )
                await manager.broadcast_alert(alert)
        
        # Cache stress test results
        risk_engine.stress_test_results.extend(results)
        
        logger.info(f"✅ Stress tests completed for portfolio: {request.portfolio_id}")
        return results
        
    except Exception as e:
        logger.error(f"❌ Stress test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stress test failed: {str(e)}")

# Risk Configuration Endpoints
@app.get("/config", response_model=RiskConfig)
async def get_risk_config():
    """Get current risk configuration"""
    return risk_engine.risk_config

@app.post("/config", response_model=RiskConfig)
async def update_risk_config(config_update: RiskConfigUpdate):
    """Update risk configuration"""
    try:
        logger.info(f"⚙️ Updating risk configuration")
        
        # Update configuration
        config_dict = risk_engine.risk_config.dict()
        for field, value in config_update.dict(exclude_unset=True).items():
            if value is not None:
                config_dict[field] = value
        
        risk_engine.risk_config = RiskConfig(**config_dict)
        
        # Cache new configuration
        if risk_engine.redis_client:
            try:
                risk_engine.redis_client.setex(
                    "risk_config",
                    3600,
                    json.dumps(risk_engine.risk_config.dict())
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to cache config: {e}")
        
        # Broadcast configuration change
        alert = RiskAlert(
            alert_id=f"config_update_{int(datetime.now().timestamp())}",
            alert_type="CONFIG_UPDATE",
            severity="MEDIUM",
            message="Risk configuration updated",
            metric_name="configuration",
            current_value=1,
            threshold_value=1,
            recommended_action="Review updated risk parameters"
        )
        await manager.broadcast_alert(alert)
        
        logger.info(f"✅ Risk configuration updated")
        return risk_engine.risk_config
        
    except Exception as e:
        logger.error(f"❌ Risk configuration update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration update failed: {str(e)}")

@app.post("/emergency-stop")
async def emergency_stop():
    """Emergency stop all trading activities"""
    try:
        logger.warning("🚨 EMERGENCY STOP ACTIVATED")
        
        risk_engine.risk_config.emergency_stop = True
        
        # Broadcast emergency alert
        alert = RiskAlert(
            alert_id=f"emergency_stop_{int(datetime.now().timestamp())}",
            alert_type="EMERGENCY_STOP",
            severity="CRITICAL",
            message="EMERGENCY STOP ACTIVATED - All trading halted",
            metric_name="emergency_stop",
            current_value=1,
            threshold_value=0,
            recommended_action="Immediate manual review required",
            auto_action_taken=True
        )
        await manager.broadcast_alert(alert)
        
        return {"status": "emergency_stop_activated", "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        logger.error(f"❌ Emergency stop failed: {e}")
        raise HTTPException(status_code=500, detail=f"Emergency stop failed: {str(e)}")

@app.post("/emergency-stop/reset")
async def reset_emergency_stop():
    """Reset emergency stop"""
    try:
        logger.info("🔄 Resetting emergency stop")
        
        risk_engine.risk_config.emergency_stop = False
        
        alert = RiskAlert(
            alert_id=f"emergency_reset_{int(datetime.now().timestamp())}",
            alert_type="EMERGENCY_RESET",
            severity="MEDIUM",
            message="Emergency stop reset - Trading resumed",
            metric_name="emergency_stop",
            current_value=0,
            threshold_value=0,
            recommended_action="Monitor systems closely"
        )
        await manager.broadcast_alert(alert)
        
        return {"status": "emergency_stop_reset", "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        logger.error(f"❌ Emergency stop reset failed: {e}")
        raise HTTPException(status_code=500, detail=f"Emergency stop reset failed: {str(e)}")

# Alert Management Endpoints
@app.get("/alerts", response_model=List[RiskAlert])
async def get_risk_alerts(
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    portfolio_id: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 100
):
    """Get risk alerts with filtering options"""
    try:
        alerts = list(risk_engine.active_alerts.values())
        
        # Apply filters
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        if portfolio_id:
            alerts = [a for a in alerts if a.portfolio_id == portfolio_id]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
        
        # Sort by timestamp (newest first) and limit
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        return alerts[:limit]
        
    except Exception as e:
        logger.error(f"❌ Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge a risk alert"""
    try:
        if alert_id not in risk_engine.active_alerts:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        risk_engine.active_alerts[alert_id].acknowledged = True
        
        return {"status": "acknowledged", "alert_id": alert_id}
        
    except Exception as e:
        logger.error(f"❌ Failed to acknowledge alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")

# Real-time Monitoring
@app.post("/monitoring/start")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Start real-time risk monitoring"""
    if not risk_engine.is_monitoring:
        background_tasks.add_task(risk_engine._start_monitoring)
        return {"status": "monitoring_started"}
    return {"status": "already_monitoring"}

@app.post("/monitoring/stop")
async def stop_monitoring():
    """Stop real-time risk monitoring"""
    risk_engine.is_monitoring = False
    return {"status": "monitoring_stopped"}

# WebSocket for real-time risk updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time risk updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic risk updates
            await asyncio.sleep(5)
            
            # Get current portfolio metrics
            try:
                metrics_summary = {
                    "type": "risk_summary",
                    "data": {
                        "active_alerts": len([a for a in risk_engine.active_alerts.values() if not a.acknowledged]),
                        "emergency_stop": risk_engine.risk_config.emergency_stop,
                        "monitoring_active": risk_engine.is_monitoring,
                        "total_portfolios": len(risk_engine.portfolio_metrics)
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send_text(json.dumps(metrics_summary))
                
            except Exception as e:
                logger.error(f"❌ WebSocket update failed: {e}")
                break
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# AI Risk Analysis Endpoints
@app.post("/ai/analyze")
async def ai_risk_analysis(
    symbol: str,
    timeframe: str = "1d",
    analysis_type: str = "comprehensive"
):
    """
    AI-powered risk analysis using market sentiment and technical indicators
    """
    try:
        logger.info(f"🤖 Running AI risk analysis for {symbol}")
        
        # Get AI risk assessment
        ai_assessment = await risk_engine._get_ai_risk_assessment(
            symbol=symbol,
            action="ANALYZE",
            market_data=await risk_engine._get_market_data(symbol)
        )
        
        return {
            "symbol": symbol,
            "ai_risk_score": ai_assessment,
            "analysis_type": analysis_type,
            "confidence": min(1.0, ai_assessment * 1.2),
            "recommendations": await risk_engine._get_ai_recommendations(symbol, ai_assessment),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ AI risk analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)