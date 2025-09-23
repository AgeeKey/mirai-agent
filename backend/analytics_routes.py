# Analytics Routes
from main import app, get_db, get_current_user, User
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import random
import numpy as np

analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])

@analytics_router.get("/performance")
async def get_performance_metrics(
    period: str = Query("7d", description="Period: 1d, 7d, 30d, 90d, 1y"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Детальные метрики производительности"""
    
    # Определяем количество дней для анализа
    period_days = {
        "1d": 1,
        "7d": 7, 
        "30d": 30,
        "90d": 90,
        "1y": 365
    }.get(period, 7)
    
    # Генерируем исторические данные доходности
    returns = []
    cumulative_return = 0
    
    for i in range(period_days):
        daily_return = random.normalvariate(0.002, 0.02)  # Среднедневная доходность 0.2% ± 2%
        returns.append(daily_return)
        cumulative_return += daily_return
    
    # Вычисляем метрики
    returns_array = np.array(returns)
    
    # Sharpe Ratio (предполагаем безрисковую ставку 2% годовых)
    risk_free_rate = 0.02 / 365  # Дневная безрисковая ставка
    excess_returns = returns_array - risk_free_rate
    sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(365) if np.std(excess_returns) > 0 else 0
    
    # Maximum Drawdown
    cumulative_returns = np.cumsum(returns_array)
    running_max = np.maximum.accumulate(cumulative_returns)
    drawdowns = cumulative_returns - running_max
    max_drawdown = np.min(drawdowns)
    
    # Volatility (годовая)
    volatility = np.std(returns_array) * np.sqrt(365)
    
    # Win Rate
    winning_days = np.sum(returns_array > 0)
    win_rate = winning_days / len(returns_array) * 100
    
    # Calmar Ratio
    annual_return = cumulative_return * (365 / period_days)
    calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
    
    return {
        "period": period,
        "total_return": round(cumulative_return * 100, 2),
        "annualized_return": round(annual_return * 100, 2),
        "volatility": round(volatility * 100, 2),
        "sharpe_ratio": round(sharpe_ratio, 3),
        "max_drawdown": round(max_drawdown * 100, 2),
        "calmar_ratio": round(calmar_ratio, 3),
        "win_rate": round(win_rate, 1),
        "total_trades": random.randint(50, 500),
        "avg_trade_duration": f"{random.randint(2, 48)}h {random.randint(0, 59)}m",
        "profit_factor": round(random.uniform(1.2, 2.5), 2),
        "updated_at": datetime.utcnow().isoformat()
    }

@analytics_router.get("/risk-metrics")
async def get_risk_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Метрики управления рисками"""
    
    # Генерируем данные о рисках
    portfolio_value = 100000.0
    positions_data = [
        {"symbol": "BTC/USDT", "exposure": 0.35, "var_1d": 0.02},
        {"symbol": "ETH/USDT", "exposure": 0.25, "var_1d": 0.025},
        {"symbol": "SOL/USDT", "exposure": 0.15, "var_1d": 0.035},
        {"symbol": "ADA/USDT", "exposure": 0.10, "var_1d": 0.03},
        {"symbol": "Cash", "exposure": 0.15, "var_1d": 0.0}
    ]
    
    # Value at Risk (VaR) расчеты
    portfolio_var_1d = sum(pos["exposure"] * pos["var_1d"] for pos in positions_data)
    portfolio_var_value = portfolio_value * portfolio_var_1d
    
    # Expected Shortfall (Conditional VaR)
    expected_shortfall = portfolio_var_value * 1.3  # Примерно для нормального распределения
    
    # Корреляционная матрица (упрощенная)
    correlation_matrix = {
        "BTC/USDT": {"ETH/USDT": 0.75, "SOL/USDT": 0.65, "ADA/USDT": 0.60},
        "ETH/USDT": {"BTC/USDT": 0.75, "SOL/USDT": 0.70, "ADA/USDT": 0.55},
        "SOL/USDT": {"BTC/USDT": 0.65, "ETH/USDT": 0.70, "ADA/USDT": 0.50},
        "ADA/USDT": {"BTC/USDT": 0.60, "ETH/USDT": 0.55, "SOL/USDT": 0.50}
    }
    
    return {
        "portfolio_value": portfolio_value,
        "var_1d_percent": round(portfolio_var_1d * 100, 2),
        "var_1d_value": round(portfolio_var_value, 2),
        "var_7d_percent": round(portfolio_var_1d * np.sqrt(7) * 100, 2),
        "var_7d_value": round(portfolio_var_value * np.sqrt(7), 2),
        "expected_shortfall": round(expected_shortfall, 2),
        "max_position_size": 0.25,  # 25% максимум на одну позицию
        "current_leverage": round(random.uniform(1.5, 3.0), 1),
        "risk_score": random.randint(65, 85),  # Из 100
        "diversification_ratio": round(random.uniform(0.7, 0.9), 2),
        "positions_breakdown": positions_data,
        "correlation_matrix": correlation_matrix,
        "stress_test_scenarios": {
            "market_crash_2008": {"loss_percent": -15.2, "recovery_days": 45},
            "crypto_winter_2022": {"loss_percent": -22.1, "recovery_days": 120},
            "flash_crash": {"loss_percent": -8.5, "recovery_days": 3}
        },
        "updated_at": datetime.utcnow().isoformat()
    }

@analytics_router.get("/strategy-performance")
async def get_strategy_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Анализ производительности торговых стратегий"""
    
    strategies = [
        {
            "name": "Momentum AI v2.1",
            "status": "active",
            "allocation": 35.0,
            "returns_30d": 4.2,
            "sharpe_ratio": 2.1,
            "max_drawdown": -3.1,
            "win_rate": 68.5,
            "total_trades": 127,
            "avg_holding_time": "4h 23m",
            "best_asset": "BTC/USDT",
            "description": "ML-based momentum strategy with sentiment analysis"
        },
        {
            "name": "Mean Reversion Pro",
            "status": "active", 
            "allocation": 25.0,
            "returns_30d": 2.8,
            "sharpe_ratio": 1.6,
            "max_drawdown": -2.5,
            "win_rate": 72.3,
            "total_trades": 89,
            "avg_holding_time": "12h 15m",
            "best_asset": "ETH/USDT",
            "description": "Statistical arbitrage on price deviations"
        },
        {
            "name": "Breakout Hunter",
            "status": "active",
            "allocation": 20.0,
            "returns_30d": 6.1,
            "sharpe_ratio": 1.8,
            "max_drawdown": -5.2,
            "win_rate": 58.9,
            "total_trades": 45,
            "avg_holding_time": "18h 47m",
            "best_asset": "SOL/USDT",
            "description": "Pattern recognition for breakout trades"
        },
        {
            "name": "Risk Parity",
            "status": "active",
            "allocation": 15.0,
            "returns_30d": 1.5,
            "sharpe_ratio": 1.2,
            "max_drawdown": -1.8,
            "win_rate": 65.0,
            "total_trades": 156,
            "avg_holding_time": "2h 30m",
            "best_asset": "Multiple",
            "description": "Volatility-weighted portfolio balancing"
        },
        {
            "name": "News Sentiment AI",
            "status": "testing",
            "allocation": 5.0,
            "returns_30d": 8.3,
            "sharpe_ratio": 2.8,
            "max_drawdown": -4.1,
            "win_rate": 74.2,
            "total_trades": 32,
            "avg_holding_time": "6h 12m",
            "best_asset": "BTC/USDT",
            "description": "NLP-driven trades based on market sentiment"
        }
    ]
    
    total_return = sum(s["returns_30d"] * s["allocation"] / 100 for s in strategies)
    
    return {
        "strategies": strategies,
        "portfolio_summary": {
            "total_return_30d": round(total_return, 2),
            "best_performer": max(strategies, key=lambda x: x["returns_30d"])["name"],
            "most_stable": min(strategies, key=lambda x: abs(x["max_drawdown"]))["name"],
            "total_trades": sum(s["total_trades"] for s in strategies),
            "avg_win_rate": round(sum(s["win_rate"] * s["allocation"] for s in strategies) / 100, 1)
        },
        "rebalancing_suggestions": [
            {
                "strategy": "News Sentiment AI",
                "action": "increase_allocation",
                "reason": "Strong performance in testing phase",
                "suggested_change": "+5%"
            },
            {
                "strategy": "Risk Parity", 
                "action": "maintain",
                "reason": "Provides good stability",
                "suggested_change": "0%"
            }
        ],
        "updated_at": datetime.utcnow().isoformat()
    }

@analytics_router.get("/market-analysis")
async def get_market_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Анализ рыночных условий и AI insights"""
    
    # Генерируем анализ рынка
    market_sentiment = random.choice(["Bullish", "Neutral", "Bearish"])
    volatility_regime = random.choice(["Low", "Medium", "High"])
    
    # AI-анализ ключевых активов
    assets_analysis = [
        {
            "symbol": "BTC/USDT",
            "trend": "Bullish",
            "strength": 7.8,
            "support_levels": [65000, 63500, 61000],
            "resistance_levels": [70000, 72500, 75000],
            "ai_confidence": 84,
            "prediction_24h": "Upward momentum expected",
            "key_factors": ["Institutional buying", "Technical breakout", "Low supply"]
        },
        {
            "symbol": "ETH/USDT", 
            "trend": "Neutral",
            "strength": 5.2,
            "support_levels": [3200, 3000, 2800],
            "resistance_levels": [3600, 3800, 4000],
            "ai_confidence": 72,
            "prediction_24h": "Consolidation phase",
            "key_factors": ["Staking rewards", "DeFi activity", "Upgrade anticipation"]
        },
        {
            "symbol": "SOL/USDT",
            "trend": "Bullish", 
            "strength": 8.5,
            "support_levels": [180, 175, 165],
            "resistance_levels": [200, 220, 240],
            "ai_confidence": 91,
            "prediction_24h": "Strong upside potential",
            "key_factors": ["Ecosystem growth", "NFT activity", "Developer adoption"]
        }
    ]
    
    # Макроэкономические факторы
    macro_factors = {
        "fed_policy": {"impact": "Neutral", "confidence": 65},
        "inflation": {"impact": "Slightly Negative", "confidence": 78},
        "geopolitical": {"impact": "Low Impact", "confidence": 55},
        "crypto_regulation": {"impact": "Positive", "confidence": 82},
        "institutional_adoption": {"impact": "Very Positive", "confidence": 89}
    }
    
    return {
        "market_overview": {
            "sentiment": market_sentiment,
            "volatility_regime": volatility_regime,
            "trend_strength": random.uniform(6, 9),
            "fear_greed_index": random.randint(25, 75),
            "market_cap_change_24h": round(random.uniform(-3, 5), 2)
        },
        "assets_analysis": assets_analysis,
        "macro_factors": macro_factors,
        "ai_insights": [
            "Cross-asset momentum suggests continued uptrend in major cryptocurrencies",
            "Volume analysis indicates strong institutional participation",
            "Technical patterns show potential for breakout in next 48-72 hours",
            "Risk/reward ratio favors long positions with tight stop-losses"
        ],
        "recommended_actions": [
            {
                "action": "Increase BTC allocation",
                "confidence": 78,
                "timeframe": "Short-term"
            },
            {
                "action": "Reduce altcoin exposure",
                "confidence": 65,
                "timeframe": "Medium-term"
            },
            {
                "action": "Maintain cash reserves",
                "confidence": 72,
                "timeframe": "Ongoing"
            }
        ],
        "next_update": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

@analytics_router.get("/backtesting")
async def get_backtesting_results(
    strategy: str = Query("all", description="Strategy name or 'all'"),
    timeframe: str = Query("1y", description="Backtesting period"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Результаты бэктестирования стратегий"""
    
    # Генерируем результаты бэктестинга
    if strategy == "all":
        strategies = ["Momentum AI v2.1", "Mean Reversion Pro", "Breakout Hunter"]
    else:
        strategies = [strategy]
    
    results = []
    
    for strat_name in strategies:
        # Генерируем исторические данные
        days = 365 if timeframe == "1y" else 90
        equity_curve = [100000]  # Начальный капитал
        
        for i in range(days):
            daily_return = random.normalvariate(0.001, 0.015)  # Средняя доходность с волатильностью
            new_value = equity_curve[-1] * (1 + daily_return)
            equity_curve.append(new_value)
        
        equity_array = np.array(equity_curve)
        returns = np.diff(equity_array) / equity_array[:-1]
        
        # Рассчитываем метрики
        total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
        max_dd = np.min(np.minimum.accumulate(equity_array) - equity_array) / 100000
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(365) if np.std(returns) > 0 else 0
        
        winning_days = np.sum(returns > 0)
        win_rate = winning_days / len(returns) * 100
        
        result = {
            "strategy_name": strat_name,
            "timeframe": timeframe,
            "total_return": round(total_return * 100, 2),
            "annualized_return": round(total_return * (365/days) * 100, 2),
            "max_drawdown": round(max_dd * 100, 2),
            "sharpe_ratio": round(sharpe, 3),
            "win_rate": round(win_rate, 1),
            "total_trades": random.randint(100, 500),
            "avg_trade_return": round(random.uniform(0.1, 0.8), 2),
            "best_trade": round(random.uniform(5, 15), 2),
            "worst_trade": round(random.uniform(-8, -2), 2),
            "profit_factor": round(random.uniform(1.2, 2.1), 2),
            "calmar_ratio": round(total_return / abs(max_dd) if max_dd != 0 else 0, 2),
            "equity_curve": equity_curve[-30:],  # Последние 30 точек для графика
            "monthly_returns": [round(random.uniform(-5, 8), 1) for _ in range(12)]
        }
        results.append(result)
    
    return {
        "backtesting_results": results,
        "comparison": {
            "best_strategy": max(results, key=lambda x: x["sharpe_ratio"])["strategy_name"],
            "most_stable": min(results, key=lambda x: abs(x["max_drawdown"]))["strategy_name"],
            "highest_return": max(results, key=lambda x: x["total_return"])["strategy_name"]
        },
        "disclaimer": "Past performance does not guarantee future results. Backtesting results may not reflect real market conditions.",
        "generated_at": datetime.utcnow().isoformat()
    }

@analytics_router.get("/detailed-report")
async def get_detailed_analytics_report(
    period: str = Query("30d", description="Period: 7d, 30d, 90d, 1y"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить детальный аналитический отчет для страницы аналитики"""
    
    # Получаем все компоненты отчета
    performance = await get_performance_metrics(period, current_user, db)
    risk = await get_risk_metrics(current_user, db)
    strategies = await get_strategy_analysis(current_user, db)
    backtesting = await get_backtesting_analysis("AI Trend Following", "1d", "30d", current_user, db)
    
    # Дополнительные метрики для детального отчета
    period_days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}.get(period, 30)
    
    # Генерируем временной ряд доходности
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
    
    # Детальные стратегии с расширенными метриками
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
            "user_id": current_user.get("id"),
            "report_version": "2.1"
        },
        "performance_summary": {
            "total_return": performance["total_return"],
            "annualized_return": performance["annualized_return"],
            "sharpe_ratio": performance["sharpe_ratio"],
            "max_drawdown": performance["max_drawdown"],
            "win_rate": performance["win_rate"],
            "profit_factor": performance["profit_factor"],
            "calmar_ratio": round(performance["total_return"] / abs(performance["max_drawdown"]), 2),
            "sortino_ratio": round(performance["sharpe_ratio"] * 1.2, 2),  # Приблизительный расчет
            "total_trades": performance["total_trades"],
            "average_trade": performance["avg_trade_return"]
        },
        "risk_metrics": {
            "value_at_risk": risk["var_95"],
            "expected_shortfall": risk["conditional_var"],
            "beta": risk["beta"],
            "alpha": round(random.uniform(0.05, 0.25), 3),
            "volatility": risk["volatility"],
            "correlation_btc": risk["correlation_btc"],
            "correlation_market": round(random.uniform(0.3, 0.7), 2),
            "downside_deviation": round(risk["volatility"] * 0.7, 1),
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
            "overall_rating": "Excellent" if performance["sharpe_ratio"] > 1.5 else "Good" if performance["sharpe_ratio"] > 1.0 else "Average",
            "risk_assessment": "Low" if risk["volatility"] < 15 else "Medium" if risk["volatility"] < 25 else "High",
            "suggested_actions": [
                "Continue current allocation" if performance["total_return"] > 15 else "Consider rebalancing",
                "Monitor risk exposure" if risk["var_95"] < -3 else "Acceptable risk level",
                "Review underperforming strategies" if any(s["performance"] < 0 for s in detailed_strategies) else "All strategies performing well"
            ]
        }
    }

# Включаем роуты в основное приложение
app.include_router(analytics_router)