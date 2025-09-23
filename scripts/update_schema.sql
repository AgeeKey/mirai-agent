-- Создание таблицы trades для 48h анализатора (если не существует)
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    symbol TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL,
    quantity REAL NOT NULL,
    pnl REAL DEFAULT 0.0,
    duration_minutes INTEGER DEFAULT 0,
    market_regime TEXT,
    volatility REAL,
    confidence REAL,
    adaptation_version INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы strategy_adaptations для адаптивных стратегий (если не существует)
CREATE TABLE IF NOT EXISTS strategy_adaptations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    old_params TEXT NOT NULL,
    new_params TEXT NOT NULL,
    market_conditions TEXT NOT NULL,
    performance_before TEXT,
    performance_after TEXT,
    adaptation_reason TEXT NOT NULL,
    confidence REAL NOT NULL
);

-- Создание таблицы economic_events для AI safety (если не существует)
CREATE TABLE IF NOT EXISTS economic_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    scheduled_time TEXT NOT NULL,
    actual_time TEXT,
    description TEXT,
    impact_currencies TEXT,
    volatility_factor REAL DEFAULT 1.0,
    duration_hours INTEGER DEFAULT 4,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы safety_activations (если не существует)
CREATE TABLE IF NOT EXISTS safety_activations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL,
    event_name TEXT NOT NULL,
    action TEXT NOT NULL,
    activated_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    reason TEXT,
    active BOOLEAN DEFAULT 1
);

-- Попытка добавить новые колонки к существующим таблицам (игнорируем ошибки)
ALTER TABLE risk_events ADD COLUMN strategy_name TEXT DEFAULT '';
ALTER TABLE risk_events ADD COLUMN confidence REAL DEFAULT 0.0;
