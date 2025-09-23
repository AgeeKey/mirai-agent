"""
Analytics Endpoints - Advanced Analytics API with ML Predictions
"""

from fastapi import HTTPException, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import asyncio
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Import from analytics.py
from analytics import (
    app, redis_client, PerformanceMetrics, TradeAnalytics, MarketAnalytics,
    PredictionResult, RiskMetrics, analytics_engine, performance_history,
    trade_analytics, logger
)

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"📡 New WebSocket connection: {len(self.active_connections)} total")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"📡 WebSocket disconnected: {len(self.active_connections)} remaining")
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, default=str))
            except Exception:
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# API Endpoints
@app.get("/analytics/performance/{portfolio_id}", response_model=PerformanceMetrics)
async def get_performance_metrics(portfolio_id: str, period_days: int = Query(30, ge=1, le=365)):
    """📊 Get comprehensive performance metrics for a portfolio"""
    try:
        # Simulate performance calculation (replace with real data)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # Generate synthetic returns for demonstration
        daily_returns = np.random.normal(0.001, 0.02, period_days)
        cumulative_return = np.prod(1 + daily_returns) - 1
        
        # Calculate metrics
        annualized_factor = 365 / period_days
        daily_return = np.mean(daily_returns)
        volatility = np.std(daily_returns) * np.sqrt(365)
        
        # Sharpe ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        sharpe_ratio = (daily_return * 365 - risk_free_rate) / volatility if volatility > 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = daily_returns[daily_returns < 0]
        downside_deviation = np.std(downside_returns) * np.sqrt(365) if len(downside_returns) > 0 else volatility
        sortino_ratio = (daily_return * 365 - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
        
        # Max drawdown
        cumulative_returns = np.cumprod(1 + daily_returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        # Calmar ratio
        calmar_ratio = (daily_return * 365) / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Win rate simulation
        winning_days = np.sum(daily_returns > 0)
        win_rate = winning_days / period_days
        
        # Profit factor simulation
        gross_profit = np.sum(daily_returns[daily_returns > 0])
        gross_loss = abs(np.sum(daily_returns[daily_returns < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        metrics = PerformanceMetrics(
            portfolio_id=portfolio_id,
            total_return=cumulative_return * 100,
            daily_return=daily_return * 100,
            weekly_return=daily_return * 7 * 100,
            monthly_return=daily_return * 30 * 100,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown=max_drawdown * 100,
            volatility=volatility * 100,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=period_days // 2,  # Simulate trades
            avg_trade_duration=8.5,  # hours
            risk_adjusted_return=sharpe_ratio * cumulative_return * 100
        )
        
        # Cache in Redis
        if redis_client:
            redis_client.setex(
                f"performance:{portfolio_id}:{period_days}",
                300,  # 5 minutes
                json.dumps(metrics.dict(), default=str)
            )
        
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Performance metrics calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/market/{symbol}", response_model=MarketAnalytics)
async def get_market_analytics(symbol: str):
    """📈 Get comprehensive market analytics for a symbol"""
    try:
        # Simulate market data (replace with real market data API)
        current_price = 45000 + np.random.normal(0, 1000)
        volume_24h = 50000000 + np.random.normal(0, 10000000)
        price_change_24h = np.random.normal(0, 5)
        
        # Generate sample OHLCV data for technical analysis
        dates = pd.date_range(end=datetime.now(), periods=100, freq='1H')
        np.random.seed(42)  # For reproducible results
        returns = np.random.normal(0, 0.02, 100)
        prices = [current_price * 0.9]  # Start price
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': [volume_24h / 24 + np.random.normal(0, volume_24h / 48) for _ in prices]
        })
        
        # Calculate technical indicators
        technical_indicators = await analytics_engine.calculate_technical_indicators(symbol, df)
        
        # Detect anomalies
        anomaly_score = await analytics_engine.detect_anomalies(symbol, {
            'price': current_price,
            'volume': volume_24h,
            'rsi': technical_indicators.get('rsi', 50),
            'volatility': abs(price_change_24h)
        })
        
        # Simulate sentiment
        sentiment_score = np.random.uniform(-0.5, 0.5)
        
        market_analytics = MarketAnalytics(
            symbol=symbol,
            price=current_price,
            volume_24h=max(0, volume_24h),
            price_change_24h=price_change_24h,
            volatility=abs(price_change_24h),
            rsi=technical_indicators.get('rsi', 50),
            sma_20=technical_indicators.get('sma_20', current_price),
            sma_50=technical_indicators.get('sma_50', current_price * 0.98),
            bollinger_upper=technical_indicators.get('bollinger_upper', current_price * 1.02),
            bollinger_lower=technical_indicators.get('bollinger_lower', current_price * 0.98),
            support_level=technical_indicators.get('support_level', current_price * 0.95),
            resistance_level=technical_indicators.get('resistance_level', current_price * 1.05),
            trend_direction=technical_indicators.get('trend_direction', 'SIDEWAYS'),
            trend_strength=technical_indicators.get('trend_strength', 0.5),
            anomaly_score=anomaly_score,
            sentiment_score=sentiment_score
        )
        
        # Cache in analytics engine
        analytics_engine.market_data[symbol] = market_analytics
        
        return market_analytics
        
    except Exception as e:
        logger.error(f"❌ Market analytics failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/predict/{symbol}", response_model=PredictionResult)
async def get_price_predictions(symbol: str):
    """🔮 Get ML-powered price predictions for a symbol"""
    try:
        # Generate sample historical data for prediction
        periods = 200
        dates = pd.date_range(end=datetime.now(), periods=periods, freq='1H')
        
        # Simulate price data with trend and volatility
        base_price = 45000
        trend = 0.0001  # Small upward trend
        volatility = 0.02
        
        prices = [base_price]
        volumes = []
        
        for i in range(1, periods):
            # Add trend and random walk
            return_rate = trend + np.random.normal(0, volatility)
            new_price = prices[-1] * (1 + return_rate)
            prices.append(new_price)
            volumes.append(1000000 + np.random.normal(0, 200000))
        
        df = pd.DataFrame({
            'timestamp': dates,
            'close': prices,
            'volume': volumes,
            'high': [p * 1.01 for p in prices],
            'low': [p * 0.99 for p in prices]
        })
        
        # Get ML predictions
        prediction = await analytics_engine.predict_prices(symbol, df)
        
        # Cache prediction
        if redis_client:
            redis_client.setex(
                f"prediction:{symbol}",
                600,  # 10 minutes
                json.dumps(prediction.dict(), default=str)
            )
        
        return prediction
        
    except Exception as e:
        logger.error(f"❌ Price prediction failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/risk/{portfolio_id}", response_model=RiskMetrics)
async def get_risk_metrics(portfolio_id: str):
    """⚠️ Get comprehensive risk assessment for a portfolio"""
    try:
        # Simulate portfolio returns for risk calculation
        returns = np.random.normal(0.001, 0.025, 252)  # Daily returns for 1 year
        
        # VaR calculations
        var_95 = np.percentile(returns, 5) * 100
        var_99 = np.percentile(returns, 1) * 100
        
        # Expected Shortfall (Conditional VaR)
        var_95_threshold = np.percentile(returns, 5)
        expected_shortfall = np.mean(returns[returns <= var_95_threshold]) * 100
        
        # Beta calculation (simplified)
        market_returns = np.random.normal(0.0008, 0.02, 252)
        covariance = np.cov(returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)
        beta = covariance / market_variance if market_variance > 0 else 1.0
        
        # Risk scores (0-1)
        volatility = np.std(returns)
        correlation_risk = min(1.0, abs(np.corrcoef(returns, market_returns)[0, 1]))
        concentration_risk = 0.3  # Simulate concentration
        liquidity_risk = 0.2     # Simulate liquidity risk
        
        # Overall risk score
        risk_score = (volatility * 10 + correlation_risk + concentration_risk + liquidity_risk) / 4
        risk_score = min(1.0, max(0.0, risk_score))
        
        # Stress test scenarios
        stress_scenarios = {
            "market_crash_20": np.sum(returns * 0.8) * 100,  # 20% market crash
            "high_volatility": np.sum(returns * 2.0) * 100,   # Double volatility
            "liquidity_crisis": np.sum(returns * 0.5) * 100,  # 50% liquidity reduction
            "black_swan": np.sum(returns * 0.3) * 100         # Extreme event
        }
        
        risk_metrics = RiskMetrics(
            portfolio_id=portfolio_id,
            var_95=var_95,
            var_99=var_99,
            expected_shortfall=expected_shortfall,
            beta=beta,
            correlation_risk=correlation_risk,
            concentration_risk=concentration_risk,
            liquidity_risk=liquidity_risk,
            leverage_ratio=1.2,  # Simulate leverage
            risk_score=risk_score,
            stress_test_results=stress_scenarios
        )
        
        # Cache risk metrics
        if redis_client:
            redis_client.setex(
                f"risk:{portfolio_id}",
                900,  # 15 minutes
                json.dumps(risk_metrics.dict(), default=str)
            )
        
        return risk_metrics
        
    except Exception as e:
        logger.error(f"❌ Risk metrics calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analytics/trade")
async def record_trade_analytics(trade: TradeAnalytics):
    """📝 Record trade analytics for analysis"""
    try:
        # Validate and process trade data
        if trade.profit_loss_percentage == 0 and trade.entry_price != trade.exit_price:
            trade.profit_loss_percentage = ((trade.exit_price - trade.entry_price) / trade.entry_price) * 100
            if trade.side == "SHORT":
                trade.profit_loss_percentage *= -1
        
        # Categorize trade
        if trade.profit_loss > 0:
            trade.category = "winning"
        elif trade.profit_loss < 0:
            trade.category = "losing"
        else:
            trade.category = "breakeven"
        
        # Add to analytics
        trade_analytics.append(trade)
        analytics_engine.trade_analytics.append(trade)
        
        # Cache in Redis
        if redis_client:
            redis_client.lpush("trade_analytics", json.dumps(trade.dict(), default=str))
            redis_client.ltrim("trade_analytics", 0, 999)  # Keep last 1000 trades
        
        # Broadcast to WebSocket clients
        await manager.broadcast({
            "type": "trade_recorded",
            "data": trade.dict()
        })
        
        return {"message": "Trade analytics recorded", "trade_id": trade.trade_id}
        
    except Exception as e:
        logger.error(f"❌ Trade recording failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/trades")
async def get_trade_analytics(
    limit: int = Query(100, ge=1, le=1000),
    symbol: Optional[str] = None,
    category: Optional[str] = None
):
    """📋 Get filtered trade analytics"""
    try:
        trades = trade_analytics.copy()
        
        # Apply filters
        if symbol:
            trades = [t for t in trades if t.symbol == symbol]
        
        if category:
            trades = [t for t in trades if t.category == category]
        
        # Sort by timestamp (newest first) and limit
        trades.sort(key=lambda x: x.timestamp, reverse=True)
        trades = trades[:limit]
        
        # Calculate summary statistics
        if trades:
            total_pnl = sum(t.profit_loss for t in trades)
            win_rate = len([t for t in trades if t.category == "winning"]) / len(trades)
            avg_duration = sum(t.duration_minutes for t in trades) / len(trades)
            
            summary = {
                "total_trades": len(trades),
                "total_pnl": total_pnl,
                "win_rate": win_rate,
                "avg_duration_minutes": avg_duration,
                "best_trade": max(trades, key=lambda x: x.profit_loss).profit_loss,
                "worst_trade": min(trades, key=lambda x: x.profit_loss).profit_loss
            }
        else:
            summary = {
                "total_trades": 0,
                "total_pnl": 0,
                "win_rate": 0,
                "avg_duration_minutes": 0,
                "best_trade": 0,
                "worst_trade": 0
            }
        
        return {
            "trades": [t.dict() for t in trades],
            "summary": summary,
            "filters_applied": {
                "symbol": symbol,
                "category": category,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Trade analytics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/dashboard/{portfolio_id}")
async def get_analytics_dashboard(portfolio_id: str):
    """🎛️ Get comprehensive analytics dashboard data"""
    try:
        # Get all analytics in parallel
        performance_task = get_performance_metrics(portfolio_id, 30)
        risk_task = get_risk_metrics(portfolio_id)
        
        # Execute tasks
        performance = await performance_task
        risk = await risk_task
        
        # Get recent trades for this portfolio
        recent_trades = [
            t for t in trade_analytics[-20:] 
            if hasattr(t, 'portfolio_id') and getattr(t, 'portfolio_id', None) == portfolio_id
        ]
        
        # Market data for major symbols
        market_symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        market_data = {}
        
        for symbol in market_symbols:
            try:
                market_data[symbol] = await get_market_analytics(symbol)
            except Exception as e:
                logger.warning(f"Failed to get market data for {symbol}: {e}")
        
        dashboard = {
            "portfolio_id": portfolio_id,
            "performance": performance.dict(),
            "risk": risk.dict(),
            "recent_trades": [t.dict() for t in recent_trades],
            "market_overview": {symbol: data.dict() for symbol, data in market_data.items()},
            "alerts": [],  # Placeholder for alerts
            "last_updated": datetime.now()
        }
        
        return dashboard
        
    except Exception as e:
        logger.error(f"❌ Dashboard data compilation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time analytics
@app.websocket("/ws/analytics")
async def websocket_analytics(websocket: WebSocket):
    """🔄 Real-time analytics WebSocket endpoint"""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(5)
            
            # Sample real-time data
            update = {
                "type": "analytics_update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "active_trades": len(trade_analytics),
                    "total_portfolios": 1,  # Placeholder
                    "system_status": "healthy"
                }
            }
            
            await websocket.send_text(json.dumps(update, default=str))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)

# Background analytics processing
async def analytics_processing_task():
    """Background task for analytics processing"""
    while True:
        try:
            logger.info("🧠 Running analytics processing...")
            
            # Process trade analytics
            if trade_analytics:
                # Calculate rolling metrics
                recent_trades = trade_analytics[-100:]  # Last 100 trades
                if recent_trades:
                    win_rate = len([t for t in recent_trades if t.category == "winning"]) / len(recent_trades)
                    avg_pnl = sum(t.profit_loss for t in recent_trades) / len(recent_trades)
                    
                    # Cache metrics
                    if redis_client:
                        redis_client.setex("rolling_win_rate", 300, str(win_rate))
                        redis_client.setex("rolling_avg_pnl", 300, str(avg_pnl))
            
            # Update ML models periodically
            await analytics_engine.initialize_ml_models()
            
            # Sleep for 5 minutes
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.error(f"❌ Analytics processing error: {e}")
            await asyncio.sleep(60)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize analytics engine on startup"""
    logger.info("🚀 Starting Mirai Analytics Engine...")
    
    # Initialize ML models
    await analytics_engine.initialize_ml_models()
    
    # Start background processing
    asyncio.create_task(analytics_processing_task())
    
    logger.info("✅ Analytics Engine startup completed")

# Legacy endpoints for compatibility
@app.get("/performance")
async def get_legacy_performance():
    """📊 Get performance overview (legacy compatibility)"""
    if performance_history:
        latest = performance_history[-1]
        return {"performance": latest.dict()}
    
    return {
        "performance": {
            "total_return": 5.2,
            "daily_return": 0.1,
            "sharpe_ratio": 1.8,
            "max_drawdown": -8.5,
            "win_rate": 0.68,
            "total_trades": 156,
            "timestamp": datetime.now()
        }
    }

@app.get("/trades")
async def get_legacy_trades():
    """📋 Get trade analytics (legacy compatibility)"""
    return {"trades": [t.dict() for t in trade_analytics[-50:]]}

@app.post("/performance")
async def add_performance_metrics(metrics: PerformanceMetrics):
    """➕ Add performance metrics (legacy compatibility)"""
    performance_history.append(metrics)
    return {"message": "Performance metrics added"}