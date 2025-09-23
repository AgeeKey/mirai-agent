#!/bin/bash

# Environment Setup Script for Production Deployment
# Creates .env.production file with secure defaults

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Logging functions
log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[WARNING] $1${NC}"; }
error() { echo -e "${RED}[ERROR] $1${NC}" >&2; }

# Generate secure random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Generate JWT secret
generate_jwt_secret() {
    openssl rand -hex 32
}

# Main setup function
setup_production_env() {
    log "Setting up production environment configuration..."
    
    # Get script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    ENV_FILE="$PROJECT_ROOT/.env.production"
    
    # Check if .env.production already exists
    if [[ -f "$ENV_FILE" ]]; then
        warn "Production environment file already exists"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Keeping existing configuration"
            exit 0
        fi
    fi
    
    log "Generating secure passwords and secrets..."
    
    # Generate passwords
    POSTGRES_ADMIN_PASSWORD=$(generate_password)
    POSTGRES_TRADING_PASSWORD=$(generate_password)
    POSTGRES_SERVICES_PASSWORD=$(generate_password)
    JWT_SECRET=$(generate_jwt_secret)
    GRAFANA_ADMIN_PASSWORD=$(generate_password)
    
    # Prompt for optional configurations
    echo
    log "Optional configuration (press Enter to skip):"
    
    read -p "Binance API Key (for live trading): " BINANCE_API_KEY
    read -p "Binance API Secret (for live trading): " BINANCE_API_SECRET
    read -p "Telegram Bot Token (for notifications): " TELEGRAM_BOT_TOKEN
    read -p "Telegram Chat ID (for notifications): " TELEGRAM_CHAT_ID
    
    # Ask about testnet
    read -p "Use Binance Testnet? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        BINANCE_TESTNET="false"
        warn "⚠️  LIVE TRADING MODE ENABLED - USE WITH CAUTION!"
    else
        BINANCE_TESTNET="true"
        log "Using Binance Testnet (safe mode)"
    fi
    
    # Create production environment file
    log "Creating production environment file..."
    
    cat > "$ENV_FILE" << EOF
# Mirai Agent Production Environment Configuration
# Generated on $(date)

# ============ DATABASE CONFIGURATION ============
POSTGRES_ADMIN_PASSWORD=$POSTGRES_ADMIN_PASSWORD
POSTGRES_TRADING_PASSWORD=$POSTGRES_TRADING_PASSWORD
POSTGRES_SERVICES_PASSWORD=$POSTGRES_SERVICES_PASSWORD

# ============ SECURITY CONFIGURATION ============
JWT_SECRET=$JWT_SECRET

# ============ TRADING CONFIGURATION ============
BINANCE_API_KEY=${BINANCE_API_KEY:-}
BINANCE_API_SECRET=${BINANCE_API_SECRET:-}
BINANCE_TESTNET=$BINANCE_TESTNET

# ============ MONITORING CONFIGURATION ============
GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD

# ============ NOTIFICATION CONFIGURATION ============
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN:-}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID:-}

# ============ DOMAIN CONFIGURATION ============
DOMAIN_TRADING=aimirai.online
DOMAIN_SERVICES=aimirai.info

# ============ SSL CONFIGURATION ============
SSL_EMAIL=admin@aimirai.info

# ============ LOGGING CONFIGURATION ============
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30

# ============ PERFORMANCE CONFIGURATION ============
WORKER_PROCESSES=auto
MAX_CONNECTIONS=1024
CLIENT_MAX_BODY_SIZE=50m

# ============ REDIS CONFIGURATION ============
REDIS_MAX_MEMORY=1gb
REDIS_MAX_MEMORY_POLICY=allkeys-lru

# ============ BACKUP CONFIGURATION ============
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE=daily

# ============ DEVELOPMENT FLAGS ============
DEBUG=false
DEVELOPMENT_MODE=false
EOF
    
    # Set secure permissions
    chmod 600 "$ENV_FILE"
    
    log "✅ Production environment configured successfully!"
    log ""
    log "📁 Configuration saved to: $ENV_FILE"
    log "🔒 File permissions set to 600 (owner read/write only)"
    log ""
    log "🔑 Generated passwords:"
    log "  - PostgreSQL Admin: $POSTGRES_ADMIN_PASSWORD"
    log "  - Grafana Admin: $GRAFANA_ADMIN_PASSWORD"
    log ""
    
    if [[ "$BINANCE_TESTNET" == "false" ]]; then
        warn "⚠️  IMPORTANT: Live trading is enabled!"
        warn "⚠️  Make sure your Binance API keys are correctly configured"
        warn "⚠️  Test thoroughly before deploying to production"
    fi
    
    log "Next steps:"
    log "  1. Review the configuration in $ENV_FILE"
    log "  2. Update any additional settings as needed"
    log "  3. Run './deployment/deploy-production.sh' to deploy"
}

# Create deployment structure
create_deployment_structure() {
    log "Creating deployment directory structure..."
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Create directories
    mkdir -p "$SCRIPT_DIR/data"
    mkdir -p "$SCRIPT_DIR/logs"
    mkdir -p "$SCRIPT_DIR/monitoring"
    mkdir -p "$SCRIPT_DIR/backup"
    
    log "✅ Deployment structure created"
}

# Main function
main() {
    log "🔧 Mirai Agent Production Environment Setup"
    log "This script will create a secure production configuration"
    echo
    
    create_deployment_structure
    setup_production_env
    
    echo
    log "🎯 Environment setup completed!"
    log "You can now run the deployment script to deploy to production"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi