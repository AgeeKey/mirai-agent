"""
Упрощенная версия FastAPI бэкенда без email валидации
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import random
import datetime
from datetime import datetime, timedelta
import uuid

app = FastAPI(title="Mirai Agent API", version="1.0.0")

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Модели данных
class UserCreate(BaseModel):
    username: str
    email: str  # Обычная строка вместо EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: int
    username: str
    email: str

# Временная база данных
fake_users_db = {
    "testuser": {
        "id": 1,
        "username": "testuser", 
        "email": "test@example.com",
        "password": "testpass"
    }
}

fake_tokens = {}

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Проверка токена"""
    token = credentials.credentials
    if token in fake_tokens:
        return fake_tokens[token]
    raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/")
async def root():
    return {"message": "Mirai Agent API", "version": "1.0.0", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Аутентификация
@app.post("/auth/register")
async def register(user: UserCreate):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    fake_users_db[user.username] = {
        "id": len(fake_users_db) + 1,
        "username": user.username,
        "email": user.email,
        "password": user.password
    }
    
    return {"message": "User created successfully"}

@app.post("/auth/login")
async def login(user: UserLogin):
    if user.username not in fake_users_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    stored_user = fake_users_db[user.username]
    if stored_user["password"] != user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = str(uuid.uuid4())
    fake_tokens[token] = stored_user
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": stored_user["id"],
            "username": stored_user["username"],
            "email": stored_user["email"]
        }
    }

@app.get("/auth/me")
async def get_current_user(user = Depends(verify_token)):
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"]
    }

# Trading API
@app.get("/trading/portfolio")
async def get_portfolio(user = Depends(verify_token)):
    return {
        "total_value": 125000 + random.uniform(-5000, 10000),
        "available_balance": 25000 + random.uniform(-2000, 5000),
        "positions": [
            {"symbol": "BTC/USDT", "size": 0.5, "value": 30000},
            {"symbol": "ETH/USDT", "size": 10.0, "value": 25000},
            {"symbol": "SOL/USDT", "size": 100.0, "value": 15000}
        ],
        "daily_pnl": random.uniform(-1000, 2000),
        "total_pnl": random.uniform(5000, 25000)
    }

@app.get("/trading/signals")
async def get_signals(user = Depends(verify_token)):
    signals = []
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT", "DOT/USDT"]
    
    for i in range(5):
        signal_type = random.choice(["BUY", "SELL"])
        confidence = random.uniform(0.6, 0.95)
        
        signals.append({
            "id": i + 1,
            "symbol": symbols[i],
            "type": signal_type,
            "confidence": round(confidence, 2),
            "price": random.uniform(100, 50000),
            "target": random.uniform(105, 52000),
            "stop_loss": random.uniform(95, 48000),
            "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat(),
            "strategy": random.choice(["AI Trend", "Mean Reversion", "Momentum"])
        })
    
    return {"signals": signals}

# Analytics API
@app.get("/analytics/performance")
async def get_performance_metrics(
    period: str = Query("30d", description="Period: 7d, 30d, 90d, 1y"),
    user = Depends(verify_token)
):
    base_return = 15.5 + random.uniform(-5, 10)
    
    return {
        "total_return": round(base_return, 2),
        "annualized_return": round(base_return * 12, 2),
        "sharpe_ratio": round(1.2 + random.uniform(-0.3, 0.8), 2),
        "max_drawdown": round(-8.5 + random.uniform(-5, 3), 2),
        "win_rate": round(65 + random.uniform(-10, 15), 2),
        "profit_factor": round(1.8 + random.uniform(-0.5, 1.0), 2),
        "total_trades": random.randint(80, 200),
        "avg_trade_return": round(0.85 + random.uniform(-0.5, 1.0), 2),
        "volatility": round(18 + random.uniform(-5, 10), 2)
    }

@app.get("/analytics/risk")
async def get_risk_metrics(user = Depends(verify_token)):
    return {
        "var_95": round(-2.5 + random.uniform(-1.5, 1.0), 2),
        "conditional_var": round(-3.8 + random.uniform(-2.0, 1.0), 2),
        "beta": round(0.85 + random.uniform(-0.3, 0.6), 2),
        "volatility": round(18 + random.uniform(-5, 10), 2),
        "correlation_btc": round(0.6 + random.uniform(-0.3, 0.3), 2),
        "downside_deviation": round(12 + random.uniform(-3, 6), 2),
        "maximum_drawdown_duration": random.randint(5, 25)
    }

@app.get("/analytics/strategies")
async def get_strategy_analysis(user = Depends(verify_token)):
    strategies = [
        {"name": "AI Trend Following", "base_performance": 28.4},
        {"name": "Mean Reversion", "base_performance": 15.2},
        {"name": "Momentum Scalping", "base_performance": -2.1},
        {"name": "Arbitrage Scanner", "base_performance": 8.7}
    ]
    
    return {
        "strategies": [
            {
                "name": s["name"],
                "performance": round(s["base_performance"] + random.uniform(-3, 3), 1),
                "trades": random.randint(50, 200),
                "win_rate": round(60 + random.uniform(-10, 25), 1),
                "avg_duration": f"{random.uniform(1, 5):.1f} дня",
                "status": random.choice(["active", "paused", "stopped"]),
                "allocation": round(random.uniform(10, 40), 1)
            }
            for s in strategies
        ]
    }

@app.get("/analytics/backtesting")
async def get_backtesting_analysis(
    strategy: str = Query("AI Trend Following"),
    timeframe: str = Query("1d"),
    period: str = Query("30d"),
    user = Depends(verify_token)
):
    initial_capital = 100000
    return_pct = 15.5 + random.uniform(-10, 20)
    final_capital = initial_capital * (1 + return_pct / 100)
    
    return {
        "strategy": strategy,
        "timeframe": timeframe,
        "period": period,
        "initial_capital": initial_capital,
        "final_capital": round(final_capital),
        "total_return": round(return_pct, 2),
        "sharpe_ratio": round(1.2 + random.uniform(-0.5, 1.0), 2),
        "max_drawdown": round(-8 + random.uniform(-5, 5), 2),
        "volatility": round(18 + random.uniform(-8, 12), 2),
        "total_trades": random.randint(50, 300),
        "win_rate": round(65 + random.uniform(-15, 20), 2),
        "best_trade": round(random.uniform(5, 25), 2),
        "worst_trade": round(random.uniform(-15, -3), 2),
        "avg_trade": round(random.uniform(0.5, 3), 2)
    }

@app.get("/analytics/detailed-report")
async def get_detailed_analytics_report(
    period: str = Query("30d", description="Period: 7d, 30d, 90d, 1y"),
    user = Depends(verify_token)
):
    """Получить детальный аналитический отчет для страницы аналитики"""
    
    # Базовые метрики
    base_return = 15.5 + random.uniform(-5, 10)
    sharpe = 1.2 + random.uniform(-0.3, 0.8)
    max_dd = -8.5 + random.uniform(-5, 3)
    volatility = 18 + random.uniform(-5, 10)
    
    # Генерируем временной ряд
    period_days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}.get(period, 30)
    timeline_data = []
    base_value = 100000
    current_value = base_value
    
    for i in range(period_days):
        daily_return = random.normalvariate(0.0012, 0.018)
        current_value *= (1 + daily_return)
        
        timeline_data.append({
            "date": (datetime.now() - timedelta(days=period_days - i)).strftime("%Y-%m-%d"),
            "portfolio_value": round(current_value, 2),
            "daily_return": round(daily_return * 100, 3),
            "cumulative_return": round((current_value - base_value) / base_value * 100, 2)
        })
    
    # Детальные стратегии
    detailed_strategies = [
        {
            "name": "AI Trend Following",
            "performance": 28.4 + random.uniform(-3, 3),
            "trades": random.randint(140, 170),
            "win_rate": 72.1 + random.uniform(-3, 3),
            "avg_duration": "2.3 дня",
            "status": "active",
            "allocation": 45.0,
            "sharpe_ratio": 1.85 + random.uniform(-0.2, 0.3),
            "max_drawdown": -5.2 + random.uniform(-1, 1),
            "profit_factor": 2.34 + random.uniform(-0.3, 0.3),
            "calmar_ratio": 3.2 + random.uniform(-0.5, 0.5)
        },
        {
            "name": "Mean Reversion",
            "performance": 15.2 + random.uniform(-2, 2),
            "trades": random.randint(80, 100),
            "win_rate": 61.5 + random.uniform(-3, 3),
            "avg_duration": "1.8 дня",
            "status": "active",
            "allocation": 30.0,
            "sharpe_ratio": 1.45 + random.uniform(-0.2, 0.2),
            "max_drawdown": -7.1 + random.uniform(-1, 1),
            "profit_factor": 1.89 + random.uniform(-0.2, 0.2),
            "calmar_ratio": 2.1 + random.uniform(-0.3, 0.3)
        },
        {
            "name": "Momentum Scalping",
            "performance": -2.1 + random.uniform(-1, 3),
            "trades": random.randint(180, 220),
            "win_rate": 58.1 + random.uniform(-3, 3),
            "avg_duration": "4.2 часа",
            "status": "paused",
            "allocation": 15.0,
            "sharpe_ratio": 0.85 + random.uniform(-0.2, 0.2),
            "max_drawdown": -12.3 + random.uniform(-2, 1),
            "profit_factor": 1.23 + random.uniform(-0.2, 0.2),
            "calmar_ratio": -0.17 + random.uniform(-0.1, 0.3)
        },
        {
            "name": "Arbitrage Scanner",
            "performance": 8.7 + random.uniform(-1, 2),
            "trades": random.randint(50, 80),
            "win_rate": 85.2 + random.uniform(-2, 2),
            "avg_duration": "1.2 часа",
            "status": "active",
            "allocation": 10.0,
            "sharpe_ratio": 2.1 + random.uniform(-0.2, 0.3),
            "max_drawdown": -3.1 + random.uniform(-0.5, 0.5),
            "profit_factor": 3.45 + random.uniform(-0.3, 0.3),
            "calmar_ratio": 2.8 + random.uniform(-0.3, 0.3)
        }
    ]
    
    # Результаты бэктестирования
    backtest_periods = [
        {"period": "2024 Q1", "base_return": 28.4},
        {"period": "2023 Q4", "base_return": 15.2},
        {"period": "2023 Q3", "base_return": 9.8},
        {"period": "2023 Q2", "base_return": 18.5},
        {"period": "2023 Q1", "base_return": 12.3}
    ]
    
    backtest_results = []
    for bt in backtest_periods:
        initial = 100000
        return_val = bt["base_return"] + random.uniform(-2, 2)
        final = initial * (1 + return_val / 100)
        
        backtest_results.append({
            "period": bt["period"],
            "initial_capital": initial,
            "final_capital": round(final),
            "return": round(return_val, 1),
            "sharpe": round(1.2 + random.uniform(-0.3, 0.6), 2),
            "max_drawdown": round(-8 + random.uniform(-3, 3), 1),
            "volatility": round(15 + random.uniform(-3, 8), 1),
            "trades_count": random.randint(80, 150),
            "win_rate": round(65 + random.uniform(-5, 10), 1)
        })
    
    return {
        "report_metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "period": period,
            "period_days": period_days,
            "user_id": user.get("id"),
            "report_version": "2.1"
        },
        "performance_summary": {
            "total_return": round(base_return, 2),
            "annualized_return": round(base_return * 12, 2),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown": round(max_dd, 2),
            "win_rate": round(65 + random.uniform(-10, 15), 2),
            "profit_factor": round(1.8 + random.uniform(-0.5, 1.0), 2),
            "calmar_ratio": round(base_return / abs(max_dd), 2),
            "sortino_ratio": round(sharpe * 1.2, 2),
            "total_trades": random.randint(80, 200),
            "average_trade": round(0.85 + random.uniform(-0.5, 1.0), 2)
        },
        "risk_metrics": {
            "value_at_risk": round(-2.5 + random.uniform(-1.5, 1.0), 2),
            "expected_shortfall": round(-3.8 + random.uniform(-2.0, 1.0), 2),
            "beta": round(0.85 + random.uniform(-0.3, 0.6), 2),
            "alpha": round(random.uniform(0.05, 0.25), 3),
            "volatility": round(volatility, 1),
            "correlation_btc": round(0.6 + random.uniform(-0.3, 0.3), 2),
            "correlation_market": round(random.uniform(0.3, 0.7), 2),
            "downside_deviation": round(volatility * 0.7, 1),
            "tracking_error": round(random.uniform(2, 8), 1)
        },
        "portfolio_timeline": timeline_data,
        "strategy_performance": [
            {
                "name": s["name"],
                "performance": round(s["performance"], 1),
                "trades": s["trades"],
                "win_rate": round(s["win_rate"], 1),
                "avg_duration": s["avg_duration"],
                "status": s["status"],
                "allocation": s["allocation"],
                "sharpe_ratio": round(s["sharpe_ratio"], 2),
                "max_drawdown": round(s["max_drawdown"], 1),
                "profit_factor": round(s["profit_factor"], 2),
                "calmar_ratio": round(s["calmar_ratio"], 2)
            }
            for s in detailed_strategies
        ],
        "backtesting_results": backtest_results,
        "market_conditions": {
            "current_trend": "Bullish" if random.random() > 0.5 else "Bearish",
            "volatility_regime": random.choice(["Low", "Medium", "High"]),
            "market_sentiment": round(random.uniform(3, 8), 1),
            "fear_greed_index": random.randint(20, 80),
            "macro_environment": random.choice(["Favorable", "Neutral", "Challenging"])
        },
        "recommendations": {
            "overall_rating": "Excellent" if sharpe > 1.5 else "Good" if sharpe > 1.0 else "Average",
            "risk_assessment": "Low" if volatility < 15 else "Medium" if volatility < 25 else "High",
            "suggested_actions": [
                "Continue current allocation" if base_return > 15 else "Consider rebalancing",
                "Monitor risk exposure" if abs(max_dd) > 10 else "Acceptable risk level",
                "Review underperforming strategies" if any(s["performance"] < 0 for s in detailed_strategies) else "All strategies performing well"
            ]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)