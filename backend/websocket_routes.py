# WebSocket Routes
from main import app, manager, get_current_user, User
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from main import SECRET_KEY, ALGORITHM
import json
import asyncio
from datetime import datetime
import random

security = HTTPBearer()

async def get_user_from_token(token: str):
    """Получить пользователя из WebSocket токена"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        return username
    except JWTError:
        return None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """WebSocket endpoint для real-time обновлений"""
    
    await manager.connect(websocket)
    
    try:
        # Отправляем приветственное сообщение
        await manager.send_personal_message(
            json.dumps({
                "type": "connection_established",
                "message": "Connected to Mirai Trading API",
                "timestamp": datetime.utcnow().isoformat()
            }),
            websocket
        )
        
        # Запускаем фоновую задачу отправки обновлений
        asyncio.create_task(send_periodic_updates(websocket))
        
        while True:
            # Ожидаем сообщения от клиента
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Обрабатываем различные типы сообщений
            if message.get("type") == "subscribe":
                await handle_subscription(websocket, message)
            elif message.get("type") == "unsubscribe":
                await handle_unsubscription(websocket, message)
            elif message.get("type") == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}),
                    websocket
                )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

async def handle_subscription(websocket: WebSocket, message: dict):
    """Обработка подписки на обновления"""
    subscription_type = message.get("subscription_type")
    
    response = {
        "type": "subscription_confirmed",
        "subscription_type": subscription_type,
        "message": f"Subscribed to {subscription_type} updates",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.send_personal_message(json.dumps(response), websocket)

async def handle_unsubscription(websocket: WebSocket, message: dict):
    """Обработка отписки от обновлений"""
    subscription_type = message.get("subscription_type")
    
    response = {
        "type": "unsubscription_confirmed", 
        "subscription_type": subscription_type,
        "message": f"Unsubscribed from {subscription_type} updates",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.send_personal_message(json.dumps(response), websocket)

async def send_periodic_updates(websocket: WebSocket):
    """Отправка периодических обновлений"""
    try:
        while True:
            await asyncio.sleep(5)  # Обновления каждые 5 секунд
            
            # Отправляем обновления цен
            price_update = {
                "type": "price_update",
                "data": {
                    "BTC/USDT": round(68000 + random.uniform(-500, 500), 2),
                    "ETH/USDT": round(3400 + random.uniform(-100, 100), 2),
                    "SOL/USDT": round(188 + random.uniform(-10, 10), 2),
                    "ADA/USDT": round(0.48 + random.uniform(-0.02, 0.02), 4)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await manager.send_personal_message(json.dumps(price_update), websocket)
            
            # Иногда отправляем новые сигналы
            if random.random() < 0.3:  # 30% вероятность
                signal_update = {
                    "type": "new_signal",
                    "data": {
                        "symbol": random.choice(["BTC/USDT", "ETH/USDT", "SOL/USDT"]),
                        "signal_type": random.choice(["BUY", "SELL"]),
                        "confidence": round(random.uniform(75, 95), 1),
                        "reasoning": "AI analysis detected favorable conditions"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await manager.send_personal_message(json.dumps(signal_update), websocket)
            
            # Обновления портфеля
            if random.random() < 0.2:  # 20% вероятность  
                portfolio_update = {
                    "type": "portfolio_update",
                    "data": {
                        "total_balance": round(100000 + random.uniform(-1000, 3000), 2),
                        "daily_pnl": round(random.uniform(-500, 1500), 2),
                        "active_positions": random.randint(5, 12)
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await manager.send_personal_message(json.dumps(portfolio_update), websocket)
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Error in periodic updates: {e}")

@app.websocket("/ws/trading/{user_id}")
async def trading_websocket(websocket: WebSocket, user_id: int):
    """Персональный WebSocket для торговых уведомлений"""
    
    await manager.connect(websocket)
    
    try:
        await manager.send_personal_message(
            json.dumps({
                "type": "trading_connection",
                "user_id": user_id,
                "message": f"Trading WebSocket connected for user {user_id}",
                "timestamp": datetime.utcnow().isoformat()
            }),
            websocket
        )
        
        # Запускаем персональные обновления
        asyncio.create_task(send_trading_updates(websocket, user_id))
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Обработка торговых команд
            if message.get("type") == "place_order":
                await handle_place_order(websocket, user_id, message)
            elif message.get("type") == "cancel_order":
                await handle_cancel_order(websocket, user_id, message)
            elif message.get("type") == "get_positions":
                await handle_get_positions(websocket, user_id)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Trading WebSocket error: {e}")
        manager.disconnect(websocket)

async def send_trading_updates(websocket: WebSocket, user_id: int):
    """Отправка торговых обновлений для конкретного пользователя"""
    try:
        while True:
            await asyncio.sleep(10)  # Обновления каждые 10 секунд
            
            # Обновления по позициям
            positions_update = {
                "type": "positions_update",
                "user_id": user_id,
                "data": [
                    {
                        "symbol": "BTC/USDT",
                        "pnl": round(random.uniform(-100, 300), 2),
                        "pnl_percentage": round(random.uniform(-2, 5), 2)
                    },
                    {
                        "symbol": "ETH/USDT", 
                        "pnl": round(random.uniform(-50, 200), 2),
                        "pnl_percentage": round(random.uniform(-1, 3), 2)
                    }
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await manager.send_personal_message(json.dumps(positions_update), websocket)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Error in trading updates: {e}")

async def handle_place_order(websocket: WebSocket, user_id: int, message: dict):
    """Обработка размещения ордера"""
    order_data = message.get("data", {})
    
    # Симуляция размещения ордера
    response = {
        "type": "order_placed",
        "user_id": user_id,
        "order_id": f"order_{random.randint(10000, 99999)}",
        "symbol": order_data.get("symbol"),
        "side": order_data.get("side"),
        "quantity": order_data.get("quantity"),
        "price": order_data.get("price"),
        "status": "filled",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.send_personal_message(json.dumps(response), websocket)

async def handle_cancel_order(websocket: WebSocket, user_id: int, message: dict):
    """Обработка отмены ордера"""
    order_id = message.get("order_id")
    
    response = {
        "type": "order_cancelled",
        "user_id": user_id,
        "order_id": order_id,
        "status": "cancelled",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.send_personal_message(json.dumps(response), websocket)

async def handle_get_positions(websocket: WebSocket, user_id: int):
    """Получение текущих позиций"""
    positions = [
        {
            "symbol": "BTC/USDT",
            "side": "LONG",
            "size": 0.25,
            "entry_price": 67250.0,
            "current_price": 68100.0,
            "pnl": 212.50
        },
        {
            "symbol": "ETH/USDT",
            "side": "SHORT", 
            "size": 5.0,
            "entry_price": 3420.0,
            "current_price": 3385.0,
            "pnl": 175.0
        }
    ]
    
    response = {
        "type": "positions_response",
        "user_id": user_id,
        "data": positions,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.send_personal_message(json.dumps(response), websocket)