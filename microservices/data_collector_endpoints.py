"""
Data Collector Endpoints - Enhanced Real-time Market Data API
"""

from fastapi import HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Query
from fastapi.responses import JSONResponse
import asyncio
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import ta

# Import from data_collector.py
from data_collector import (
    app, redis_client, binance_client, MarketData, OHLCVData, TechnicalIndicators,
    MLFeatures, HealthCheck, ConnectionManager, DataCollectionEngine, manager,
    data_engine, market_data_cache, is_collecting, logger
)

# Continue DataCollectionEngine implementation
async def calculate_technical_indicators_method(self):
    """Calculate technical indicators for all symbols"""
    while self.is_collecting:
        try:
            for symbol in self.subscribed_symbols:
                # Get 1h OHLCV data for indicators
                cache_key = f"{symbol}_1h"
                if cache_key in self.ohlcv_cache:
                    ohlcv_data = self.ohlcv_cache[cache_key]
                    
                    if len(ohlcv_data) >= 50:  # Need sufficient data
                        # Convert to DataFrame
                        df = pd.DataFrame([{
                            'close': o.close,
                            'high': o.high,
                            'low': o.low,
                            'volume': o.volume
                        } for o in ohlcv_data])
                        
                        # Calculate indicators
                        indicators = TechnicalIndicators(symbol=symbol)
                        
                        try:
                            # RSI
                            indicators.rsi_14 = ta.momentum.RSIIndicator(df['close']).rsi().iloc[-1]
                            
                            # Moving averages
                            indicators.sma_20 = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator().iloc[-1]
                            indicators.sma_50 = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator().iloc[-1]
                            indicators.ema_12 = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator().iloc[-1]
                            indicators.ema_26 = ta.trend.EMAIndicator(df['close'], window=26).ema_indicator().iloc[-1]
                            
                            # MACD
                            macd_indicator = ta.trend.MACD(df['close'])
                            indicators.macd = macd_indicator.macd().iloc[-1]
                            indicators.macd_signal = macd_indicator.macd_signal().iloc[-1]
                            
                            # Bollinger Bands
                            bb_indicator = ta.volatility.BollingerBands(df['close'])
                            indicators.bollinger_upper = bb_indicator.bollinger_hband().iloc[-1]
                            indicators.bollinger_lower = bb_indicator.bollinger_lband().iloc[-1]
                            
                            # Stochastic
                            stoch_indicator = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
                            indicators.stoch_k = stoch_indicator.stoch().iloc[-1]
                            indicators.stoch_d = stoch_indicator.stoch_signal().iloc[-1]
                            
                            # ATR
                            indicators.atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range().iloc[-1]
                            
                            self.indicators_cache[symbol] = indicators
                            
                            # Cache in Redis
                            if redis_client:
                                redis_client.setex(
                                    f"indicators:{symbol}",
                                    300,  # 5 minutes TTL
                                    json.dumps(indicators.dict(), default=str)
                                )
                            
                        except Exception as e:
                            logger.warning(f"Indicators calculation failed for {symbol}: {e}")
            
            await asyncio.sleep(300)  # Update every 5 minutes
            
        except Exception as e:
            logger.error(f"❌ Technical indicators calculation error: {e}")
            await asyncio.sleep(60)

async def extract_ml_features_method(self):
    """Extract ML features for analytics engine"""
    while self.is_collecting:
        try:
            for symbol in self.subscribed_symbols:
                # Get multiple timeframe data
                h1_key = f"{symbol}_1h"
                h4_key = f"{symbol}_4h"
                d1_key = f"{symbol}_1d"
                
                if all(key in self.ohlcv_cache for key in [h1_key, h4_key, d1_key]):
                    h1_data = self.ohlcv_cache[h1_key]
                    h4_data = self.ohlcv_cache[h4_key]
                    d1_data = self.ohlcv_cache[d1_key]
                    
                    if len(h1_data) >= 24 and len(h4_data) >= 6 and len(d1_data) >= 2:
                        current_price = h1_data[-1].close
                        
                        # Calculate momentum features
                        price_1h_ago = h1_data[-2].close if len(h1_data) >= 2 else current_price
                        price_4h_ago = h4_data[-2].close if len(h4_data) >= 2 else current_price
                        price_24h_ago = d1_data[-2].close if len(d1_data) >= 2 else current_price
                        
                        momentum_1h = (current_price - price_1h_ago) / price_1h_ago
                        momentum_4h = (current_price - price_4h_ago) / price_4h_ago
                        momentum_24h = (current_price - price_24h_ago) / price_24h_ago
                        
                        # Calculate volatility
                        h1_prices = [o.close for o in h1_data[-24:]]
                        h1_returns = np.diff(h1_prices) / h1_prices[:-1]
                        volatility_1h = np.std(h1_returns) if len(h1_returns) > 0 else 0
                        
                        d1_prices = [o.close for o in d1_data[-7:]]
                        d1_returns = np.diff(d1_prices) / d1_prices[:-1]
                        volatility_24h = np.std(d1_returns) if len(d1_returns) > 0 else 0
                        
                        # Volume analysis
                        current_volume = h1_data[-1].volume
                        avg_volume = np.mean([o.volume for o in h1_data[-24:]])
                        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
                        
                        # Trend strength (simplified)
                        trend_strength = abs(momentum_24h) * 10  # Scale to 0-1 range approximately
                        trend_strength = min(1.0, max(0.0, trend_strength))
                        
                        # Support/Resistance distance (simplified)
                        recent_highs = [o.high for o in h1_data[-24:]]
                        recent_lows = [o.low for o in h1_data[-24:]]
                        resistance = max(recent_highs)
                        support = min(recent_lows)
                        
                        dist_to_resistance = (resistance - current_price) / current_price
                        dist_to_support = (current_price - support) / current_price
                        sr_distance = min(dist_to_resistance, dist_to_support)
                        
                        # Market dominance (simplified - could use actual market cap data)
                        market_dominance = 0.5 if symbol == 'BTCUSDT' else 0.1
                        
                        # BTC correlation (simplified)
                        btc_correlation = 1.0 if symbol == 'BTCUSDT' else np.random.uniform(0.3, 0.8)
                        
                        ml_features = MLFeatures(
                            symbol=symbol,
                            price_momentum_1h=momentum_1h,
                            price_momentum_4h=momentum_4h,
                            price_momentum_24h=momentum_24h,
                            volatility_1h=volatility_1h,
                            volatility_24h=volatility_24h,
                            volume_ratio=volume_ratio,
                            trend_strength=trend_strength,
                            support_resistance_distance=sr_distance,
                            market_dominance=market_dominance,
                            correlation_btc=btc_correlation
                        )
                        
                        self.ml_features_cache[symbol] = ml_features
                        
                        # Cache in Redis for analytics engine
                        if redis_client:
                            redis_client.setex(
                                f"ml_features:{symbol}",
                                600,  # 10 minutes TTL
                                json.dumps(ml_features.dict(), default=str)
                            )
                        
                        # Send to analytics service
                        analytics_url = os.getenv('ANALYTICS_URL')
                        if analytics_url:
                            try:
                                async with aiohttp.ClientSession() as session:
                                    async with session.post(
                                        f"{analytics_url}/features/update",
                                        json=ml_features.dict()
                                    ) as response:
                                        if response.status != 200:
                                            logger.warning(f"Failed to send features to analytics: {response.status}")
                            except Exception as e:
                                logger.warning(f"Analytics service communication failed: {e}")
            
            await asyncio.sleep(600)  # Update every 10 minutes
            
        except Exception as e:
            logger.error(f"❌ ML features extraction error: {e}")
            await asyncio.sleep(120)

async def binance_websocket_stream_method(self):
    """Real-time Binance WebSocket stream"""
    try:
        from binance.streams import BinanceSocketManager
        
        bm = BinanceSocketManager(binance_client)
        
        # Create streams for subscribed symbols
        streams = []
        for symbol in self.subscribed_symbols:
            streams.append(f"{symbol.lower()}@ticker")
            streams.append(f"{symbol.lower()}@kline_1m")
        
        async def handle_socket_message(msg):
            try:
                if msg['e'] == '24hrTicker':
                    # Ticker update
                    symbol = msg['s']
                    if symbol in self.subscribed_symbols:
                        market_data = MarketData(
                            symbol=symbol,
                            price=float(msg['c']),
                            volume=float(msg['v']),
                            bid=float(msg['b']),
                            ask=float(msg['a']),
                            high_24h=float(msg['h']),
                            low_24h=float(msg['l']),
                            price_change_24h=float(msg['P']),
                            count=int(msg['n'])
                        )
                        
                        self.market_data_cache[symbol] = market_data
                        
                        # Broadcast real-time update
                        await manager.broadcast_market_data({
                            "type": "realtime_ticker",
                            "symbol": symbol,
                            "data": market_data.dict()
                        })
                
                elif msg['e'] == 'kline':
                    # Kline update
                    kline_data = msg['k']
                    symbol = kline_data['s']
                    
                    if symbol in self.subscribed_symbols and kline_data['x']:  # Closed kline
                        ohlcv = OHLCVData(
                            symbol=symbol,
                            timestamp=datetime.fromtimestamp(kline_data['t'] / 1000),
                            open=float(kline_data['o']),
                            high=float(kline_data['h']),
                            low=float(kline_data['l']),
                            close=float(kline_data['c']),
                            volume=float(kline_data['v']),
                            interval='1m'
                        )
                        
                        # Update cache
                        cache_key = f"{symbol}_1m"
                        if cache_key not in self.ohlcv_cache:
                            self.ohlcv_cache[cache_key] = []
                        
                        self.ohlcv_cache[cache_key].append(ohlcv)
                        # Keep only last 1000 candles
                        if len(self.ohlcv_cache[cache_key]) > 1000:
                            self.ohlcv_cache[cache_key] = self.ohlcv_cache[cache_key][-1000:]
                        
                        # Broadcast kline update
                        await manager.broadcast_market_data({
                            "type": "kline_update",
                            "symbol": symbol,
                            "data": ohlcv.dict()
                        })
            
            except Exception as e:
                logger.error(f"❌ WebSocket message handling error: {e}")
        
        # Start multiplex socket
        ms = bm.multiplex_socket(streams)
        ms.start()
        
        async for msg in ms:
            await handle_socket_message(msg)
    
    except Exception as e:
        logger.error(f"❌ Binance WebSocket stream error: {e}")
        await asyncio.sleep(30)
        # Retry connection
        if self.is_collecting:
            asyncio.create_task(self.binance_websocket_stream())

# Patch methods to DataCollectionEngine
DataCollectionEngine.calculate_technical_indicators = calculate_technical_indicators_method
DataCollectionEngine.extract_ml_features = extract_ml_features_method
DataCollectionEngine.binance_websocket_stream = binance_websocket_stream_method

# Complete health check implementation
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
        status="healthy" if quality_score > 0.5 else "degraded",
        service="mirai-data-collector",
        version="2.0.0",
        timestamp=datetime.now(),
        redis_connected=redis_connected,
        binance_connected=binance_connected,
        active_streams=len(data_engine.subscribed_symbols),
        data_quality_score=quality_score
    )

# API Endpoints
@app.get("/market-data/{symbol}", response_model=MarketData)
async def get_market_data(symbol: str):
    """📊 Get current market data for a symbol"""
    try:
        symbol = symbol.upper()
        
        if symbol in data_engine.market_data_cache:
            return data_engine.market_data_cache[symbol]
        
        # Try to get from Redis cache
        if redis_client:
            cached_data = redis_client.get(f"market_data:{symbol}")
            if cached_data:
                data_dict = json.loads(cached_data)
                return MarketData(**data_dict)
        
        raise HTTPException(status_code=404, detail=f"Market data not found for {symbol}")
        
    except Exception as e:
        logger.error(f"❌ Get market data failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ohlcv/{symbol}")
async def get_ohlcv_data(
    symbol: str,
    interval: str = Query("1h", description="Time interval"),
    limit: int = Query(100, ge=1, le=1000, description="Number of candles")
):
    """📈 Get OHLCV candlestick data"""
    try:
        symbol = symbol.upper()
        cache_key = f"{symbol}_{interval}"
        
        if cache_key in data_engine.ohlcv_cache:
            ohlcv_data = data_engine.ohlcv_cache[cache_key][-limit:]
            return {
                "symbol": symbol,
                "interval": interval,
                "data": [o.dict() for o in ohlcv_data],
                "count": len(ohlcv_data)
            }
        
        raise HTTPException(status_code=404, detail=f"OHLCV data not found for {symbol} {interval}")
        
    except Exception as e:
        logger.error(f"❌ Get OHLCV data failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/indicators/{symbol}", response_model=TechnicalIndicators)
async def get_technical_indicators(symbol: str):
    """🔍 Get technical indicators for a symbol"""
    try:
        symbol = symbol.upper()
        
        if symbol in data_engine.indicators_cache:
            return data_engine.indicators_cache[symbol]
        
        raise HTTPException(status_code=404, detail=f"Technical indicators not found for {symbol}")
        
    except Exception as e:
        logger.error(f"❌ Get indicators failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ml-features/{symbol}", response_model=MLFeatures)
async def get_ml_features(symbol: str):
    """🤖 Get ML features for a symbol"""
    try:
        symbol = symbol.upper()
        
        if symbol in data_engine.ml_features_cache:
            return data_engine.ml_features_cache[symbol]
        
        raise HTTPException(status_code=404, detail=f"ML features not found for {symbol}")
        
    except Exception as e:
        logger.error(f"❌ Get ML features failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/symbols")
async def get_available_symbols():
    """📋 Get list of available symbols"""
    return {
        "subscribed_symbols": list(data_engine.subscribed_symbols),
        "active_data": list(data_engine.market_data_cache.keys()),
        "total_symbols": len(data_engine.subscribed_symbols)
    }

@app.post("/symbols/subscribe")
async def subscribe_symbol(symbol: str):
    """➕ Subscribe to a new symbol"""
    try:
        symbol = symbol.upper()
        data_engine.subscribed_symbols.add(symbol)
        manager.subscribed_symbols.add(symbol)
        
        return {"message": f"Subscribed to {symbol}", "total_symbols": len(data_engine.subscribed_symbols)}
        
    except Exception as e:
        logger.error(f"❌ Symbol subscription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/symbols/unsubscribe")
async def unsubscribe_symbol(symbol: str):
    """➖ Unsubscribe from a symbol"""
    try:
        symbol = symbol.upper()
        data_engine.subscribed_symbols.discard(symbol)
        manager.subscribed_symbols.discard(symbol)
        
        # Clean up cache
        if symbol in data_engine.market_data_cache:
            del data_engine.market_data_cache[symbol]
        
        return {"message": f"Unsubscribed from {symbol}", "total_symbols": len(data_engine.subscribed_symbols)}
        
    except Exception as e:
        logger.error(f"❌ Symbol unsubscription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/collection/start")
async def start_collection(background_tasks: BackgroundTasks):
    """🚀 Start data collection"""
    try:
        background_tasks.add_task(data_engine.start_data_collection)
        return {"message": "Data collection started", "status": "started"}
        
    except Exception as e:
        logger.error(f"❌ Start collection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/collection/stop")
async def stop_collection():
    """🛑 Stop data collection"""
    try:
        data_engine.is_collecting = False
        return {"message": "Data collection stopped", "status": "stopped"}
        
    except Exception as e:
        logger.error(f"❌ Stop collection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collection/status")
async def get_collection_status():
    """📊 Get data collection status"""
    return {
        "is_collecting": data_engine.is_collecting,
        "subscribed_symbols": len(data_engine.subscribed_symbols),
        "cached_market_data": len(data_engine.market_data_cache),
        "cached_ohlcv": len(data_engine.ohlcv_cache),
        "cached_indicators": len(data_engine.indicators_cache),
        "cached_ml_features": len(data_engine.ml_features_cache),
        "websocket_connections": len(manager.active_connections),
        "last_update": datetime.now()
    }

# WebSocket endpoint for real-time data
@app.websocket("/ws/market-data")
async def websocket_market_data(websocket: WebSocket):
    """🔄 Real-time market data WebSocket"""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic heartbeat
            await asyncio.sleep(10)
            await websocket.send_text(json.dumps({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "active_symbols": len(data_engine.subscribed_symbols)
            }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize data collector on startup"""
    logger.info("🚀 Starting Mirai Data Collector...")
    
    # Auto-start data collection
    await data_engine.start_data_collection()
    
    logger.info("✅ Data Collector startup completed")

# Legacy endpoints for compatibility
@app.get("/market_data")
async def get_legacy_market_data():
    """📊 Get all market data (legacy compatibility)"""
    return {"market_data": [data.dict() for data in data_engine.market_data_cache.values()]}

@app.post("/market_data")
async def add_legacy_market_data(data: MarketData):
    """➕ Add market data (legacy compatibility)"""
    data_engine.market_data_cache[data.symbol] = data
    return {"message": "Market data added", "symbol": data.symbol}