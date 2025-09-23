# Individual API endpoints
@app.post("/api/v1/predict-price", response_model=Dict[str, Any])
async def predict_price(symbol: str, historical_data: List[float]):
    """Predict future price using LSTM model"""
    if not ai_models.is_initialized:
        raise HTTPException(status_code=503, detail="AI models not initialized")
    
    result = await ai_models.price_predictor.predict_price(symbol, historical_data)
    
    # Update model performance
    if symbol in model_performance_cache:
        model_performance_cache["lstm_price_predictor"].predictions_count += 1
    
    return result

@app.post("/api/v1/detect-patterns", response_model=PatternAnalysis)
async def detect_patterns(symbol: str, ohlcv_data: List[Dict]):
    """Detect chart patterns"""
    if not ai_models.is_initialized:
        raise HTTPException(status_code=503, detail="AI models not initialized")
    
    result = await ai_models.pattern_detector.detect_patterns(symbol, ohlcv_data)
    model_performance_cache["pattern_detector"].predictions_count += 1
    
    return result

@app.post("/api/v1/analyze-sentiment", response_model=SentimentAnalysis)
async def analyze_sentiment(symbol: str, news_texts: List[str]):
    """Analyze market sentiment"""
    result = await sentiment_analyzer.analyze_sentiment(symbol, news_texts)
    model_performance_cache["sentiment_analyzer"].predictions_count += 1
    
    return result

@app.post("/api/v1/assess-risk", response_model=RiskAssessment)
async def assess_risk(symbol: str, portfolio_data: Dict, market_data: List[Dict]):
    """Assess trading risk"""
    if not ai_models.is_initialized:
        raise HTTPException(status_code=503, detail="AI models not initialized")
    
    result = await ai_models.risk_analyzer.analyze_risk(symbol, portfolio_data, market_data)
    model_performance_cache["risk_analyzer"].predictions_count += 1
    
    return result

@app.post("/api/v1/llm-analysis", response_model=LLMAnalysis)
async def llm_analysis(symbol: str, market_data: Dict, news_data: List[str] = None):
    """Generate LLM-powered market analysis"""
    result = await llm_service.analyze_market(symbol, market_data, news_data)
    return result

@app.get("/api/v1/models/performance", response_model=Dict[str, ModelPerformance])
async def get_model_performance():
    """Get performance metrics for all models"""
    return model_performance_cache

@app.post("/api/v1/models/{model_name}/retrain")
async def retrain_model(model_name: str, background_tasks: BackgroundTasks):
    """Trigger model retraining"""
    if model_name not in model_performance_cache:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Update status to training
    model_performance_cache[model_name].status = "TRAINING"
    model_performance_cache[model_name].last_updated = datetime.now()
    
    # Add background task for retraining
    background_tasks.add_task(retrain_model_task, model_name)
    
    return {"message": f"Model {model_name} retraining initiated"}

async def retrain_model_task(model_name: str):
    """Background task for model retraining"""
    try:
        logger.info(f"🔄 Starting retraining for {model_name}")
        
        # Simulate training time
        await asyncio.sleep(10)
        
        # Update performance metrics (simulated improvement)
        if model_name in model_performance_cache:
            current_accuracy = model_performance_cache[model_name].accuracy
            new_accuracy = min(0.95, current_accuracy + np.random.uniform(0.01, 0.05))
            
            model_performance_cache[model_name].accuracy = new_accuracy
            model_performance_cache[model_name].precision = new_accuracy - 0.02
            model_performance_cache[model_name].recall = new_accuracy + 0.01
            model_performance_cache[model_name].f1_score = new_accuracy - 0.01
            model_performance_cache[model_name].status = "READY"
            model_performance_cache[model_name].last_updated = datetime.now()
        
        logger.info(f"✅ Model {model_name} retraining completed")
        
    except Exception as e:
        logger.error(f"❌ Model retraining failed: {e}")
        if model_name in model_performance_cache:
            model_performance_cache[model_name].status = "ERROR"

# Batch processing endpoints
@app.post("/api/v1/batch/analyze")
async def batch_analysis(symbols: List[str], market_data: Dict[str, Dict]):
    """Batch analysis for multiple symbols"""
    results = {}
    
    for symbol in symbols:
        if symbol in market_data:
            try:
                result = await comprehensive_analysis(
                    symbol=symbol,
                    market_data=market_data[symbol],
                    historical_data=None,
                    news_data=None,
                    portfolio_data=None
                )
                results[symbol] = result
            except Exception as e:
                results[symbol] = {"error": str(e)}
        else:
            results[symbol] = {"error": "No market data provided"}
    
    return results

@app.get("/api/v1/signals/active")
async def get_active_signals():
    """Get all active trading signals"""
    if not redis_client:
        return {"error": "Redis not available"}
    
    try:
        # Get all cached analysis results
        keys = redis_client.keys("analysis:*")
        active_signals = []
        
        for key in keys[-10:]:  # Get last 10 signals
            data = redis_client.get(key)
            if data:
                analysis = json.loads(data)
                if "overall_signal" in analysis:
                    active_signals.append(analysis["overall_signal"])
        
        return {"signals": active_signals, "count": len(active_signals)}
        
    except Exception as e:
        logger.error(f"Error getting active signals: {e}")
        return {"error": str(e)}

# WebSocket for real-time updates
@app.websocket("/ws/analysis")
async def websocket_analysis(websocket):
    """WebSocket endpoint for real-time analysis updates"""
    await websocket.accept()
    
    try:
        while True:
            # Wait for client message
            data = await websocket.receive_json()
            symbol = data.get("symbol")
            
            if symbol:
                # Generate quick analysis
                quick_analysis = {
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat(),
                    "signal": "HOLD",
                    "confidence": 0.65,
                    "risk": "MEDIUM"
                }
                
                await websocket.send_json(quick_analysis)
            
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Admin endpoints
@app.get("/api/v1/admin/stats")
async def get_system_stats():
    """Get system statistics"""
    stats = {
        "models_status": {name: perf.status for name, perf in model_performance_cache.items()},
        "total_predictions": sum(perf.predictions_count for perf in model_performance_cache.values()),
        "average_accuracy": np.mean([perf.accuracy for perf in model_performance_cache.values()]),
        "cache_keys": len(redis_client.keys("*")) if redis_client else 0,
        "uptime": datetime.now(),
        "version": "2.0.0"
    }
    
    return stats

@app.post("/api/v1/admin/clear-cache")
async def clear_cache():
    """Clear all cached data"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        redis_client.flushall()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "ai_engine:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )