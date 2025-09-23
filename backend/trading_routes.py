# Trading Routes
from main import app, get_db, get_current_user, User, Position, TradingSignal, TradingStats
from main import PositionResponse, TradingSignalResponse, TradingStatsResponse
from main import generate_mock_positions, generate_mock_signals, manager
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
import random
import json

trading_router = APIRouter(prefix="/trading", tags=["Trading"])

@trading_router.get("/portfolio", response_model=TradingStatsResponse)
async def get_portfolio_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить статистику портфеля пользователя"""
    
    # Ищем существующую статистику или создаем новую
    stats = db.query(TradingStats).filter(TradingStats.user_id == current_user.id).first()
    
    if not stats:
        # Создаем начальную статистику для нового пользователя
        stats = TradingStats(
            user_id=current_user.id,
            total_balance=100000.0,
            daily_pnl=random.uniform(-1000, 3000),
            total_trades=random.randint(50, 200),
            winning_trades=random.randint(30, 150),
            losing_trades=random.randint(10, 50),
        )
        # Вычисляем производные метрики
        stats.win_rate = (stats.winning_trades / stats.total_trades * 100) if stats.total_trades > 0 else 0
        stats.max_drawdown = random.uniform(5, 15)
        stats.sharpe_ratio = random.uniform(1.2, 2.8)
        
        db.add(stats)
        db.commit()
        db.refresh(stats)
    
    return stats

@trading_router.get("/positions", response_model=List[PositionResponse])
async def get_active_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить активные позиции пользователя"""
    
    # Для демонстрации генерируем мок-данные
    # В реальном приложении здесь будет запрос к базе данных
    mock_positions = generate_mock_positions(current_user.id)
    
    # Создаем объекты PositionResponse
    positions = []
    for pos_data in mock_positions:
        position = PositionResponse(
            id=random.randint(1, 1000),
            symbol=pos_data["symbol"],
            side=pos_data["side"],
            size=pos_data["size"],
            entry_price=pos_data["entry_price"],
            current_price=pos_data["current_price"],
            pnl=pos_data["pnl"],
            pnl_percentage=pos_data["pnl_percentage"],
            status="OPEN",
            created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        )
        positions.append(position)
    
    return positions

@trading_router.get("/signals", response_model=List[TradingSignalResponse])
async def get_trading_signals(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить последние торговые сигналы AI"""
    
    # Для демонстрации генерируем мок-данные
    mock_signals = generate_mock_signals()
    
    signals = []
    for signal_data in mock_signals:
        signal = TradingSignalResponse(
            id=random.randint(1, 1000),
            symbol=signal_data["symbol"],
            signal_type=signal_data["signal_type"],
            confidence=signal_data["confidence"],
            price=signal_data["price"],
            reasoning=signal_data["reasoning"],
            timestamp=signal_data["timestamp"],
            is_executed=random.choice([True, False])
        )
        signals.append(signal)
    
    return signals[:limit]

@trading_router.post("/signals/{signal_id}/execute")
async def execute_signal(
    signal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Исполнить торговый сигнал"""
    
    # В реальном приложении здесь будет логика исполнения через биржу
    # Для демонстрации возвращаем успешный результат
    
    await manager.broadcast(json.dumps({
        "type": "trade_executed",
        "user_id": current_user.id,
        "signal_id": signal_id,
        "timestamp": datetime.utcnow().isoformat(),
        "message": f"Signal {signal_id} executed successfully"
    }))
    
    return {
        "status": "executed",
        "signal_id": signal_id,
        "message": "Trade executed successfully",
        "timestamp": datetime.utcnow().isoformat()
    }

@trading_router.get("/history")
async def get_trading_history(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить историю торгов"""
    
    # Генерируем мок-данные истории торгов
    history = []
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=i)
        daily_trades = random.randint(0, 15)
        daily_pnl = random.uniform(-500, 1500)
        
        history.append({
            "date": date.date().isoformat(),
            "trades_count": daily_trades,
            "pnl": round(daily_pnl, 2),
            "win_rate": round(random.uniform(60, 95), 1),
            "volume": round(random.uniform(10000, 50000), 2)
        })
    
    return {
        "history": history,
        "total_days": days,
        "total_trades": sum(h["trades_count"] for h in history),
        "total_pnl": round(sum(h["pnl"] for h in history), 2)
    }

@trading_router.get("/market-data/{symbol}")
async def get_market_data(symbol: str):
    """Получить рыночные данные для символа"""
    
    # Мок-данные рыночной информации
    base_prices = {
        "BTC/USDT": 68000,
        "ETH/USDT": 3400,
        "SOL/USDT": 188,
        "ADA/USDT": 0.48,
        "DOT/USDT": 7.2
    }
    
    base_price = base_prices.get(symbol, 100)
    current_price = base_price * random.uniform(0.98, 1.02)
    change_24h = random.uniform(-5, 8)
    volume_24h = random.uniform(100000000, 2000000000)
    
    return {
        "symbol": symbol,
        "current_price": round(current_price, 2),
        "change_24h": round(change_24h, 2),
        "change_24h_percent": round(change_24h / base_price * 100, 2),
        "volume_24h": round(volume_24h, 2),
        "high_24h": round(current_price * 1.05, 2),
        "low_24h": round(current_price * 0.95, 2),
        "timestamp": datetime.utcnow().isoformat()
    }

@trading_router.post("/start-trading")
async def start_trading(
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Запустить автономную торговлю"""
    
    # Запускаем фоновую задачу генерации сигналов
    background_tasks.add_task(generate_signals_background, current_user.id)
    
    await manager.broadcast(json.dumps({
        "type": "trading_started",
        "user_id": current_user.id,
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Autonomous trading started"
    }))
    
    return {
        "status": "started",
        "message": "Autonomous trading activated",
        "timestamp": datetime.utcnow().isoformat()
    }

@trading_router.post("/stop-trading")
async def stop_trading(current_user: User = Depends(get_current_user)):
    """Остановить автономную торговлю"""
    
    await manager.broadcast(json.dumps({
        "type": "trading_stopped",
        "user_id": current_user.id,
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Autonomous trading stopped"
    }))
    
    return {
        "status": "stopped", 
        "message": "Autonomous trading deactivated",
        "timestamp": datetime.utcnow().isoformat()
    }

async def generate_signals_background(user_id: int):
    """Фоновая задача генерации торговых сигналов"""
    for _ in range(5):  # Генерируем 5 сигналов
        await asyncio.sleep(random.uniform(10, 30))  # Случайная задержка
        
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT", "DOT/USDT"]
        symbol = random.choice(symbols)
        signal_type = random.choice(["BUY", "SELL"])
        confidence = random.uniform(75, 98)
        
        signal_message = {
            "type": "new_signal",
            "user_id": user_id,
            "symbol": symbol,
            "signal_type": signal_type,
            "confidence": round(confidence, 1),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await manager.broadcast(json.dumps(signal_message))

# Включаем роуты в основное приложение
app.include_router(trading_router)