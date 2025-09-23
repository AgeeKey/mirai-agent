-- Mirai Agent Database Schema
-- Initialize database tables for trading system

-- Trading orders table
CREATE TABLE IF NOT EXISTS trading_orders (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    order_type VARCHAR(20) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8),
    status VARCHAR(20) NOT NULL DEFAULT 'NEW',
    order_id VARCHAR(100) UNIQUE,
    client_order_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    executed_at TIMESTAMP WITH TIME ZONE,
    filled_quantity DECIMAL(20, 8) DEFAULT 0,
    avg_price DECIMAL(20, 8),
    commission DECIMAL(20, 8),
    commission_asset VARCHAR(10)
);

-- Trading signals table
CREATE TABLE IF NOT EXISTS trading_signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('BUY', 'SELL', 'HOLD')),
    strength DECIMAL(5, 2) NOT NULL CHECK (strength >= 0 AND strength <= 100),
    confidence DECIMAL(5, 2) NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
    price DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(20, 8),
    indicators JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    is_processed BOOLEAN DEFAULT FALSE
);

-- Portfolio balances table
CREATE TABLE IF NOT EXISTS portfolio_balances (
    id SERIAL PRIMARY KEY,
    asset VARCHAR(20) NOT NULL,
    free_balance DECIMAL(20, 8) NOT NULL DEFAULT 0,
    locked_balance DECIMAL(20, 8) NOT NULL DEFAULT 0,
    total_balance DECIMAL(20, 8) GENERATED ALWAYS AS (free_balance + locked_balance) STORED,
    usd_value DECIMAL(20, 2),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(asset)
);

-- Risk management events table
CREATE TABLE IF NOT EXISTS risk_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    symbol VARCHAR(20),
    description TEXT NOT NULL,
    data JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Trading performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    symbol VARCHAR(20),
    pnl DECIMAL(20, 2) NOT NULL DEFAULT 0,
    volume DECIMAL(20, 8) NOT NULL DEFAULT 0,
    trades_count INTEGER NOT NULL DEFAULT 0,
    win_rate DECIMAL(5, 2),
    avg_profit DECIMAL(20, 2),
    avg_loss DECIMAL(20, 2),
    max_drawdown DECIMAL(20, 2),
    sharpe_ratio DECIMAL(10, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(date, symbol)
);

-- System configuration table
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_trading_orders_symbol_status ON trading_orders(symbol, status);
CREATE INDEX IF NOT EXISTS idx_trading_orders_created_at ON trading_orders(created_at);
CREATE INDEX IF NOT EXISTS idx_trading_signals_symbol_processed ON trading_signals(symbol, is_processed);
CREATE INDEX IF NOT EXISTS idx_trading_signals_created_at ON trading_signals(created_at);
CREATE INDEX IF NOT EXISTS idx_risk_events_severity ON risk_events(severity, resolved);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_date ON performance_metrics(date);

-- Insert default system configuration
INSERT INTO system_config (config_key, config_value, description) VALUES
('risk_management', '{"max_position_size": 0.1, "max_daily_loss": 0.05, "max_drawdown": 0.15}', 'Risk management parameters'),
('trading_pairs', '["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"]', 'Active trading pairs'),
('strategy_config', '{"rsi_period": 14, "ma_fast": 9, "ma_slow": 21, "signal_threshold": 0.7}', 'Trading strategy configuration')
ON CONFLICT (config_key) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_trading_orders_updated_at BEFORE UPDATE ON trading_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_portfolio_balances_updated_at BEFORE UPDATE ON portfolio_balances
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();