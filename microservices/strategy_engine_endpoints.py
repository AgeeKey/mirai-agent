"""
Strategy Engine Endpoints - AI-Powered Trading Strategies API
"""

from fastapi import HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse
import asyncio
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid

# Import from strategy_engine.py
from strategy_engine import (
    app, redis_client, TradingSignal, StrategyConfig, StrategyPerformance,
    MarketAnalysis, AIStrategyModel, StrategyEngine, strategy_engine,
    active_signals, strategies, logger
)

# Strategy Implementation Methods
async def generate_ma_crossover_signal(self, symbol: str, timeframe: str, market_data: Dict) -> Optional[TradingSignal]:
    """Generate Moving Average Crossover signals"""
    try:
        strategy = self.strategies.get("ma_crossover")
        if not strategy or not strategy.enabled:
            return None
        
        # Get OHLCV data from data collector
        data_collector_url = os.getenv('DATA_COLLECTOR_URL', 'http://localhost:8004')
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{data_collector_url}/ohlcv/{symbol}?interval={timeframe}&limit=50") as response:
                if response.status != 200:
                    return None
                
                ohlcv_response = await response.json()
                ohlcv_data = ohlcv_response.get('data', [])
                
                if len(ohlcv_data) < 30:
                    return None
                
                # Convert to DataFrame
                df = pd.DataFrame(ohlcv_data)
                df['close'] = df['close'].astype(float)
                
                # Calculate moving averages
                fast_ma = strategy.parameters.get('fast_ma', 12)
                slow_ma = strategy.parameters.get('slow_ma', 26)
                
                df['ma_fast'] = df['close'].rolling(window=fast_ma).mean()
                df['ma_slow'] = df['close'].rolling(window=slow_ma).mean()
                
                # Get current and previous values
                current_fast = df['ma_fast'].iloc[-1]
                current_slow = df['ma_slow'].iloc[-1]
                prev_fast = df['ma_fast'].iloc[-2]
                prev_slow = df['ma_slow'].iloc[-2]
                
                current_price = df['close'].iloc[-1]
                
                # Detect crossover
                signal_action = "HOLD"
                confidence = 0.5
                
                if prev_fast <= prev_slow and current_fast > current_slow:
                    # Golden cross - bullish signal
                    signal_action = "BUY"
                    confidence = min(0.9, 0.6 + abs(current_fast - current_slow) / current_slow)
                elif prev_fast >= prev_slow and current_fast < current_slow:
                    # Death cross - bearish signal
                    signal_action = "SELL"
                    confidence = min(0.9, 0.6 + abs(current_fast - current_slow) / current_slow)
                
                if signal_action != "HOLD" and confidence >= strategy.min_confidence:
                    signal_id = f"ma_crossover_{symbol}_{timeframe}_{int(datetime.now().timestamp())}"
                    
                    # Calculate stop loss and take profit
                    if signal_action == "BUY":
                        stop_loss = current_price * (1 - strategy.stop_loss_pct)
                        take_profit = current_price * (1 + strategy.take_profit_pct)
                    else:
                        stop_loss = current_price * (1 + strategy.stop_loss_pct)
                        take_profit = current_price * (1 - strategy.take_profit_pct)
                    
                    risk_reward = abs(take_profit - current_price) / abs(current_price - stop_loss)
                    
                    return TradingSignal(
                        signal_id=signal_id,
                        symbol=symbol,
                        action=signal_action,
                        confidence=confidence,
                        strength=confidence * 0.8,
                        price=current_price,
                        quantity=1000,  # Will be adjusted by portfolio manager
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        risk_reward_ratio=risk_reward,
                        timeframe=timeframe,
                        strategy="ma_crossover",
                        reasoning=f"MA crossover detected: {fast_ma}MA = {current_fast:.2f}, {slow_ma}MA = {current_slow:.2f}",
                        technical_score=confidence,
                        ai_score=0.5,
                        sentiment_score=0.0,
                        volatility_score=0.5,
                        trend_alignment="BULLISH" if signal_action == "BUY" else "BEARISH",
                        market_condition="TRENDING",
                        expiry_time=datetime.now() + timedelta(hours=2)
                    )
        
        return None
        
    except Exception as e:
        logger.error(f"❌ MA crossover signal generation failed: {e}")
        return None

async def generate_rsi_reversion_signal(self, symbol: str, timeframe: str, market_data: Dict) -> Optional[TradingSignal]:
    """Generate RSI Mean Reversion signals"""
    try:
        strategy = self.strategies.get("rsi_reversion")
        if not strategy or not strategy.enabled:
            return None
        
        # Get technical indicators
        data_collector_url = os.getenv('DATA_COLLECTOR_URL', 'http://localhost:8004')
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{data_collector_url}/indicators/{symbol}") as response:
                if response.status != 200:
                    return None
                
                indicators = await response.json()
                rsi = indicators.get('rsi_14')
                
                if rsi is None:
                    return None
                
                current_price = market_data.get('price', 0)
                if current_price <= 0:
                    return None
                
                # RSI signal logic
                signal_action = "HOLD"
                confidence = 0.5
                
                rsi_oversold = strategy.parameters.get('rsi_oversold', 30)
                rsi_overbought = strategy.parameters.get('rsi_overbought', 70)
                
                if rsi <= rsi_oversold:
                    # Oversold - potential buy signal
                    signal_action = "BUY"
                    confidence = min(0.9, 0.6 + (rsi_oversold - rsi) / rsi_oversold)
                elif rsi >= rsi_overbought:
                    # Overbought - potential sell signal
                    signal_action = "SELL"
                    confidence = min(0.9, 0.6 + (rsi - rsi_overbought) / (100 - rsi_overbought))
                
                if signal_action != "HOLD" and confidence >= strategy.min_confidence:
                    signal_id = f"rsi_reversion_{symbol}_{timeframe}_{int(datetime.now().timestamp())}"
                    
                    # Calculate stop loss and take profit
                    if signal_action == "BUY":
                        stop_loss = current_price * (1 - strategy.stop_loss_pct)
                        take_profit = current_price * (1 + strategy.take_profit_pct)
                    else:
                        stop_loss = current_price * (1 + strategy.stop_loss_pct)
                        take_profit = current_price * (1 - strategy.take_profit_pct)
                    
                    risk_reward = abs(take_profit - current_price) / abs(current_price - stop_loss)
                    
                    return TradingSignal(
                        signal_id=signal_id,
                        symbol=symbol,
                        action=signal_action,
                        confidence=confidence,
                        strength=confidence * 0.9,
                        price=current_price,
                        quantity=500,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        risk_reward_ratio=risk_reward,
                        timeframe=timeframe,
                        strategy="rsi_reversion",
                        reasoning=f"RSI mean reversion: RSI = {rsi:.1f}, threshold = {rsi_oversold if signal_action == 'BUY' else rsi_overbought}",
                        technical_score=confidence,
                        ai_score=0.5,
                        sentiment_score=0.0,
                        volatility_score=0.3,
                        trend_alignment="NEUTRAL",
                        market_condition="RANGING",
                        expiry_time=datetime.now() + timedelta(hours=1)
                    )
        
        return None
        
    except Exception as e:
        logger.error(f"❌ RSI reversion signal generation failed: {e}")
        return None

async def generate_ai_momentum_signal(self, symbol: str, timeframe: str, market_data: Dict) -> Optional[TradingSignal]:
    """Generate AI-powered momentum signals"""
    try:
        strategy = self.strategies.get("ai_momentum")
        if not strategy or not strategy.enabled:
            return None
        
        # Get ML features and indicators
        data_collector_url = os.getenv('DATA_COLLECTOR_URL', 'http://localhost:8004')
        ai_engine_url = os.getenv('AI_ENGINE_URL', 'http://localhost:8001')
        
        # Collect all required data
        ml_features = None
        indicators = None
        ai_analysis = None
        
        async with aiohttp.ClientSession() as session:
            # Get ML features
            try:
                async with session.get(f"{data_collector_url}/ml-features/{symbol}") as response:
                    if response.status == 200:
                        ml_features = await response.json()
            except Exception as e:
                logger.warning(f"Failed to get ML features: {e}")
            
            # Get technical indicators
            try:
                async with session.get(f"{data_collector_url}/indicators/{symbol}") as response:
                    if response.status == 200:
                        indicators = await response.json()
            except Exception as e:
                logger.warning(f"Failed to get indicators: {e}")
            
            # Get AI analysis
            try:
                async with session.post(f"{ai_engine_url}/analyze/signal", json={
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "features": ml_features or {},
                    "indicators": indicators or {}
                }) as response:
                    if response.status == 200:
                        ai_analysis = await response.json()
            except Exception as e:
                logger.warning(f"Failed to get AI analysis: {e}")
        
        if not ml_features or not indicators:
            return None
        
        # Combine signals
        current_price = market_data.get('price', 0)
        momentum_24h = ml_features.get('price_momentum_24h', 0)
        volatility = ml_features.get('volatility_24h', 0)
        volume_ratio = ml_features.get('volume_ratio', 1)
        rsi = indicators.get('rsi_14', 50)
        
        # AI model prediction
        features = {
            'rsi': rsi,
            'macd': indicators.get('macd', 0),
            'bb_position': (current_price - indicators.get('bollinger_lower', current_price)) / 
                          (indicators.get('bollinger_upper', current_price) - indicators.get('bollinger_lower', current_price)),
            'volume_ratio': volume_ratio,
            'price_momentum': momentum_24h,
            'volatility': volatility,
            'trend_strength': ml_features.get('trend_strength', 0.5),
            'support_distance': ml_features.get('support_resistance_distance', 0.05),
            'resistance_distance': ml_features.get('support_resistance_distance', 0.05)
        }
        
        ai_prediction = await self.ai_model.predict_signal(features, timeframe)
        
        # Strategy logic
        momentum_threshold = strategy.parameters.get('momentum_threshold', 0.02)
        volatility_filter = strategy.parameters.get('volatility_filter', 0.05)
        volume_threshold = strategy.parameters.get('volume_threshold', 1.5)
        
        signal_action = "HOLD"
        confidence = 0.5
        
        # Strong momentum with volume confirmation
        if (abs(momentum_24h) > momentum_threshold and 
            volatility < volatility_filter and 
            volume_ratio > volume_threshold and
            ai_prediction['direction'] != "HOLD"):
            
            signal_action = ai_prediction['direction']
            
            # Combine technical and AI confidence
            technical_confidence = min(0.9, abs(momentum_24h) / momentum_threshold * 0.5 + 0.3)
            ai_confidence = ai_prediction['confidence']
            confidence = (technical_confidence + ai_confidence) / 2
        
        if signal_action != "HOLD" and confidence >= strategy.min_confidence:
            signal_id = f"ai_momentum_{symbol}_{timeframe}_{int(datetime.now().timestamp())}"
            
            # Calculate stop loss and take profit
            if signal_action == "BUY":
                stop_loss = current_price * (1 - strategy.stop_loss_pct)
                take_profit = current_price * (1 + strategy.take_profit_pct)
            else:
                stop_loss = current_price * (1 + strategy.stop_loss_pct)
                take_profit = current_price * (1 - strategy.take_profit_pct)
            
            risk_reward = abs(take_profit - current_price) / abs(current_price - stop_loss)
            
            return TradingSignal(
                signal_id=signal_id,
                symbol=symbol,
                action=signal_action,
                confidence=confidence,
                strength=confidence,
                price=current_price,
                quantity=2000,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward_ratio=risk_reward,
                timeframe=timeframe,
                strategy="ai_momentum",
                reasoning=f"AI momentum signal: 24h momentum = {momentum_24h:.3f}, AI confidence = {ai_confidence:.2f}",
                technical_score=technical_confidence,
                ai_score=ai_confidence,
                sentiment_score=ai_analysis.get('sentiment_score', 0) if ai_analysis else 0,
                volatility_score=min(1.0, volatility / 0.1),
                trend_alignment="BULLISH" if signal_action == "BUY" else "BEARISH",
                market_condition="TRENDING",
                expiry_time=datetime.now() + timedelta(hours=4)
            )
        
        return None
        
    except Exception as e:
        logger.error(f"❌ AI momentum signal generation failed: {e}")
        return None

async def signal_generation_loop(self):
    """Main signal generation loop"""
    while self.is_running:
        try:
            logger.info("🔄 Running signal generation...")
            
            # Get active symbols from data collector
            data_collector_url = os.getenv('DATA_COLLECTOR_URL', 'http://localhost:8004')
            
            symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'BNBUSDT']  # Default symbols
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{data_collector_url}/symbols") as response:
                        if response.status == 200:
                            symbols_data = await response.json()
                            symbols = symbols_data.get('subscribed_symbols', symbols)
            except Exception as e:
                logger.warning(f"Failed to get symbols from data collector: {e}")
            
            # Generate signals for each symbol and strategy
            for symbol in symbols:
                try:
                    # Get current market data
                    market_data = {}
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{data_collector_url}/market-data/{symbol}") as response:
                            if response.status == 200:
                                market_data = await response.json()
                    
                    if not market_data:
                        continue
                    
                    # Generate signals for each enabled strategy
                    for strategy_name, strategy in self.strategies.items():
                        if not strategy.enabled or symbol not in strategy.symbols:
                            continue
                        
                        for timeframe in strategy.timeframes:
                            signal = None
                            
                            if strategy_name == "ma_crossover":
                                signal = await self.generate_ma_crossover_signal(symbol, timeframe, market_data)
                            elif strategy_name == "rsi_reversion":
                                signal = await self.generate_rsi_reversion_signal(symbol, timeframe, market_data)
                            elif strategy_name == "ai_momentum":
                                signal = await self.generate_ai_momentum_signal(symbol, timeframe, market_data)
                            
                            if signal:
                                # Store signal
                                self.active_signals[signal.signal_id] = signal
                                
                                # Cache in Redis
                                if redis_client:
                                    redis_client.setex(
                                        f"signal:{signal.signal_id}",
                                        3600,  # 1 hour TTL
                                        json.dumps(signal.dict(), default=str)
                                    )
                                
                                logger.info(f"✅ Generated signal: {signal.action} {signal.symbol} @ {signal.price} (confidence: {signal.confidence:.2f})")
                
                except Exception as e:
                    logger.error(f"❌ Signal generation failed for {symbol}: {e}")
            
            # Clean up expired signals
            await self.cleanup_expired_signals()
            
            # Sleep before next iteration
            await asyncio.sleep(60)  # Generate signals every minute
            
        except Exception as e:
            logger.error(f"❌ Signal generation loop error: {e}")
            await asyncio.sleep(30)

async def cleanup_expired_signals(self):
    """Clean up expired signals"""
    try:
        current_time = datetime.now()
        expired_signals = []
        
        for signal_id, signal in self.active_signals.items():
            if signal.expiry_time <= current_time:
                expired_signals.append(signal_id)
        
        for signal_id in expired_signals:
            del self.active_signals[signal_id]
            if redis_client:
                redis_client.delete(f"signal:{signal_id}")
        
        if expired_signals:
            logger.info(f"🧹 Cleaned up {len(expired_signals)} expired signals")
            
    except Exception as e:
        logger.error(f"❌ Signal cleanup failed: {e}")

# Patch methods to StrategyEngine
StrategyEngine.generate_ma_crossover_signal = generate_ma_crossover_signal
StrategyEngine.generate_rsi_reversion_signal = generate_rsi_reversion_signal
StrategyEngine.generate_ai_momentum_signal = generate_ai_momentum_signal
StrategyEngine.signal_generation_loop = signal_generation_loop
StrategyEngine.cleanup_expired_signals = cleanup_expired_signals

# API Endpoints
@app.get("/health")
async def health_check():
    """Enhanced health check"""
    data_collector_connected = False
    ai_engine_connected = False
    
    try:
        data_collector_url = os.getenv('DATA_COLLECTOR_URL', 'http://localhost:8004')
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{data_collector_url}/health", timeout=5) as response:
                data_collector_connected = response.status == 200
    except:
        pass
    
    try:
        ai_engine_url = os.getenv('AI_ENGINE_URL', 'http://localhost:8001')
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ai_engine_url}/health", timeout=5) as response:
                ai_engine_connected = response.status == 200
    except:
        pass
    
    return {
        "status": "healthy" if data_collector_connected else "degraded",
        "service": "mirai-strategy-engine",
        "version": "2.0.0",
        "timestamp": datetime.now(),
        "data_collector_connected": data_collector_connected,
        "ai_engine_connected": ai_engine_connected,
        "active_strategies": len([s for s in strategy_engine.strategies.values() if s.enabled]),
        "active_signals": len(strategy_engine.active_signals),
        "is_running": strategy_engine.is_running
    }

@app.get("/signals", response_model=List[TradingSignal])
async def get_active_signals(
    symbol: Optional[str] = None,
    strategy: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500)
):
    """📊 Get active trading signals with filters"""
    try:
        signals = list(strategy_engine.active_signals.values())
        
        # Apply filters
        if symbol:
            signals = [s for s in signals if s.symbol == symbol.upper()]
        if strategy:
            signals = [s for s in signals if s.strategy == strategy]
        if action:
            signals = [s for s in signals if s.action == action.upper()]
        
        # Sort by confidence (highest first) and limit
        signals.sort(key=lambda x: x.confidence, reverse=True)
        signals = signals[:limit]
        
        return signals
        
    except Exception as e:
        logger.error(f"❌ Get signals failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/signals/{signal_id}", response_model=TradingSignal)
async def get_signal(signal_id: str):
    """📋 Get specific signal by ID"""
    try:
        if signal_id in strategy_engine.active_signals:
            return strategy_engine.active_signals[signal_id]
        
        raise HTTPException(status_code=404, detail="Signal not found")
        
    except Exception as e:
        logger.error(f"❌ Get signal failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategies", response_model=List[StrategyConfig])
async def get_strategies():
    """🎯 Get all strategy configurations"""
    try:
        return list(strategy_engine.strategies.values())
        
    except Exception as e:
        logger.error(f"❌ Get strategies failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategies/{strategy_name}/enable")
async def enable_strategy(strategy_name: str):
    """✅ Enable a strategy"""
    try:
        if strategy_name in strategy_engine.strategies:
            strategy_engine.strategies[strategy_name].enabled = True
            strategy_engine.strategies[strategy_name].updated_at = datetime.now()
            return {"message": f"Strategy {strategy_name} enabled"}
        
        raise HTTPException(status_code=404, detail="Strategy not found")
        
    except Exception as e:
        logger.error(f"❌ Enable strategy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategies/{strategy_name}/disable")
async def disable_strategy(strategy_name: str):
    """❌ Disable a strategy"""
    try:
        if strategy_name in strategy_engine.strategies:
            strategy_engine.strategies[strategy_name].enabled = False
            strategy_engine.strategies[strategy_name].updated_at = datetime.now()
            return {"message": f"Strategy {strategy_name} disabled"}
        
        raise HTTPException(status_code=404, detail="Strategy not found")
        
    except Exception as e:
        logger.error(f"❌ Disable strategy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-signals")
async def force_signal_generation(background_tasks: BackgroundTasks):
    """🔄 Force signal generation"""
    try:
        background_tasks.add_task(strategy_engine.signal_generation_loop)
        return {"message": "Signal generation started"}
        
    except Exception as e:
        logger.error(f"❌ Force signal generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start")
async def start_strategy_engine():
    """🚀 Start strategy engine"""
    try:
        if not strategy_engine.is_running:
            strategy_engine.is_running = True
            await strategy_engine.ai_model.initialize_models()
            asyncio.create_task(strategy_engine.signal_generation_loop())
            return {"message": "Strategy engine started"}
        
        return {"message": "Strategy engine already running"}
        
    except Exception as e:
        logger.error(f"❌ Start strategy engine failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop")
async def stop_strategy_engine():
    """🛑 Stop strategy engine"""
    try:
        strategy_engine.is_running = False
        return {"message": "Strategy engine stopped"}
        
    except Exception as e:
        logger.error(f"❌ Stop strategy engine failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_engine_status():
    """📊 Get strategy engine status"""
    try:
        return {
            "is_running": strategy_engine.is_running,
            "total_strategies": len(strategy_engine.strategies),
            "enabled_strategies": len([s for s in strategy_engine.strategies.values() if s.enabled]),
            "active_signals": len(strategy_engine.active_signals),
            "strategies": {name: {"enabled": config.enabled, "priority": config.priority} 
                         for name, config in strategy_engine.strategies.items()},
            "last_update": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"❌ Get status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize strategy engine on startup"""
    logger.info("🚀 Starting Mirai Strategy Engine...")
    
    # Initialize AI models
    await strategy_engine.ai_model.initialize_models()
    
    # Auto-start signal generation
    strategy_engine.is_running = True
    asyncio.create_task(strategy_engine.signal_generation_loop())
    
    logger.info("✅ Strategy Engine startup completed")

# Legacy endpoints for compatibility
@app.get("/trading_signals")
async def get_legacy_trading_signals():
    """📊 Get trading signals (legacy compatibility)"""
    signals = list(strategy_engine.active_signals.values())[:10]
    return {"signals": [s.dict() for s in signals]}

@app.post("/trading_signal")
async def add_legacy_trading_signal(signal: TradingSignal):
    """➕ Add trading signal (legacy compatibility)"""
    strategy_engine.active_signals[signal.signal_id] = signal
    return {"message": "Signal added", "signal_id": signal.signal_id}