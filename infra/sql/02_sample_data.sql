-- Sample data for development and testing
-- This file populates the database with realistic test data

-- Insert sample portfolio balances
INSERT INTO portfolio_balances (asset, free_balance, locked_balance, usd_value) VALUES
('USDT', 10000.00, 0.00, 10000.00),
('BTC', 0.15, 0.05, 6000.00),
('ETH', 2.5, 0.3, 4200.00),
('ADA', 1000.0, 200.0, 500.00),
('SOL', 50.0, 10.0, 3000.00)
ON CONFLICT (asset) DO UPDATE SET
    free_balance = EXCLUDED.free_balance,
    locked_balance = EXCLUDED.locked_balance,
    usd_value = EXCLUDED.usd_value;

-- Insert sample trading signals
INSERT INTO trading_signals (symbol, signal_type, direction, strength, confidence, price, volume, indicators, is_processed) VALUES
('BTCUSDT', 'RSI_OVERSOLD', 'BUY', 75.0, 85.0, 42350.50, 1.5, '{"rsi": 28, "macd": -150, "volume_ratio": 1.2}', false),
('ETHUSDT', 'MOVING_AVERAGE_CROSS', 'BUY', 68.0, 78.0, 2825.75, 3.2, '{"ma_9": 2820, "ma_21": 2815, "volume": 5500000}', false),
('ADAUSDT', 'SUPPORT_LEVEL', 'HOLD', 45.0, 60.0, 0.4150, 15000, '{"support": 0.41, "resistance": 0.45}', true),
('SOLUSDT', 'BREAKOUT', 'SELL', 82.0, 88.0, 125.80, 45.5, '{"breakout_level": 126, "volume_spike": true}', false);

-- Insert sample trading orders
INSERT INTO trading_orders (symbol, side, order_type, quantity, price, status, order_id, client_order_id, filled_quantity, avg_price, commission, commission_asset) VALUES
('BTCUSDT', 'BUY', 'LIMIT', 0.023, 42300.00, 'FILLED', 'BTC001', 'MIRAI_BTC_001', 0.023, 42310.50, 0.000023, 'BTC'),
('ETHUSDT', 'BUY', 'MARKET', 1.5, NULL, 'FILLED', 'ETH001', 'MIRAI_ETH_001', 1.5, 2825.30, 0.0015, 'ETH'),
('ADAUSDT', 'SELL', 'LIMIT', 500.0, 0.4200, 'PARTIALLY_FILLED', 'ADA001', 'MIRAI_ADA_001', 300.0, 0.4195, 0.126, 'USDT'),
('SOLUSDT', 'SELL', 'STOP_LOSS', 20.0, 124.50, 'NEW', 'SOL001', 'MIRAI_SOL_001', 0.0, NULL, NULL, NULL);

-- Insert sample risk events
INSERT INTO risk_events (event_type, severity, symbol, description, data, resolved) VALUES
('POSITION_SIZE_LIMIT', 'MEDIUM', 'BTCUSDT', 'Position size approaching 8% of total portfolio', '{"position_percentage": 7.8, "limit": 10.0}', true),
('DAILY_LOSS_THRESHOLD', 'HIGH', NULL, 'Daily loss reached 3.5% of portfolio value', '{"daily_pnl": -3.5, "threshold": -5.0}', false),
('PRICE_VOLATILITY', 'LOW', 'SOLUSDT', 'Unusual price volatility detected', '{"volatility_spike": 15.2, "normal_range": "5-10"}', true),
('API_CONNECTION', 'CRITICAL', NULL, 'Exchange API connection failed', '{"error": "timeout", "retry_count": 3}', true);

-- Insert sample performance metrics for the last 7 days
INSERT INTO performance_metrics (date, symbol, pnl, volume, trades_count, win_rate, avg_profit, avg_loss, max_drawdown, sharpe_ratio) VALUES
(CURRENT_DATE - INTERVAL '6 days', 'BTCUSDT', 250.75, 15.5, 8, 62.5, 125.30, -98.20, -2.1, 1.85),
(CURRENT_DATE - INTERVAL '6 days', 'ETHUSDT', 180.20, 25.8, 12, 58.3, 89.15, -76.50, -1.8, 1.92),
(CURRENT_DATE - INTERVAL '5 days', 'BTCUSDT', -120.50, 8.2, 5, 40.0, 95.20, -110.30, -3.2, 0.95),
(CURRENT_DATE - INTERVAL '5 days', 'ADAUSDT', 45.30, 8500.0, 6, 66.7, 35.80, -28.90, -1.2, 2.10),
(CURRENT_DATE - INTERVAL '4 days', 'SOLUSDT', 320.80, 85.5, 15, 73.3, 68.90, -45.20, -1.5, 2.45),
(CURRENT_DATE - INTERVAL '3 days', 'ETHUSDT', 95.60, 18.3, 9, 55.6, 78.30, -69.80, -2.0, 1.65),
(CURRENT_DATE - INTERVAL '2 days', 'BTCUSDT', 480.25, 22.1, 14, 71.4, 115.50, -82.10, -1.8, 2.35),
(CURRENT_DATE - INTERVAL '1 day', 'ADAUSDT', -85.40, 12000.0, 11, 36.4, 42.10, -95.50, -4.1, 0.75),
(CURRENT_DATE, 'SOLUSDT', 165.90, 45.2, 7, 85.7, 95.30, -35.20, -0.8, 3.15);

-- Create a view for daily portfolio summary
CREATE OR REPLACE VIEW daily_portfolio_summary AS
SELECT 
    date,
    SUM(pnl) as total_pnl,
    SUM(volume) as total_volume,
    SUM(trades_count) as total_trades,
    AVG(win_rate) as avg_win_rate,
    MIN(max_drawdown) as max_drawdown,
    AVG(sharpe_ratio) as avg_sharpe_ratio
FROM performance_metrics 
GROUP BY date 
ORDER BY date DESC;

-- Create a view for current portfolio value
CREATE OR REPLACE VIEW current_portfolio_value AS
SELECT 
    asset,
    total_balance,
    usd_value,
    CASE 
        WHEN SUM(usd_value) OVER() > 0 
        THEN ROUND((usd_value / SUM(usd_value) OVER()) * 100, 2)
        ELSE 0 
    END as percentage
FROM portfolio_balances 
WHERE total_balance > 0
ORDER BY usd_value DESC;

-- Create a view for active risk events
CREATE OR REPLACE VIEW active_risk_events AS
SELECT 
    id,
    event_type,
    severity,
    symbol,
    description,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at))/3600 as hours_since_created
FROM risk_events 
WHERE resolved = false
ORDER BY 
    CASE severity 
        WHEN 'CRITICAL' THEN 1 
        WHEN 'HIGH' THEN 2 
        WHEN 'MEDIUM' THEN 3 
        WHEN 'LOW' THEN 4 
    END,
    created_at DESC;