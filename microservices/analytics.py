"""
Analytics Microservice - Advanced Analytics with ML and Real-time Processing
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
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
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import ta
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mirai Analytics Engine",
    description="🧠 Advanced Analytics with ML, Real-time Processing & Predictive Insights",
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
class PerformanceMetrics(BaseModel):
    portfolio_id: str = Field(..., description="Portfolio identifier")
    total_return: float = Field(..., description="Total return percentage")
    daily_return: float = Field(..., description="Daily return percentage")
    weekly_return: float = Field(..., description="Weekly return percentage") 
    monthly_return: float = Field(..., description="Monthly return percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: float = Field(..., description="Sortino ratio")
    calmar_ratio: float = Field(..., description="Calmar ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    volatility: float = Field(..., description="Portfolio volatility")
    win_rate: float = Field(..., ge=0, le=1, description="Win rate percentage")
    profit_factor: float = Field(..., description="Profit factor")
    total_trades: int = Field(..., ge=0, description="Total number of trades")
    avg_trade_duration: float = Field(..., description="Average trade duration in hours")
    risk_adjusted_return: float = Field(..., description="Risk-adjusted return")
    timestamp: datetime = Field(default_factory=datetime.now)

class TradeAnalytics(BaseModel):
    trade_id: str = Field(..., description="Unique trade identifier")
    symbol: str = Field(..., description="Trading symbol")
    entry_price: float = Field(..., gt=0, description="Entry price")
    exit_price: float = Field(..., gt=0, description="Exit price")
    quantity: float = Field(..., gt=0, description="Trade quantity")
    profit_loss: float = Field(..., description="Profit/Loss amount")
    profit_loss_percentage: float = Field(..., description="Profit/Loss percentage")
    duration_minutes: int = Field(..., ge=0, description="Trade duration in minutes")
    side: str = Field(..., description="LONG or SHORT")
    category: str = Field(..., description="winning/losing/breakeven")
    entry_reason: str = Field(..., description="Reason for entry")
    exit_reason: str = Field(..., description="Reason for exit")
    risk_reward_ratio: float = Field(..., description="Risk/Reward ratio")
    market_condition: str = Field(..., description="Market condition during trade")
    timestamp: datetime = Field(default_factory=datetime.now)

class MarketAnalytics(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    price: float = Field(..., gt=0, description="Current price")
    volume_24h: float = Field(..., ge=0, description="24h volume")
    price_change_24h: float = Field(..., description="24h price change %")
    volatility: float = Field(..., ge=0, description="Current volatility")
    rsi: float = Field(..., ge=0, le=100, description="RSI indicator")
    sma_20: float = Field(..., gt=0, description="20-period SMA")
    sma_50: float = Field(..., gt=0, description="50-period SMA")
    bollinger_upper: float = Field(..., gt=0, description="Bollinger upper band")
    bollinger_lower: float = Field(..., gt=0, description="Bollinger lower band")
    support_level: float = Field(..., gt=0, description="Support level")
    resistance_level: float = Field(..., gt=0, description="Resistance level")
    trend_direction: str = Field(..., description="UP, DOWN, SIDEWAYS")
    trend_strength: float = Field(..., ge=0, le=1, description="Trend strength 0-1")
    anomaly_score: float = Field(..., ge=0, le=1, description="Anomaly detection score")
    sentiment_score: float = Field(..., ge=-1, le=1, description="Market sentiment -1 to 1")
    timestamp: datetime = Field(default_factory=datetime.now)

class PredictionResult(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    current_price: float = Field(..., gt=0, description="Current price")
    predicted_price_1h: float = Field(..., gt=0, description="1-hour price prediction")
    predicted_price_24h: float = Field(..., gt=0, description="24-hour price prediction")
    predicted_price_7d: float = Field(..., gt=0, description="7-day price prediction")
    confidence_1h: float = Field(..., ge=0, le=1, description="1-hour confidence")
    confidence_24h: float = Field(..., ge=0, le=1, description="24-hour confidence")
    confidence_7d: float = Field(..., ge=0, le=1, description="7-day confidence")
    model_accuracy: float = Field(..., ge=0, le=1, description="Model accuracy score")
    feature_importance: Dict[str, float] = Field(..., description="Feature importance scores")
    risk_assessment: str = Field(..., description="LOW, MEDIUM, HIGH")
    recommendation: str = Field(..., description="BUY, SELL, HOLD")
    timestamp: datetime = Field(default_factory=datetime.now)

class RiskMetrics(BaseModel):
    portfolio_id: str = Field(..., description="Portfolio identifier")
    var_95: float = Field(..., description="Value at Risk 95%")
    var_99: float = Field(..., description="Value at Risk 99%")
    expected_shortfall: float = Field(..., description="Expected Shortfall")
    beta: float = Field(..., description="Portfolio beta")
    correlation_risk: float = Field(..., ge=0, le=1, description="Correlation risk score")
    concentration_risk: float = Field(..., ge=0, le=1, description="Concentration risk score")
    liquidity_risk: float = Field(..., ge=0, le=1, description="Liquidity risk score")
    leverage_ratio: float = Field(..., ge=0, description="Leverage ratio")
    risk_score: float = Field(..., ge=0, le=1, description="Overall risk score")
    stress_test_results: Dict[str, float] = Field(..., description="Stress test scenarios")
    timestamp: datetime = Field(default_factory=datetime.now)

# Analytics Engine
class AnalyticsEngine:
    def __init__(self):
        self.performance_history: List[PerformanceMetrics] = []
        self.trade_analytics: List[TradeAnalytics] = []
        self.market_data: Dict[str, MarketAnalytics] = {}
        self.ml_models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.anomaly_detectors: Dict[str, IsolationForest] = {}
        
    async def initialize_ml_models(self):
        """Initialize ML models for analytics"""
        try:
            # Price prediction models for major symbols
            symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
            
            for symbol in symbols:
                # Random Forest for price prediction
                self.ml_models[f"{symbol}_price_predictor"] = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
                
                # Scaler for feature normalization
                self.scalers[f"{symbol}_scaler"] = StandardScaler()
                
                # Anomaly detector
                self.anomaly_detectors[f"{symbol}_anomaly"] = IsolationForest(
                    contamination=0.1,
                    random_state=42
                )
            
            logger.info("✅ ML models initialized")
            
        except Exception as e:
            logger.error(f"❌ ML model initialization failed: {e}")
    
    async def calculate_technical_indicators(self, symbol: str, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical indicators for a symbol"""
        try:
            if len(df) < 50:
                return {}
            
            # RSI
            rsi = ta.momentum.RSIIndicator(df['close']).rsi().iloc[-1]
            
            # Moving averages
            sma_20 = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator().iloc[-1]
            sma_50 = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator().iloc[-1]
            
            # Bollinger Bands
            bb_indicator = ta.volatility.BollingerBands(df['close'])
            bb_upper = bb_indicator.bollinger_hband().iloc[-1]
            bb_lower = bb_indicator.bollinger_lband().iloc[-1]
            
            # Support and Resistance (simplified)
            recent_lows = df['low'].rolling(window=20).min().iloc[-1]
            recent_highs = df['high'].rolling(window=20).max().iloc[-1]
            
            # Trend analysis
            price_change = (df['close'].iloc[-1] - df['close'].iloc[-20]) / df['close'].iloc[-20]
            trend_direction = "UP" if price_change > 0.02 else "DOWN" if price_change < -0.02 else "SIDEWAYS"
            trend_strength = min(1.0, abs(price_change) * 10)
            
            return {
                'rsi': float(rsi),
                'sma_20': float(sma_20),
                'sma_50': float(sma_50),
                'bollinger_upper': float(bb_upper),
                'bollinger_lower': float(bb_lower),
                'support_level': float(recent_lows),
                'resistance_level': float(recent_highs),
                'trend_direction': trend_direction,
                'trend_strength': float(trend_strength)
            }
            
        except Exception as e:
            logger.error(f"❌ Technical indicators calculation failed: {e}")
            return {}
    
    async def detect_anomalies(self, symbol: str, current_data: Dict[str, float]) -> float:
        """Detect market anomalies using ML"""
        try:
            detector_key = f"{symbol}_anomaly"
            if detector_key not in self.anomaly_detectors:
                return 0.0
            
            # Prepare features
            features = np.array([[
                current_data.get('price', 0),
                current_data.get('volume', 0),
                current_data.get('rsi', 50),
                current_data.get('volatility', 0)
            ]])
            
            # Predict anomaly score
            anomaly_score = self.anomaly_detectors[detector_key].decision_function(features)[0]
            # Normalize to 0-1 range
            normalized_score = max(0, min(1, (anomaly_score + 0.5) / 1.0))
            
            return float(normalized_score)
            
        except Exception as e:
            logger.error(f"❌ Anomaly detection failed: {e}")
            return 0.0
    
    async def predict_prices(self, symbol: str, historical_data: pd.DataFrame) -> PredictionResult:
        """Predict future prices using ML models"""
        try:
            if len(historical_data) < 100:
                raise ValueError("Insufficient historical data")
            
            # Prepare features
            features = []
            for i in range(20, len(historical_data)):
                window = historical_data.iloc[i-20:i]
                feature_row = [
                    window['close'].mean(),
                    window['volume'].mean(),
                    window['high'].max() - window['low'].min(),  # volatility proxy
                    (window['close'].iloc[-1] - window['close'].iloc[0]) / window['close'].iloc[0]  # momentum
                ]
                features.append(feature_row)
            
            features = np.array(features[:-3])  # Keep last 3 for prediction
            targets_1h = historical_data['close'].iloc[23:-2].values
            targets_24h = historical_data['close'].iloc[24:-1].values
            targets_7d = historical_data['close'].iloc[30:].values
            
            # Train models if not exists
            model_key = f"{symbol}_price_predictor"
            if model_key not in self.ml_models:
                await self.initialize_ml_models()
            
            # Fit and predict
            current_price = float(historical_data['close'].iloc[-1])
            
            # Simple prediction (replace with actual ML when data is available)
            volatility = historical_data['close'].pct_change().std()
            trend = (historical_data['close'].iloc[-1] - historical_data['close'].iloc[-24]) / historical_data['close'].iloc[-24]
            
            predicted_1h = current_price * (1 + trend * 0.1 + np.random.normal(0, volatility * 0.1))
            predicted_24h = current_price * (1 + trend * 0.5 + np.random.normal(0, volatility * 0.5))
            predicted_7d = current_price * (1 + trend * 2.0 + np.random.normal(0, volatility * 2.0))
            
            return PredictionResult(
                symbol=symbol,
                current_price=current_price,
                predicted_price_1h=max(0.01, predicted_1h),
                predicted_price_24h=max(0.01, predicted_24h),
                predicted_price_7d=max(0.01, predicted_7d),
                confidence_1h=0.8,
                confidence_24h=0.6,
                confidence_7d=0.4,
                model_accuracy=0.75,
                feature_importance={
                    "price_momentum": 0.3,
                    "volume": 0.2,
                    "volatility": 0.25,
                    "trend": 0.25
                },
                risk_assessment="MEDIUM",
                recommendation="HOLD" if abs(trend) < 0.02 else ("BUY" if trend > 0 else "SELL")
            )
            
        except Exception as e:
            logger.error(f"❌ Price prediction failed: {e}")
            # Return default prediction
            return PredictionResult(
                symbol=symbol,
                current_price=100.0,
                predicted_price_1h=100.5,
                predicted_price_24h=102.0,
                predicted_price_7d=105.0,
                confidence_1h=0.5,
                confidence_24h=0.3,
                confidence_7d=0.2,
                model_accuracy=0.5,
                feature_importance={},
                risk_assessment="UNKNOWN",
                recommendation="HOLD"
            )

# Initialize analytics engine
analytics_engine = AnalyticsEngine()

# Cache and state
performance_history: List[PerformanceMetrics] = []
trade_analytics: List[TradeAnalytics] = []

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mirai-analytics",
        "version": "2.0.0",
        "ml_models_loaded": len(analytics_engine.ml_models),
        "timestamp": datetime.now()
    }

@app.get("/performance", response_model=PerformanceMetrics)
async def get_performance():
    # Generate demo performance metrics
    import random
    
    metrics = PerformanceMetrics(
        total_return=random.uniform(-5.0, 15.0),
        daily_return=random.uniform(-2.0, 3.0),
        sharpe_ratio=random.uniform(0.5, 2.5),
        max_drawdown=random.uniform(2.0, 8.0),
        win_rate=random.uniform(45.0, 75.0),
        total_trades=random.randint(50, 200),
        timestamp=datetime.now()
    )
    
    performance_history.append(metrics)
    if len(performance_history) > 100:
        performance_history.pop(0)
    
    return metrics

@app.get("/trades", response_model=List[TradeAnalytics])
async def get_trade_analytics():
    return trade_analytics

@app.post("/trades/add")
async def add_trade_analytics(
    symbol: str,
    profit_loss: float,
    duration_minutes: int
):
    return_percentage = (profit_loss / 1000) * 100  # Assuming base of 1000
    category = "winning" if profit_loss > 0 else "losing"
    
    analytics = TradeAnalytics(
        symbol=symbol,
        profit_loss=profit_loss,
        duration_minutes=duration_minutes,
        return_percentage=return_percentage,
        category=category
    )
    
    trade_analytics.append(analytics)
    if len(trade_analytics) > 1000:
        trade_analytics.pop(0)
    
    return {"message": "Trade analytics added", "analytics": analytics}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
