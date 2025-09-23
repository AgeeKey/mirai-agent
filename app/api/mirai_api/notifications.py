"""
Push Notifications API endpoints for Mirai trading platform
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import httpx
import asyncio
from datetime import datetime
import logging

from .auth import get_current_user

# Настройка логирования
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Pydantic модели для push уведомлений
class PushTokenRequest(BaseModel):
    token: str
    device_id: str
    platform: str = "mobile"

class TradingSignalNotification(BaseModel):
    symbol: str
    type: str  # 'BUY' | 'SELL'
    confidence: int
    price: float
    strategy: str

class PortfolioNotification(BaseModel):
    total_value: float
    daily_pnl: float
    change_percent: float

class SystemNotification(BaseModel):
    title: str
    message: str
    priority: str = "normal"  # 'low' | 'normal' | 'high'
    category: str = "system"

# In-memory хранилище токенов (в продакшене использовать Redis/Database)
user_push_tokens: Dict[int, List[Dict]] = {}

@router.post("/register-token")
async def register_push_token(
    token_data: PushTokenRequest,
    current_user = Depends(get_current_user)
):
    """Регистрация push токена для пользователя"""
    try:
        user_id = current_user.id
        
        if user_id not in user_push_tokens:
            user_push_tokens[user_id] = []
        
        # Проверяем, есть ли уже этот токен
        existing_token = next(
            (t for t in user_push_tokens[user_id] if t['token'] == token_data.token),
            None
        )
        
        if not existing_token:
            user_push_tokens[user_id].append({
                'token': token_data.token,
                'device_id': token_data.device_id,
                'platform': token_data.platform,
                'registered_at': datetime.now().isoformat()
            })
            
        logger.info(f"Registered push token for user {user_id}")
        return {"status": "success", "message": "Push token registered"}
        
    except Exception as e:
        logger.error(f"Error registering push token: {e}")
        raise HTTPException(status_code=500, detail="Failed to register push token")

@router.delete("/unregister-token")
async def unregister_push_token(
    device_id: str,
    current_user = Depends(get_current_user)
):
    """Удаление push токена пользователя"""
    try:
        user_id = current_user.id
        
        if user_id in user_push_tokens:
            user_push_tokens[user_id] = [
                t for t in user_push_tokens[user_id] 
                if t['device_id'] != device_id
            ]
            
        return {"status": "success", "message": "Push token unregistered"}
        
    except Exception as e:
        logger.error(f"Error unregistering push token: {e}")
        raise HTTPException(status_code=500, detail="Failed to unregister push token")

@router.get("/tokens")
async def get_user_tokens(current_user = Depends(get_current_user)):
    """Получение списка зарегистрированных токенов пользователя"""
    user_id = current_user.id
    tokens = user_push_tokens.get(user_id, [])
    
    return {
        "user_id": user_id,
        "tokens": tokens,
        "count": len(tokens)
    }

async def send_expo_notification(expo_token: str, notification_data: Dict[str, Any]):
    """Отправка уведомления через Expo Push API"""
    try:
        url = "https://exp.host/--/api/v2/push/send"
        
        payload = {
            "to": expo_token,
            "title": notification_data.get("title", "Mirai Trading"),
            "body": notification_data.get("body", ""),
            "data": notification_data.get("data", {}),
            "sound": notification_data.get("sound", "default"),
            "badge": notification_data.get("badge", 1),
            "priority": notification_data.get("priority", "default"),
            "channelId": notification_data.get("channelId", "default")
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                logger.info(f"Push notification sent successfully to {expo_token[:10]}...")
                return response.json()
            else:
                logger.error(f"Failed to send push notification: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")
        return None

@router.post("/send/trading-signal")
async def send_trading_signal_notification(
    signal: TradingSignalNotification,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Отправка уведомления о торговом сигнале"""
    try:
        user_id = current_user.id
        tokens = user_push_tokens.get(user_id, [])
        
        if not tokens:
            return {"status": "no_tokens", "message": "No push tokens registered"}
        
        notification_data = {
            "title": f"🚨 {signal.type} Signal",
            "body": f"{signal.symbol} at ${signal.price:.2f} ({signal.confidence}% confidence)",
            "data": {
                "type": "trading_signal",
                "symbol": signal.symbol,
                "signal_type": signal.type,
                "price": signal.price,
                "confidence": signal.confidence,
                "strategy": signal.strategy,
                "timestamp": datetime.now().isoformat()
            },
            "channelId": "trading_signals",
            "priority": "high",
            "badge": 1
        }
        
        # Отправляем уведомления всем зарегистрированным устройствам
        for token_info in tokens:
            background_tasks.add_task(
                send_expo_notification,
                token_info['token'],
                notification_data
            )
        
        return {
            "status": "success", 
            "message": f"Trading signal notification sent to {len(tokens)} devices"
        }
        
    except Exception as e:
        logger.error(f"Error sending trading signal notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")

@router.post("/send/portfolio-update")
async def send_portfolio_notification(
    portfolio: PortfolioNotification,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Отправка уведомления об обновлении портфолио"""
    try:
        user_id = current_user.id
        tokens = user_push_tokens.get(user_id, [])
        
        if not tokens:
            return {"status": "no_tokens", "message": "No push tokens registered"}
        
        # Определяем эмодзи и цвет на основе PnL
        emoji = "📈" if portfolio.daily_pnl >= 0 else "📉"
        sign = "+" if portfolio.daily_pnl >= 0 else ""
        
        notification_data = {
            "title": f"{emoji} Portfolio Update",
            "body": f"${portfolio.total_value:,.2f} ({sign}{portfolio.change_percent:.1f}%)",
            "data": {
                "type": "portfolio_update",
                "total_value": portfolio.total_value,
                "daily_pnl": portfolio.daily_pnl,
                "change_percent": portfolio.change_percent,
                "timestamp": datetime.now().isoformat()
            },
            "channelId": "portfolio_updates",
            "priority": "normal",
            "badge": 1
        }
        
        # Отправляем уведомления всем зарегистрированным устройствам
        for token_info in tokens:
            background_tasks.add_task(
                send_expo_notification,
                token_info['token'],
                notification_data
            )
        
        return {
            "status": "success", 
            "message": f"Portfolio notification sent to {len(tokens)} devices"
        }
        
    except Exception as e:
        logger.error(f"Error sending portfolio notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")

@router.post("/send/system")
async def send_system_notification(
    system_notif: SystemNotification,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Отправка системного уведомления"""
    try:
        user_id = current_user.id
        tokens = user_push_tokens.get(user_id, [])
        
        if not tokens:
            return {"status": "no_tokens", "message": "No push tokens registered"}
        
        # Определяем приоритет и эмодзи
        priority_emoji = {
            "low": "ℹ️",
            "normal": "🔔",
            "high": "⚠️"
        }
        
        notification_data = {
            "title": f"{priority_emoji.get(system_notif.priority, '🔔')} {system_notif.title}",
            "body": system_notif.message,
            "data": {
                "type": "system",
                "category": system_notif.category,
                "priority": system_notif.priority,
                "timestamp": datetime.now().isoformat()
            },
            "channelId": "system_alerts",
            "priority": "default" if system_notif.priority == "normal" else system_notif.priority,
            "badge": 1
        }
        
        # Отправляем уведомления всем зарегистрированным устройствам
        for token_info in tokens:
            background_tasks.add_task(
                send_expo_notification,
                token_info['token'],
                notification_data
            )
        
        return {
            "status": "success", 
            "message": f"System notification sent to {len(tokens)} devices"
        }
        
    except Exception as e:
        logger.error(f"Error sending system notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")

@router.post("/broadcast/all-users")
async def broadcast_notification(
    notification: SystemNotification,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Широковещательная отправка уведомления всем пользователям (только для админов)"""
    try:
        # Проверка прав администратора (в реальном приложении)
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        total_devices = 0
        
        # Отправляем всем зарегистрированным пользователям
        for user_id, tokens in user_push_tokens.items():
            total_devices += len(tokens)
            
            notification_data = {
                "title": f"📢 {notification.title}",
                "body": notification.message,
                "data": {
                    "type": "broadcast",
                    "category": notification.category,
                    "priority": notification.priority,
                    "timestamp": datetime.now().isoformat()
                },
                "channelId": "broadcasts",
                "priority": "high",
                "badge": 1
            }
            
            for token_info in tokens:
                background_tasks.add_task(
                    send_expo_notification,
                    token_info['token'],
                    notification_data
                )
        
        return {
            "status": "success", 
            "message": f"Broadcast notification sent to {total_devices} devices across {len(user_push_tokens)} users"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error broadcasting notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast notification")

@router.get("/stats")
async def get_notification_stats():
    """Получение статистики по уведомлениям"""
    try:
        total_users = len(user_push_tokens)
        total_devices = sum(len(tokens) for tokens in user_push_tokens.values())
        
        platform_stats = {}
        for tokens in user_push_tokens.values():
            for token_info in tokens:
                platform = token_info.get('platform', 'unknown')
                platform_stats[platform] = platform_stats.get(platform, 0) + 1
        
        return {
            "total_users": total_users,
            "total_devices": total_devices,
            "platform_distribution": platform_stats,
            "users_with_tokens": list(user_push_tokens.keys())
        }
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")