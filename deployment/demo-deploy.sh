#!/bin/bash

# Quick Demo Deployment for Local Testing
# Sets up aimirai.online and aimirai.info on localhost

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"; }
info() { echo -e "${BLUE}[INFO] $1${NC}"; }
warn() { echo -e "${YELLOW}[WARNING] $1${NC}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log "🚀 Starting Mirai Agent Demo Deployment"
log "This will set up a local demo on ports 8000 (trading) and 8001 (services)"

# Create demo environment
create_demo_env() {
    log "Creating demo environment..."
    
    cat > "$PROJECT_ROOT/.env.demo" << EOF
# Demo Environment for Local Testing
POSTGRES_ADMIN_PASSWORD=demo123
POSTGRES_TRADING_PASSWORD=trading123
POSTGRES_SERVICES_PASSWORD=services123
JWT_SECRET=demo_jwt_secret_key_for_testing_only
GRAFANA_ADMIN_PASSWORD=admin
BINANCE_TESTNET=true
LOG_LEVEL=INFO
EOF

    log "✅ Demo environment created"
}

# Create demo docker-compose
create_demo_compose() {
    log "Creating demo docker-compose..."
    
    cat > "$PROJECT_ROOT/docker-compose.demo.yml" << EOF
version: '3.8'

networks:
  mirai-demo:
    driver: bridge

volumes:
  demo_postgres_data:
  demo_redis_data:

services:
  # Trading Platform (aimirai.online simulation)
  mirai-trading:
    build:
      context: ./microservices
      dockerfile: Dockerfile
    container_name: mirai-demo-trading
    ports:
      - "8000:8000"
    environment:
      - PLATFORM_TYPE=trading
      - JWT_SECRET=demo_jwt_secret_key_for_testing_only
    networks:
      - mirai-demo
    command: ["python", "-m", "uvicorn", "gateway:app", "--host", "0.0.0.0", "--port", "8000"]

  # Services Platform (aimirai.info simulation)  
  mirai-services:
    build:
      context: ./microservices
      dockerfile: Dockerfile
    container_name: mirai-demo-services
    ports:
      - "8001:8001"
    environment:
      - PLATFORM_TYPE=services
      - JWT_SECRET=demo_jwt_secret_key_for_testing_only
    networks:
      - mirai-demo
    command: ["python", "-m", "uvicorn", "gateway:app", "--host", "0.0.0.0", "--port", "8001"]

  # AI Engine
  mirai-ai:
    build:
      context: ./microservices
      dockerfile: Dockerfile
    container_name: mirai-demo-ai
    ports:
      - "8010:8010"
    networks:
      - mirai-demo
    command: ["python", "-m", "uvicorn", "ai_simple:app", "--host", "0.0.0.0", "--port", "8010"]

  # Portfolio Manager
  mirai-portfolio:
    build:
      context: ./microservices
      dockerfile: Dockerfile
    container_name: mirai-demo-portfolio
    ports:
      - "8011:8011"
    networks:
      - mirai-demo
    command: ["python", "-m", "uvicorn", "portfolio_simple:app", "--host", "0.0.0.0", "--port", "8011"]

  # Redis for demo
  redis-demo:
    image: redis:7-alpine
    container_name: mirai-demo-redis
    networks:
      - mirai-demo
    command: redis-server --appendonly yes
EOF

    log "✅ Demo compose created"
}

# Create simple microservices Dockerfile
create_microservices_dockerfile() {
    log "Creating microservices Dockerfile..."
    
    cat > "$PROJECT_ROOT/microservices/Dockerfile" << EOF
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \\
    CMD curl -f http://localhost:8000/healthz || exit 1

EXPOSE 8000 8001 8010 8011

CMD ["python", "-m", "uvicorn", "gateway:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    # Create requirements.txt for microservices
    cat > "$PROJECT_ROOT/microservices/requirements.txt" << EOF
fastapi==0.117.1
uvicorn[standard]==0.36.0
pyjwt==2.10.1
httpx==0.28.1
redis==6.4.0
pydantic==2.11.9
python-multipart==0.0.12
EOF

    log "✅ Microservices Dockerfile created"
}

# Start demo
start_demo() {
    log "Starting demo deployment..."
    
    cd "$PROJECT_ROOT"
    
    # Load demo environment
    set -a
    source .env.demo
    set +a
    
    # Build and start services
    info "Building demo images..."
    docker-compose -f docker-compose.demo.yml build
    
    info "Starting demo services..."
    docker-compose -f docker-compose.demo.yml up -d
    
    # Wait for services to start
    info "Waiting for services to start..."
    sleep 15
    
    log "✅ Demo deployment started!"
}

# Test demo
test_demo() {
    log "Testing demo endpoints..."
    
    # Test trading platform (aimirai.online simulation)
    info "Testing trading platform on port 8000..."
    if curl -f -s "http://localhost:8000/healthz" > /dev/null; then
        echo "✅ Trading platform (8000): OK"
    else
        echo "❌ Trading platform (8000): Failed"
    fi
    
    # Test services platform (aimirai.info simulation)
    info "Testing services platform on port 8001..."
    if curl -f -s "http://localhost:8001/healthz" > /dev/null; then
        echo "✅ Services platform (8001): OK"
    else
        echo "❌ Services platform (8001): Failed"
    fi
    
    # Test AI engine
    info "Testing AI engine on port 8010..."
    if curl -f -s "http://localhost:8010/healthz" > /dev/null; then
        echo "✅ AI Engine (8010): OK"
    else
        echo "❌ AI Engine (8010): Failed"
    fi
    
    # Test portfolio manager
    info "Testing portfolio manager on port 8011..."
    if curl -f -s "http://localhost:8011/healthz" > /dev/null; then
        echo "✅ Portfolio Manager (8011): OK"
    else
        echo "❌ Portfolio Manager (8011): Failed"
    fi
}

# Show demo info
show_demo_info() {
    log "🎉 Demo deployment completed!"
    echo
    info "Demo Access Points:"
    info "  📈 Trading Platform (aimirai.online): http://localhost:8000"
    info "  🔧 Services Platform (aimirai.info): http://localhost:8001"  
    info "  🤖 AI Engine: http://localhost:8010"
    info "  💼 Portfolio Manager: http://localhost:8011"
    echo
    info "Test Authentication:"
    info "  curl -X POST 'http://localhost:8000/auth/login' -H 'Content-Type: application/json' -d '{\"username\": \"admin\", \"password\": \"admin\"}'"
    echo
    info "Phase 2 Microservices:"
    info "  curl 'http://localhost:8010/analyze' -H 'Content-Type: application/json' -d '{\"market_data\": {\"symbol\": \"BTCUSDT\", \"price\": 45000}}'"
    echo
    info "Management Commands:"
    info "  docker-compose -f docker-compose.demo.yml ps     # Show status"
    info "  docker-compose -f docker-compose.demo.yml logs   # Show logs"
    info "  docker-compose -f docker-compose.demo.yml down   # Stop demo"
    echo
    warn "This is a DEMO environment - not for production use!"
}

# Main function
main() {
    create_demo_env
    create_microservices_dockerfile
    create_demo_compose
    start_demo
    test_demo
    show_demo_info
}

# Cleanup function
cleanup_demo() {
    log "Cleaning up demo deployment..."
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.demo.yml down -v
    docker system prune -f
    log "✅ Demo cleanup completed"
}

# Check command line arguments
if [[ "${1:-}" == "cleanup" ]]; then
    cleanup_demo
    exit 0
fi

# Run main deployment
main "$@"