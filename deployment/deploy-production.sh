#!/bin/bash

# Mirai Agent Production Deployment Script
# Deploys aimirai.online and aimirai.info to production servers

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_DIR="$PROJECT_ROOT/deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check requirements
check_requirements() {
    log "Checking deployment requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if running as root or in docker group
    if [[ $EUID -ne 0 ]] && ! groups $USER | grep -q docker; then
        error "This script must be run as root or user must be in docker group"
        exit 1
    fi
    
    # Check environment file
    if [[ ! -f "$PROJECT_ROOT/.env.production" ]]; then
        error "Production environment file not found: $PROJECT_ROOT/.env.production"
        error "Please create it based on .env.example"
        exit 1
    fi
    
    log "✅ All requirements satisfied"
}

# Load environment variables
load_environment() {
    log "Loading production environment..."
    
    # Load production environment
    set -a
    source "$PROJECT_ROOT/.env.production"
    set +a
    
    # Validate required variables
    required_vars=(
        "POSTGRES_ADMIN_PASSWORD"
        "POSTGRES_TRADING_PASSWORD"
        "POSTGRES_SERVICES_PASSWORD"
        "JWT_SECRET"
        "GRAFANA_ADMIN_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    log "✅ Environment loaded successfully"
}

# Setup directories
setup_directories() {
    log "Setting up deployment directories..."
    
    # Create necessary directories
    mkdir -p "$DEPLOYMENT_DIR/data/postgres"
    mkdir -p "$DEPLOYMENT_DIR/data/redis"
    mkdir -p "$DEPLOYMENT_DIR/data/nginx/cache"
    mkdir -p "$DEPLOYMENT_DIR/data/letsencrypt/certs"
    mkdir -p "$DEPLOYMENT_DIR/data/letsencrypt/www"
    mkdir -p "$DEPLOYMENT_DIR/data/prometheus"
    mkdir -p "$DEPLOYMENT_DIR/data/grafana"
    mkdir -p "$DEPLOYMENT_DIR/logs"
    mkdir -p "$DEPLOYMENT_DIR/state"
    
    # Set permissions
    chmod 755 "$DEPLOYMENT_DIR/data"
    chmod 755 "$DEPLOYMENT_DIR/logs"
    chmod 755 "$DEPLOYMENT_DIR/state"
    
    log "✅ Directories created"
}

# Build Docker images
build_images() {
    log "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build main application image
    info "Building main Mirai image..."
    docker build -t mirai-agent:latest -f Dockerfile .
    
    # Build API image
    info "Building API image..."
    docker build -t mirai-api:latest -f app/api/Dockerfile .
    
    # Build dashboard image
    info "Building dashboard image..."
    docker build -t mirai-dashboard:latest -f web/services/Dockerfile ./web/services
    
    # Build microservices image
    info "Building microservices image..."
    docker build -t mirai-microservices:latest -f microservices/Dockerfile ./microservices
    
    log "✅ All images built successfully"
}

# Setup SSL certificates
setup_ssl() {
    log "Setting up SSL certificates..."
    
    # Create nginx configuration for initial SSL setup
    info "Creating initial nginx configuration..."
    
    # Start nginx with basic configuration for ACME challenge
    docker run -d \
        --name nginx-temp \
        -p 80:80 \
        -v "$DEPLOYMENT_DIR/data/letsencrypt/www:/var/www/certbot:ro" \
        nginx:alpine
    
    # Wait for nginx to start
    sleep 5
    
    # Request SSL certificates
    info "Requesting SSL certificates for aimirai.online..."
    docker run --rm \
        -v "$DEPLOYMENT_DIR/data/letsencrypt/certs:/etc/letsencrypt" \
        -v "$DEPLOYMENT_DIR/data/letsencrypt/www:/var/www/certbot" \
        certbot/certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email admin@aimirai.info \
        --agree-tos \
        --no-eff-email \
        -d aimirai.online -d www.aimirai.online
    
    info "Requesting SSL certificates for aimirai.info..."
    docker run --rm \
        -v "$DEPLOYMENT_DIR/data/letsencrypt/certs:/etc/letsencrypt" \
        -v "$DEPLOYMENT_DIR/data/letsencrypt/www:/var/www/certbot" \
        certbot/certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email admin@aimirai.info \
        --agree-tos \
        --no-eff-email \
        -d aimirai.info -d www.aimirai.info
    
    # Stop temporary nginx
    docker stop nginx-temp
    docker rm nginx-temp
    
    log "✅ SSL certificates configured"
}

# Deploy services
deploy_services() {
    log "Deploying production services..."
    
    cd "$PROJECT_ROOT"
    
    # Replace password placeholders in SQL files
    info "Preparing database initialization..."
    sed -i "s/TRADING_PASSWORD_PLACEHOLDER/$POSTGRES_TRADING_PASSWORD/g" \
        "$DEPLOYMENT_DIR/sql/init-databases.sql"
    sed -i "s/SERVICES_PASSWORD_PLACEHOLDER/$POSTGRES_SERVICES_PASSWORD/g" \
        "$DEPLOYMENT_DIR/sql/init-databases.sql"
    
    # Start core infrastructure first
    info "Starting core infrastructure..."
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.production.yml" \
        up -d postgres redis
    
    # Wait for database to be ready
    info "Waiting for database to be ready..."
    sleep 30
    
    # Start application services
    info "Starting application services..."
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.production.yml" \
        up -d mirai-api-trading mirai-api-services
    
    # Wait for APIs to be ready
    sleep 20
    
    # Start web services
    info "Starting web services..."
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.production.yml" \
        up -d mirai-dashboard-trading mirai-dashboard-services
    
    # Start gateway services
    info "Starting gateway services..."
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.production.yml" \
        up -d mirai-gateway-trading mirai-ai-gateway
    
    # Start nginx last
    info "Starting nginx reverse proxy..."
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.production.yml" \
        up -d nginx
    
    # Start monitoring
    info "Starting monitoring services..."
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.production.yml" \
        up -d prometheus grafana fluentd
    
    # Start remaining services
    info "Starting remaining services..."
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.production.yml" \
        up -d
    
    log "✅ All services deployed"
}

# Health check
health_check() {
    log "Performing health checks..."
    
    # Wait for services to stabilize
    sleep 30
    
    # Check main services
    services=(
        "aimirai.online/health"
        "aimirai.info/status"
    )
    
    for service in "${services[@]}"; do
        info "Checking $service..."
        if curl -f -s "https://$service" > /dev/null; then
            echo "✅ $service is healthy"
        else
            warn "❌ $service is not responding"
        fi
    done
    
    # Check Docker services
    info "Checking Docker services status..."
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.production.yml" ps
    
    log "✅ Health check completed"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring and alerting..."
    
    # Setup log rotation
    info "Configuring log rotation..."
    cat > /etc/logrotate.d/mirai << EOF
$DEPLOYMENT_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
    
    # Setup systemd service for auto-restart
    info "Creating systemd service..."
    cat > /etc/systemd/system/mirai-agent.service << EOF
[Unit]
Description=Mirai Agent Production
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_ROOT
ExecStart=/usr/bin/docker-compose -f deployment/docker-compose.production.yml up -d
ExecStop=/usr/bin/docker-compose -f deployment/docker-compose.production.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable mirai-agent.service
    
    log "✅ Monitoring configured"
}

# Backup existing deployment
backup_existing() {
    log "Creating backup of existing deployment..."
    
    if [[ -d "$DEPLOYMENT_DIR/data" ]]; then
        backup_dir="$DEPLOYMENT_DIR/backup/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$backup_dir"
        
        # Backup data
        if [[ -d "$DEPLOYMENT_DIR/data/postgres" ]]; then
            info "Backing up database..."
            cp -r "$DEPLOYMENT_DIR/data/postgres" "$backup_dir/"
        fi
        
        # Backup state
        if [[ -d "$DEPLOYMENT_DIR/state" ]]; then
            info "Backing up application state..."
            cp -r "$DEPLOYMENT_DIR/state" "$backup_dir/"
        fi
        
        log "✅ Backup created at $backup_dir"
    else
        info "No existing deployment found, skipping backup"
    fi
}

# Main deployment function
main() {
    log "🚀 Starting Mirai Agent Production Deployment"
    log "Deploying to aimirai.online (trading) and aimirai.info (services)"
    
    # Deployment steps
    check_requirements
    load_environment
    backup_existing
    setup_directories
    build_images
    
    # SSL setup (comment out if certificates already exist)
    # setup_ssl
    
    deploy_services
    health_check
    setup_monitoring
    
    log "🎉 Deployment completed successfully!"
    log ""
    log "📊 Access points:"
    log "  Trading Platform: https://aimirai.online"
    log "  Services Platform: https://aimirai.info"
    log "  Monitoring: https://monitor.aimirai.online"
    log ""
    log "📝 Next steps:"
    log "  1. Configure DNS records for your domains"
    log "  2. Verify SSL certificates are working"
    log "  3. Test both platforms"
    log "  4. Setup monitoring alerts"
    log ""
    log "📁 Logs location: $DEPLOYMENT_DIR/logs/"
    log "📁 Data location: $DEPLOYMENT_DIR/data/"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi