"""
AI Engine Microservice - Production Version
"""

from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
import redis
import json

app = FastAPI(
    title="AI Engine Service",
    description="Искусственный интеллект и машинное обучение",
    version="1.0.0"
)

# Redis connection
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Models
class Prediction(BaseModel):
    symbol: str
    direction: str  # UP, DOWN, SIDEWAYS
    confidence: float
    target_price: Optional[float] = None
    timeframe: str = "1H"
    model_used: str
    timestamp: datetime

class ModelStatus(BaseModel):
    name: str
    status: str  # TRAINING, READY, ERROR
    accuracy: float
    last_update: datetime

# Cache
predictions: Dict[str, Prediction] = {}
models_status: Dict[str, ModelStatus] = {
    "lstm_price_predictor": ModelStatus(
        name="LSTM Price Predictor",
        status="READY",
        accuracy=0.72,
        last_update=datetime.now()
    ),
    "sentiment_analyzer": ModelStatus(
        name="Market Sentiment Analyzer",
        status="READY",
        accuracy=0.68,
        last_update=datetime.now()
    )
}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-engine",
        "timestamp": datetime.now(),
        "models_ready": len([m for m in models_status.values() if m.status == "READY"])
    }

@app.get("/models", response_model=List[ModelStatus])
async def get_models():
    return list(models_status.values())

@app.get("/predictions", response_model=List[Prediction])
async def get_predictions():
    return list(predictions.values())

@app.post("/predict")
async def make_prediction(symbol: str, timeframe: str = "1H"):
    """Создание AI прогноза для символа"""
    import random
    
    # Simulate AI prediction
    directions = ["UP", "DOWN", "SIDEWAYS"]
    direction = random.choice(directions)
    confidence = random.uniform(0.6, 0.95)
    
    # Generate target price based on direction
    base_price = random.uniform(1000, 50000)  # Demo base price
    if direction == "UP":
        target_price = base_price * random.uniform(1.02, 1.10)
    elif direction == "DOWN":
        target_price = base_price * random.uniform(0.90, 0.98)
    else:
        target_price = base_price * random.uniform(0.99, 1.01)
    
    prediction = Prediction(
        symbol=symbol,
        direction=direction,
        confidence=confidence,
        target_price=target_price,
        timeframe=timeframe,
        model_used="lstm_price_predictor",
        timestamp=datetime.now()
    )
    
    predictions[symbol] = prediction
    
    # Store in Redis
    try:
        redis_client.setex(f"ai_prediction:{symbol}", 3600, json.dumps(prediction.dict(), default=str))
    except:
        pass
    
    return prediction

@app.post("/analyze_sentiment")
async def analyze_market_sentiment():
    """Анализ настроений рынка"""
    import random
    
    sentiment_scores = {
        "overall": random.uniform(-1.0, 1.0),
        "news": random.uniform(-1.0, 1.0),
        "social": random.uniform(-1.0, 1.0),
        "technical": random.uniform(-1.0, 1.0)
    }
    
    # Interpret sentiment
    overall_sentiment = sentiment_scores["overall"]
    if overall_sentiment > 0.3:
        sentiment_label = "BULLISH"
    elif overall_sentiment < -0.3:
        sentiment_label = "BEARISH"
    else:
        sentiment_label = "NEUTRAL"
    
    return {
        "sentiment": sentiment_label,
        "scores": sentiment_scores,
        "confidence": abs(overall_sentiment),
        "timestamp": datetime.now()
    }

@app.post("/train_model")
async def train_model(model_name: str):
    """Тренировка AI модели"""
    if model_name not in models_status:
        return {"error": "Model not found"}
    
    # Simulate training
    models_status[model_name].status = "TRAINING"
    
    # Simulate training completion (in real app this would be async)
    await asyncio.sleep(1)
    
    models_status[model_name].status = "READY"
    models_status[model_name].accuracy = random.uniform(0.65, 0.85)
    models_status[model_name].last_update = datetime.now()
    
    return {
        "message": f"Model {model_name} training completed",
        "status": models_status[model_name]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
