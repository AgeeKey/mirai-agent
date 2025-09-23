"""
Advanced Trading Metrics for Prometheus
Enterprise-level monitoring for trading operations
"""

from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest
import time
from typing import Dict, Any
from datetime import datetime
import threading

# Custom registry for trading metrics
trading_registry = CollectorRegistry()

# Trading Performance Metrics
trades_total = Counter(
    'mirai_trades_total',
    'Total number of trades executed',
    ['symbol', 'side', 'status', 'strategy'],
    registry=trading_registry
)

trade_pnl = Histogram(
    'mirai_trade_pnl_usdt',
    'Trade P&L in USDT',
    ['symbol', 'strategy'],
    buckets=[-1000, -500, -100, -50, -10, 0, 10, 50, 100, 500, 1000, float('inf')],
    registry=trading_registry
)

portfolio_value = Gauge(
    'mirai_portfolio_value_usdt',
    'Current portfolio value in USDT',
    registry=trading_registry
)

unrealized_pnl = Gauge(
    'mirai_unrealized_pnl_usdt',
    'Unrealized P&L in USDT',
    registry=trading_registry
)

# Risk Metrics
risk_exposure = Gauge(
    'mirai_risk_exposure_ratio',
    'Current risk exposure as ratio of portfolio',
    ['symbol'],
    registry=trading_registry
)

position_size = Gauge(
    'mirai_position_size_usdt',
    'Position size in USDT',
    ['symbol', 'side'],
    registry=trading_registry
)

max_drawdown = Gauge(
    'mirai_max_drawdown_ratio',
    'Maximum portfolio drawdown ratio',
    registry=trading_registry
)

# AI Decision Metrics
ai_signal_strength = Histogram(
    'mirai_ai_signal_strength',
    'AI signal strength distribution',
    ['symbol', 'signal_type'],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    registry=trading_registry
)

ai_decision_latency = Histogram(
    'mirai_ai_decision_latency_seconds',
    'Time taken for AI decision making',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=trading_registry
)

model_accuracy = Gauge(
    'mirai_model_accuracy_ratio',
    'AI model prediction accuracy',
    ['model_name', 'timeframe'],
    registry=trading_registry
)

# Order Execution Metrics
order_latency = Histogram(
    'mirai_order_latency_seconds',
    'Order execution latency',
    ['exchange', 'order_type'],
    buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=trading_registry
)

order_slippage = Histogram(
    'mirai_order_slippage_bps',
    'Order slippage in basis points',
    ['symbol', 'order_type'],
    buckets=[0, 1, 5, 10, 25, 50, 100, 250, 500],
    registry=trading_registry
)

fill_ratio = Gauge(
    'mirai_order_fill_ratio',
    'Order fill ratio',
    ['symbol', 'order_type'],
    registry=trading_registry
)

# Market Data Metrics
market_data_latency = Histogram(
    'mirai_market_data_latency_seconds',
    'Market data feed latency',
    ['exchange', 'data_type'],
    buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=trading_registry
)

websocket_reconnects = Counter(
    'mirai_websocket_reconnects_total',
    'WebSocket reconnection events',
    ['exchange', 'stream_type'],
    registry=trading_registry
)

# System Health Metrics
api_requests = Counter(
    'mirai_api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status'],
    registry=trading_registry
)

active_positions = Gauge(
    'mirai_active_positions_count',
    'Number of active positions',
    ['symbol'],
    registry=trading_registry
)

daily_trades_count = Gauge(
    'mirai_daily_trades_count',
    'Number of trades executed today',
    registry=trading_registry
)

# Performance Ratios
sharpe_ratio = Gauge(
    'mirai_sharpe_ratio',
    'Sharpe ratio of the portfolio',
    ['timeframe'],
    registry=trading_registry
)

win_rate = Gauge(
    'mirai_win_rate_ratio',
    'Win rate ratio',
    ['strategy', 'timeframe'],
    registry=trading_registry
)

profit_factor = Gauge(
    'mirai_profit_factor',
    'Profit factor (gross profit / gross loss)',
    ['strategy'],
    registry=trading_registry
)


class TradingMetricsCollector:
    """
    Collector for advanced trading metrics
    """
    
    def __init__(self):
        self.lock = threading.Lock()
        self.last_update = time.time()
        
    def record_trade(self, symbol: str, side: str, pnl: float, strategy: str = "default"):
        """Record a completed trade"""
        with self.lock:
            status = "win" if pnl > 0 else "loss" if pnl < 0 else "breakeven"
            trades_total.labels(symbol=symbol, side=side, status=status, strategy=strategy).inc()
            trade_pnl.labels(symbol=symbol, strategy=strategy).observe(pnl)
    
    def update_portfolio_metrics(self, portfolio_val: float, unrealized: float, max_dd: float):
        """Update portfolio-level metrics"""
        with self.lock:
            portfolio_value.set(portfolio_val)
            unrealized_pnl.set(unrealized)
            max_drawdown.set(max_dd)
    
    def record_ai_decision(self, symbol: str, signal_strength: float, latency: float, signal_type: str = "entry"):
        """Record AI decision metrics"""
        with self.lock:
            ai_signal_strength.labels(symbol=symbol, signal_type=signal_type).observe(signal_strength)
            ai_decision_latency.observe(latency)
    
    def record_order_execution(self, symbol: str, latency: float, slippage_bps: float, order_type: str = "market"):
        """Record order execution metrics"""
        with self.lock:
            order_latency.labels(exchange="binance", order_type=order_type).observe(latency)
            order_slippage.labels(symbol=symbol, order_type=order_type).observe(slippage_bps)
    
    def update_position_metrics(self, positions: Dict[str, Dict[str, Any]]):
        """Update position-related metrics"""
        with self.lock:
            # Clear existing position metrics
            active_positions._value.clear()
            position_size._value.clear()
            risk_exposure._value.clear()
            
            total_exposure = 0
            total_value = portfolio_value._value._value if portfolio_value._value._value else 1
            
            for symbol, pos_data in positions.items():
                size = abs(pos_data.get('size', 0))
                side = 'long' if pos_data.get('size', 0) > 0 else 'short'
                value = pos_data.get('notional', 0)
                
                active_positions.labels(symbol=symbol).set(1 if size > 0 else 0)
                position_size.labels(symbol=symbol, side=side).set(value)
                
                exposure_ratio = value / total_value if total_value > 0 else 0
                risk_exposure.labels(symbol=symbol).set(exposure_ratio)
                total_exposure += exposure_ratio
    
    def get_metrics(self) -> str:
        """Get all trading metrics in Prometheus format"""
        return generate_latest(trading_registry)


# Global metrics collector instance
metrics_collector = TradingMetricsCollector()


def get_trading_metrics() -> str:
    """Get trading metrics for Prometheus scraping"""
    return metrics_collector.get_metrics()