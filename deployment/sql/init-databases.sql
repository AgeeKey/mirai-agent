-- Initialize separate databases for trading and services platforms
-- This script runs during PostgreSQL container startup

-- Create databases
CREATE DATABASE mirai_trading_db;
CREATE DATABASE mirai_services_db;

-- Create users for each platform
CREATE USER mirai_trading WITH PASSWORD 'TRADING_PASSWORD_PLACEHOLDER';
CREATE USER mirai_services WITH PASSWORD 'SERVICES_PASSWORD_PLACEHOLDER';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE mirai_trading_db TO mirai_trading;
GRANT ALL PRIVILEGES ON DATABASE mirai_services_db TO mirai_services;

-- Grant connection privileges
GRANT CONNECT ON DATABASE mirai_trading_db TO mirai_trading;
GRANT CONNECT ON DATABASE mirai_services_db TO mirai_services;

-- Additional security settings
ALTER DATABASE mirai_trading_db OWNER TO mirai_trading;
ALTER DATABASE mirai_services_db OWNER TO mirai_services;