-- Trading Platform Database Schema
-- Tables for aimirai.online trading functionality

\c mirai_trading_db;

-- Users and Authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'trader',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trading Accounts
CREATE TABLE trading_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    account_type VARCHAR(20) DEFAULT 'demo', -- demo, live
    balance DECIMAL(15,8) DEFAULT 0,
    equity DECIMAL(15,8) DEFAULT 0,
    margin_used DECIMAL(15,8) DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trading Positions
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES trading_accounts(id),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL, -- long, short
    size DECIMAL(15,8) NOT NULL,
    entry_price DECIMAL(15,8) NOT NULL,
    current_price DECIMAL(15,8),
    unrealized_pnl DECIMAL(15,8) DEFAULT 0,
    stop_loss DECIMAL(15,8),
    take_profit DECIMAL(15,8),
    status VARCHAR(20) DEFAULT 'open', -- open, closed, partial
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trading Orders
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES trading_accounts(id),
    position_id INTEGER REFERENCES positions(id),
    symbol VARCHAR(20) NOT NULL,
    order_type VARCHAR(20) NOT NULL, -- market, limit, stop_loss, take_profit
    side VARCHAR(10) NOT NULL, -- buy, sell
    quantity DECIMAL(15,8) NOT NULL,
    price DECIMAL(15,8),
    stop_price DECIMAL(15,8),
    status VARCHAR(20) DEFAULT 'pending', -- pending, filled, cancelled, rejected
    exchange_order_id VARCHAR(100),
    filled_quantity DECIMAL(15,8) DEFAULT 0,
    average_fill_price DECIMAL(15,8),
    commission DECIMAL(15,8) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    filled_at TIMESTAMP
);

-- Market Data
CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(15,8) NOT NULL,
    volume_24h DECIMAL(15,8),
    change_24h DECIMAL(5,2),
    bid DECIMAL(15,8),
    ask DECIMAL(15,8),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp)
);

-- AI Analysis Results
CREATE TABLE ai_analysis (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    sentiment VARCHAR(20), -- bullish, bearish, neutral
    confidence DECIMAL(3,2), -- 0.00 to 1.00
    recommendation VARCHAR(20), -- BUY, SELL, HOLD
    price_target DECIMAL(15,8),
    stop_loss_level DECIMAL(15,8),
    timeframe VARCHAR(10), -- 1h, 4h, 1d, etc.
    analysis_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Risk Management
CREATE TABLE risk_events (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES trading_accounts(id),
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL, -- low, medium, high, critical
    description TEXT,
    action_taken VARCHAR(100),
    resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Trading Sessions
CREATE TABLE trading_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE,
    ip_address INET,
    user_agent TEXT,
    login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Audit Trail
CREATE TABLE audit_trail (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50), -- order, position, account
    entity_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_positions_account_symbol ON positions(account_id, symbol);
CREATE INDEX idx_orders_account_status ON orders(account_id, status);
CREATE INDEX idx_market_data_symbol_timestamp ON market_data(symbol, timestamp DESC);
CREATE INDEX idx_ai_analysis_symbol_timestamp ON ai_analysis(symbol, created_at DESC);
CREATE INDEX idx_risk_events_account_severity ON risk_events(account_id, severity);
CREATE INDEX idx_audit_trail_user_timestamp ON audit_trail(user_id, created_at DESC);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_trading_accounts_updated_at BEFORE UPDATE ON trading_accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON positions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();