-- Services Platform Database Schema
-- Tables for aimirai.info online services

\c mirai_services_db;

-- Service Users (public access)
CREATE TABLE service_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) UNIQUE,
    username VARCHAR(50),
    api_key VARCHAR(255) UNIQUE,
    subscription_tier VARCHAR(20) DEFAULT 'free', -- free, basic, premium
    rate_limit_per_hour INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Usage Tracking
CREATE TABLE api_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES service_users(id),
    api_key VARCHAR(255),
    endpoint VARCHAR(100) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Service Requests
CREATE TABLE ai_service_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES service_users(id),
    service_type VARCHAR(50) NOT NULL, -- market_analysis, price_prediction, sentiment
    input_data JSONB NOT NULL,
    output_data JSONB,
    processing_time_ms INTEGER,
    cost_credits DECIMAL(10,4) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'processing', -- processing, completed, failed
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Market Data Cache for Services
CREATE TABLE market_data_cache (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    data_type VARCHAR(50) NOT NULL, -- price, volume, indicators
    timeframe VARCHAR(10) NOT NULL, -- 1m, 5m, 1h, 1d
    data JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, data_type, timeframe)
);

-- Analytics Reports
CREATE TABLE analytics_reports (
    id SERIAL PRIMARY KEY,
    report_type VARCHAR(50) NOT NULL, -- daily_summary, market_overview, performance
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    symbols TEXT[], -- array of symbols covered
    report_data JSONB NOT NULL,
    is_public BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Portfolio Tracking (for services)
CREATE TABLE portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES service_users(id),
    portfolio_name VARCHAR(100) DEFAULT 'default',
    holdings JSONB NOT NULL, -- {"BTC": {"quantity": 1.5, "value": 45000}, ...}
    total_value DECIMAL(15,8) NOT NULL,
    daily_change DECIMAL(15,8),
    daily_change_percent DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Service Alerts
CREATE TABLE service_alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES service_users(id),
    alert_type VARCHAR(50) NOT NULL, -- price_alert, portfolio_alert, news_alert
    condition_data JSONB NOT NULL, -- {"symbol": "BTC", "price": 50000, "direction": "above"}
    is_active BOOLEAN DEFAULT true,
    is_triggered BOOLEAN DEFAULT false,
    triggered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- News and Market Sentiment
CREATE TABLE market_news (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    source VARCHAR(100),
    symbols TEXT[], -- related symbols
    sentiment_score DECIMAL(3,2), -- -1.00 to 1.00
    importance_score DECIMAL(3,2), -- 0.00 to 1.00
    published_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Service Subscriptions and Billing
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES service_users(id),
    plan_type VARCHAR(20) NOT NULL, -- free, basic, premium
    billing_cycle VARCHAR(20), -- monthly, yearly
    price_per_cycle DECIMAL(10,2),
    credits_per_cycle INTEGER,
    credits_used INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active', -- active, suspended, cancelled
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- WebSocket Connections
CREATE TABLE websocket_connections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES service_users(id),
    connection_id VARCHAR(255) UNIQUE NOT NULL,
    subscribed_channels TEXT[], -- ["BTC-price", "market-overview"]
    ip_address INET,
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Service Health Monitoring
CREATE TABLE service_health (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL, -- healthy, degraded, down
    response_time_ms INTEGER,
    error_rate DECIMAL(5,2), -- percentage
    cpu_usage DECIMAL(5,2),
    memory_usage DECIMAL(5,2),
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_api_usage_user_timestamp ON api_usage(user_id, created_at DESC);
CREATE INDEX idx_ai_requests_user_status ON ai_service_requests(user_id, status);
CREATE INDEX idx_market_cache_symbol_type ON market_data_cache(symbol, data_type, timeframe);
CREATE INDEX idx_portfolio_user_timestamp ON portfolio_snapshots(user_id, created_at DESC);
CREATE INDEX idx_alerts_user_active ON service_alerts(user_id, is_active);
CREATE INDEX idx_news_published ON market_news(published_at DESC);
CREATE INDEX idx_subscriptions_user_status ON subscriptions(user_id, status);
CREATE INDEX idx_websocket_user_active ON websocket_connections(user_id, is_active);
CREATE INDEX idx_service_health_timestamp ON service_health(service_name, checked_at DESC);

-- Create triggers for updated_at timestamps
CREATE TRIGGER update_service_users_updated_at BEFORE UPDATE ON service_users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_service_alerts_updated_at BEFORE UPDATE ON service_alerts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default subscription plans
INSERT INTO subscriptions (user_id, plan_type, credits_per_cycle, current_period_start, current_period_end) 
VALUES 
  (1, 'free', 1000, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '1 month'),
  (1, 'basic', 10000, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '1 month'),
  (1, 'premium', 100000, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '1 month');