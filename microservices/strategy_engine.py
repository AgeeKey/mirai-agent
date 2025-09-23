"""
Strategy Engine Microservice - AI-Powered Trading Strategies
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
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import ta
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mirai Strategy Engine",
    description="🧠 AI-Powered Trading Strategies with Multi-Timeframe Analysis",
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
class TradingSignal(BaseModel):
    signal_id: str = Field(..., description="Unique signal identifier")
    symbol: str = Field(..., description="Trading symbol")
    action: str = Field(..., description="BUY, SELL, HOLD")
    confidence: float = Field(..., ge=0, le=1, description="Signal confidence 0-1")
    strength: float = Field(..., ge=0, le=1, description="Signal strength 0-1")
    price: float = Field(..., gt=0, description="Target price")
    quantity: float = Field(..., gt=0, description="Recommended quantity")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    risk_reward_ratio: float = Field(..., description="Risk/Reward ratio")
    timeframe: str = Field(..., description="Signal timeframe (1m, 5m, 1h, 4h, 1d)")
    strategy: str = Field(..., description="Strategy name")
    reasoning: str = Field(..., description="Signal reasoning")
    technical_score: float = Field(..., ge=0, le=1, description="Technical analysis score")
    ai_score: float = Field(..., ge=0, le=1, description="AI model score")
    sentiment_score: float = Field(..., ge=-1, le=1, description="Market sentiment score")
    volatility_score: float = Field(..., ge=0, le=1, description="Volatility assessment")
    trend_alignment: str = Field(..., description="BULLISH, BEARISH, NEUTRAL")
    market_condition: str = Field(..., description="TRENDING, RANGING, VOLATILE")
    expiry_time: datetime = Field(..., description="Signal expiry time")
    timestamp: datetime = Field(default_factory=datetime.now)

class StrategyConfig(BaseModel):
    name: str = Field(..., description="Strategy name")
    enabled: bool = Field(default=True, description="Strategy enabled status")
    priority: int = Field(..., ge=1, le=10, description="Strategy priority")
    timeframes: List[str] = Field(..., description="Supported timeframes")
    symbols: List[str] = Field(..., description="Supported symbols")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH")
    max_positions: int = Field(..., ge=1, description="Maximum concurrent positions")
    min_confidence: float = Field(..., ge=0, le=1, description="Minimum signal confidence")
    stop_loss_pct: float = Field(..., ge=0, le=1, description="Default stop loss percentage")
    take_profit_pct: float = Field(..., ge=0, description="Default take profit percentage")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class StrategyPerformance(BaseModel):
    strategy_name: str = Field(..., description="Strategy name")
    total_signals: int = Field(..., ge=0, description="Total signals generated")
    successful_signals: int = Field(..., ge=0, description="Successful signals")
    win_rate: float = Field(..., ge=0, le=1, description="Win rate percentage")
    avg_profit: float = Field(..., description="Average profit per signal")
    max_profit: float = Field(..., description="Maximum profit")
    max_loss: float = Field(..., description="Maximum loss")
    total_pnl: float = Field(..., description="Total P&L")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    avg_holding_time: float = Field(..., description="Average holding time in hours")
    last_signal_time: Optional[datetime] = Field(None, description="Last signal timestamp")
    performance_score: float = Field(..., ge=0, le=1, description="Overall performance score")

class MarketAnalysis(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    trend_1h: str = Field(..., description="1-hour trend")
    trend_4h: str = Field(..., description="4-hour trend")
    trend_1d: str = Field(..., description="Daily trend")
    support_levels: List[float] = Field(..., description="Support levels")
    resistance_levels: List[float] = Field(..., description="Resistance levels")
    volatility: float = Field(..., ge=0, description="Current volatility")
    volume_profile: str = Field(..., description="Volume profile analysis")
    momentum: float = Field(..., description="Price momentum")
    mean_reversion_score: float = Field(..., ge=0, le=1, description="Mean reversion probability")
    breakout_probability: float = Field(..., ge=0, le=1, description="Breakout probability")
    market_phase: str = Field(..., description="ACCUMULATION, MARKUP, DISTRIBUTION, MARKDOWN")
    timestamp: datetime = Field(default_factory=datetime.now)

class AIStrategyModel:
    def __init__(self):
        self.models: Dict[str, RandomForestClassifier] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.feature_names = [
            'rsi', 'macd', 'bb_position', 'volume_ratio', 'price_momentum',
            'volatility', 'trend_strength', 'support_distance', 'resistance_distance'
        ]
        
    async def initialize_models(self):
        """Initialize AI models for different timeframes"""
        try:
            timeframes = ['1h', '4h', '1d']
            
            for tf in timeframes:
                # Random Forest for signal classification
                self.models[f"signal_{tf}"] = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
                
                # Scaler for feature normalization
                self.scalers[f"signal_{tf}"] = StandardScaler()
            
            logger.info("✅ AI strategy models initialized")
            
        except Exception as e:
            logger.error(f"❌ AI model initialization failed: {e}")
    
    async def predict_signal(self, features: Dict[str, float], timeframe: str) -> Dict[str, float]:
        """Predict trading signal using AI model"""
        try:
            model_key = f"signal_{timeframe}"
            
            if model_key not in self.models:
                # Return neutral prediction if model not available
                return {
                    "signal_probability": 0.5,
                    "confidence": 0.5,
                    "direction": "HOLD"
                }
            
            # Prepare features
            feature_vector = np.array([[
                features.get('rsi', 50),
                features.get('macd', 0),
                features.get('bb_position', 0.5),
                features.get('volume_ratio', 1),
                features.get('price_momentum', 0),
                features.get('volatility', 0.02),
                features.get('trend_strength', 0.5),
                features.get('support_distance', 0.05),
                features.get('resistance_distance', 0.05)
            ]])
            
            # Simulate prediction (replace with actual trained model)
            signal_prob = np.random.uniform(0.3, 0.8)
            confidence = np.random.uniform(0.6, 0.9)
            
            if signal_prob > 0.6:
                direction = "BUY"
            elif signal_prob < 0.4:
                direction = "SELL"
            else:
                direction = "HOLD"
            
            return {
                "signal_probability": signal_prob,
                "confidence": confidence,
                "direction": direction
            }
            
        except Exception as e:
            logger.error(f"❌ AI signal prediction failed: {e}")
            return {
                "signal_probability": 0.5,
                "confidence": 0.3,
                "direction": "HOLD"
            }

# Strategy Engine
class StrategyEngine:
    def __init__(self):
        self.active_signals: Dict[str, TradingSignal] = {}
        self.strategies: Dict[str, StrategyConfig] = {}
        self.performance_metrics: Dict[str, StrategyPerformance] = {}
        self.ai_model = AIStrategyModel()
        self.is_running = False
        self.market_data_cache = {}
        
        # Initialize default strategies
        self._initialize_default_strategies()
        
    def _initialize_default_strategies(self):
        """Initialize default trading strategies"""
        try:
            # Moving Average Crossover Strategy
            self.strategies["ma_crossover"] = StrategyConfig(
                name="ma_crossover",
                enabled=True,
                priority=7,
                timeframes=["1h", "4h"],
                symbols=["BTCUSDT", "ETHUSDT"],
                parameters={
                    "fast_ma": 12,
                    "slow_ma": 26,
                    "signal_ma": 9
                },
                risk_level="MEDIUM",
                max_positions=3,
                min_confidence=0.6,
                stop_loss_pct=0.02,
                take_profit_pct=0.04
            )
            
            # RSI Mean Reversion Strategy
            self.strategies["rsi_reversion"] = StrategyConfig(
                name="rsi_reversion",
                enabled=True,
                priority=6,
                timeframes=["15m", "1h"],
                symbols=["BTCUSDT", "ETHUSDT", "ADAUSDT"],
                parameters={
                    "rsi_oversold": 30,
                    "rsi_overbought": 70,
                    "rsi_period": 14
                },
                risk_level="LOW",
                max_positions=2,
                min_confidence=0.7,
                stop_loss_pct=0.015,
                take_profit_pct=0.03
            )
            
            # AI Momentum Strategy
            self.strategies["ai_momentum"] = StrategyConfig(
                name="ai_momentum",
                enabled=True,
                priority=9,
                timeframes=["1h", "4h", "1d"],
                symbols=["BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT"],
                parameters={
                    "momentum_threshold": 0.02,
                    "volatility_filter": 0.05,
                    "volume_threshold": 1.5
                },
                risk_level="HIGH",
                max_positions=5,
                min_confidence=0.75,
                stop_loss_pct=0.025,
                take_profit_pct=0.06
            )
            
            # Breakout Strategy
            self.strategies["breakout"] = StrategyConfig(
                name="breakout",
                enabled=True,
                priority=8,
                timeframes=["4h", "1d"],
                symbols=["BTCUSDT", "ETHUSDT"],
                parameters={
                    "breakout_threshold": 0.03,
                    "volume_confirmation": 2.0,
                    "consolidation_period": 20
                },
                risk_level="HIGH",
                max_positions=2,
                min_confidence=0.8,
                stop_loss_pct=0.03,
                take_profit_pct=0.08
            )
            
            logger.info("✅ Default strategies initialized")
            
        except Exception as e:
            logger.error(f"❌ Strategy initialization failed: {e}")

# Initialize strategy engine
strategy_engine = StrategyEngine()

# Cache and state
active_signals: Dict[str, TradingSignal] = {}
strategies: Dict[str, StrategyConfig] = {
    "ma_crossover": StrategyConfig(
        name="ma_crossover",
        enabled=True,
        priority=5,
        timeframes=["1h"],
        symbols=["BTCUSDT"],
        parameters={"fast_period": 12, "slow_period": 26},
        risk_level="MEDIUM",
        max_positions=1,
        min_confidence=0.6,
        stop_loss_pct=0.02,
        take_profit_pct=0.04
    )
}
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
