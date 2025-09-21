"""
Notifications Microservice - Production Version
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
    title="Notifications Service",
    description="Система уведомлений и алертов",
    version="1.0.0"
)

# Redis connection  
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Models
class Notification(BaseModel):
    id: str
    type: str  # INFO, WARNING, ERROR, TRADE
    title: str
    message: str
    timestamp: datetime
    read: bool = False
    channel: str = "web"  # web, telegram, email

class AlertConfig(BaseModel):
    telegram_enabled: bool = True
    email_enabled: bool = False
    web_enabled: bool = True
    price_alerts: bool = True
    trade_alerts: bool = True

# Cache
notifications: List[Notification] = []
alert_config = AlertConfig()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "notifications",
        "timestamp": datetime.now()
    }

@app.get("/notifications", response_model=List[Notification])
async def get_notifications(limit: int = 50):
    return notifications[-limit:] if notifications else []

@app.post("/notify")
async def send_notification(
    type: str,
    title: str,
    message: str,
    channel: str = "web"
):
    notification = Notification(
        id=f"notif_{datetime.now().timestamp()}",
        type=type,
        title=title,
        message=message,
        timestamp=datetime.now(),
        channel=channel
    )
    
    notifications.append(notification)
    if len(notifications) > 1000:
        notifications.pop(0)
    
    # Store in Redis
    try:
        redis_client.lpush("notifications", json.dumps(notification.dict(), default=str))
        redis_client.ltrim("notifications", 0, 999)  # Keep last 1000
    except:
        pass
    
    return {"message": "Notification sent", "notification": notification}

@app.post("/notify/trade")
async def notify_trade(
    symbol: str,
    action: str,
    quantity: float,
    price: float,
    status: str = "EXECUTED"
):
    title = f"Trade {status}: {action} {symbol}"
    message = f"{action} {quantity} {symbol} at {price}"
    
    return await send_notification("TRADE", title, message)

@app.post("/notify/alert")
async def notify_alert(
    symbol: str,
    alert_type: str,
    message: str
):
    title = f"{alert_type} Alert: {symbol}"
    
    return await send_notification("WARNING", title, message)

@app.get("/config", response_model=AlertConfig)
async def get_alert_config():
    return alert_config

@app.post("/config")
async def update_alert_config(config: AlertConfig):
    global alert_config
    alert_config = config
    return {"message": "Alert configuration updated"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
