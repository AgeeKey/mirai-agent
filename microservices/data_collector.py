"""
Data Collector Microservice - Enhanced Real-time Market Data Collection
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncio
import logging
import os
import json
import aiohttp
import websockets
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import redis
from binance.client import Client
from binance.streams import BinanceSocketManager
from binance.exceptions import BinanceAPIException
import ta
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mirai Data Collector",
    description="🌊 Enhanced Real-time Market Data Collection with ML Feature Extraction",
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

# Binance client
try:
    binance_client = Client(
        api_key=os.getenv('BINANCE_API_KEY', ''),
        api_secret=os.getenv('BINANCE_SECRET_KEY', '')
    )
    logger.info("✅ Binance client initialized")
except Exception as e:
    logger.warning(f"⚠️ Binance client initialization failed: {e}")
    binance_client = None

# Enhanced Data Models
class MarketData(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    price: float = Field(..., gt=0, description="Current price")
    volume: float = Field(..., ge=0, description="24h volume")
    timestamp: datetime = Field(default_factory=datetime.now)
    bid: Optional[float] = Field(None, description="Best bid price")
    ask: Optional[float] = Field(None, description="Best ask price")
    high_24h: Optional[float] = Field(None, description="24h high")
    low_24h: Optional[float] = Field(None, description="24h low")
    price_change_24h: Optional[float] = Field(None, description="24h price change %")
    count: Optional[int] = Field(None, description="24h trade count")

class OHLCVData(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    timestamp: datetime = Field(..., description="Candle timestamp")
    open: float = Field(..., gt=0, description="Open price")
    high: float = Field(..., gt=0, description="High price")
    low: float = Field(..., gt=0, description="Low price")
    close: float = Field(..., gt=0, description="Close price")
    volume: float = Field(..., ge=0, description="Volume")
    interval: str = Field(..., description="Time interval (1m, 5m, 1h, etc.)")

class TechnicalIndicators(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    rsi_14: Optional[float] = Field(None, description="RSI 14-period")
    sma_20: Optional[float] = Field(None, description="SMA 20-period")
    sma_50: Optional[float] = Field(None, description="SMA 50-period")
    ema_12: Optional[float] = Field(None, description="EMA 12-period")
    ema_26: Optional[float] = Field(None, description="EMA 26-period")
    macd: Optional[float] = Field(None, description="MACD line")
    macd_signal: Optional[float] = Field(None, description="MACD signal line")
    bollinger_upper: Optional[float] = Field(None, description="Bollinger upper band")
    bollinger_lower: Optional[float] = Field(None, description="Bollinger lower band")
    stoch_k: Optional[float] = Field(None, description="Stochastic %K")
    stoch_d: Optional[float] = Field(None, description="Stochastic %D")
    atr: Optional[float] = Field(None, description="Average True Range")
    timestamp: datetime = Field(default_factory=datetime.now)

class MLFeatures(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    price_momentum_1h: float = Field(..., description="1-hour price momentum")
    price_momentum_4h: float = Field(..., description="4-hour price momentum")
    price_momentum_24h: float = Field(..., description="24-hour price momentum")
    volatility_1h: float = Field(..., description="1-hour volatility")
    volatility_24h: float = Field(..., description="24-hour volatility")
    volume_ratio: float = Field(..., description="Current volume / average volume ratio")
    trend_strength: float = Field(..., description="Trend strength indicator")
    support_resistance_distance: float = Field(..., description="Distance to nearest support/resistance")
    market_dominance: float = Field(..., description="Market dominance score")
    correlation_btc: float = Field(..., description="Correlation with BTC")
    timestamp: datetime = Field(default_factory=datetime.now)

class HealthCheck(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime
    redis_connected: bool
    binance_connected: bool
    active_streams: int
    data_quality_score: float

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscribed_symbols: Set[str] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"📡 New WebSocket connection: {len(self.active_connections)} total")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"📡 WebSocket disconnected: {len(self.active_connections)} remaining")
    
    async def broadcast_market_data(self, data: Dict[str, Any]):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(data, default=str))
            except Exception:
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

# Data Collection Engine
class DataCollectionEngine:
    def __init__(self):
        self.market_data_cache: Dict[str, MarketData] = {}
        self.ohlcv_cache: Dict[str, List[OHLCVData]] = {}
        self.indicators_cache: Dict[str, TechnicalIndicators] = {}
        self.ml_features_cache: Dict[str, MLFeatures] = {}
        self.websocket_connections: Dict[str, Any] = {}
        self.is_collecting = False
        self.subscribed_symbols = {'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'BNBUSDT', 'SOLUSDT'}
        
    async def start_data_collection(self):
        """Start comprehensive data collection"""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        logger.info("🚀 Starting enhanced data collection...")
        
        # Start background tasks
        asyncio.create_task(self.collect_ticker_data())
        asyncio.create_task(self.collect_ohlcv_data())
        asyncio.create_task(self.calculate_technical_indicators())
        asyncio.create_task(self.extract_ml_features())
        
        if binance_client:
            asyncio.create_task(self.binance_websocket_stream())
        
        logger.info("✅ Data collection started")
    
    async def collect_ticker_data(self):
        """Collect real-time ticker data"""
        while self.is_collecting:
            try:
                if binance_client:
                    tickers = binance_client.get_ticker()
                    
                    for ticker in tickers:
                        symbol = ticker['symbol']
                        if symbol in self.subscribed_symbols:
                            market_data = MarketData(
                                symbol=symbol,
                                price=float(ticker['lastPrice']),
                                volume=float(ticker['volume']),
                                bid=float(ticker['bidPrice']) if ticker['bidPrice'] else None,
                                ask=float(ticker['askPrice']) if ticker['askPrice'] else None,
                                high_24h=float(ticker['highPrice']),
                                low_24h=float(ticker['lowPrice']),
                                price_change_24h=float(ticker['priceChangePercent']),
                                count=int(ticker['count'])
                            )
                            
                            self.market_data_cache[symbol] = market_data
                            
                            # Cache in Redis
                            if redis_client:
                                redis_client.setex(
                                    f"market_data:{symbol}",
                                    60,  # 1 minute TTL
                                    json.dumps(market_data.dict(), default=str)
                                )
                            
                            # Broadcast to WebSocket clients
                            await manager.broadcast_market_data({
                                "type": "ticker_update",
                                "symbol": symbol,
                                "data": market_data.dict()
                            })
                
                await asyncio.sleep(1)  # Update every second
                
            except Exception as e:
                logger.error(f"❌ Ticker data collection error: {e}")
                await asyncio.sleep(5)
    
    async def collect_ohlcv_data(self):
        """Collect OHLCV candlestick data"""
        intervals = ['1m', '5m', '15m', '1h', '4h', '1d']
        
        while self.is_collecting:
            try:
                if binance_client:
                    for symbol in self.subscribed_symbols:
                        for interval in intervals:
                            klines = binance_client.get_klines(
                                symbol=symbol,
                                interval=interval,
                                limit=100
                            )
                            
                            ohlcv_data = []
                            for kline in klines:
                                ohlcv = OHLCVData(
                                    symbol=symbol,
                                    timestamp=datetime.fromtimestamp(kline[0] / 1000),
                                    open=float(kline[1]),
                                    high=float(kline[2]),
                                    low=float(kline[3]),
                                    close=float(kline[4]),
                                    volume=float(kline[5]),
                                    interval=interval
                                )
                                ohlcv_data.append(ohlcv)
                            
                            cache_key = f"{symbol}_{interval}"
                            self.ohlcv_cache[cache_key] = ohlcv_data
                            
                            # Cache in Redis
                            if redis_client:
                                redis_client.setex(
                                    f"ohlcv:{cache_key}",
                                    300,  # 5 minutes TTL
                                    json.dumps([o.dict() for o in ohlcv_data[-50:]], default=str)
                                )
                
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"❌ OHLCV data collection error: {e}")
                await asyncio.sleep(30)

# Cache and state
manager = ConnectionManager()
data_engine = DataCollectionEngine()
market_data_cache: Dict[str, MarketData] = {}
is_collecting = False

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Enhanced health check with comprehensive status"""
    redis_connected = True
    binance_connected = True
    
    try:
        if redis_client:
            redis_client.ping()
    except:
        redis_connected = False
    
    try:
        if binance_client:
            binance_client.ping()
    except:
        binance_connected = False
    
    # Calculate data quality score
    quality_score = 0.0
    if data_engine.market_data_cache:
        quality_score += 0.4
    if data_engine.ohlcv_cache:
        quality_score += 0.3
    if data_engine.indicators_cache:
        quality_score += 0.2
    if data_engine.ml_features_cache:
        quality_score += 0.1
    
    return HealthCheck(
        status="healthy" if redis_connected else "degraded",
        service="data-collector",
        timestamp=datetime.now(),
        redis_connected=redis_connected
    )

@app.get("/status")
async def get_status():
    return {
        "collecting": is_collecting,
        "symbols_tracked": len(market_data_cache),
        "last_update": max([data.timestamp for data in market_data_cache.values()]) if market_data_cache else None,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/data/{symbol}", response_model=MarketData)
async def get_market_data(symbol: str):
    if symbol not in market_data_cache:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    return market_data_cache[symbol]

@app.get("/data", response_model=List[MarketData])
async def get_all_market_data():
    return list(market_data_cache.values())

@app.post("/start")
async def start_collection():
    global is_collecting
    is_collecting = True
    
    # Demo data for production testing
    demo_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "BNBUSDT"]
    import random
    
    for symbol in demo_symbols:
        market_data = MarketData(
            symbol=symbol,
            price=random.uniform(1000, 50000),
            volume=random.uniform(1000000, 10000000),
            timestamp=datetime.now(),
            bid=random.uniform(1000, 50000),
            ask=random.uniform(1000, 50000)
        )
        market_data_cache[symbol] = market_data
        
        # Store in Redis
        try:
            redis_client.setex(f"market_data:{symbol}", 3600, json.dumps(market_data.dict(), default=str))
        except:
            pass
    
    return {"message": "Data collection started", "symbols": demo_symbols}

@app.post("/stop")
async def stop_collection():
    global is_collecting
    is_collecting = False
    return {"message": "Data collection stopped"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
