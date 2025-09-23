#!/bin/bash

# Fast Production Deployment for Mirai Agent
set -e

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 Fast Mirai Agent Deployment"
echo "Deploying to aimirai.online (trading) and aimirai.info (services)"

# Load environment
source .env.production 2>/dev/null || true

# Create deployment directories
mkdir -p deployment/data/{postgres,redis} deployment/ssl deployment/logs

# Build fast image
echo "Building optimized Docker image..."
docker build -t mirai-agent:latest -f Dockerfile.fast .

# Generate minimal docker-compose
cat > deployment/docker-compose.fast.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: mirai_production
      POSTGRES_USER: mirai
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-mirai_secure_pass_2024}
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mirai -d mirai_production"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-redis_secure_pass_2024}
    volumes:
      - ./data/redis:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # Trading Platform (aimirai.online)
  mirai-trading:
    image: mirai-agent:latest
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=postgresql://mirai:${POSTGRES_PASSWORD:-mirai_secure_pass_2024}@postgres:5432/mirai_production
      - REDIS_URL=redis://:${REDIS_PASSWORD:-redis_secure_pass_2024}@redis:6379
      - DOMAIN=aimirai.online
      - SERVICE_TYPE=trading
      - DRY_RUN=false
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
      - ./data:/app/state
    restart: unless-stopped

  # Services Platform (aimirai.info)  
  mirai-services:
    image: mirai-agent:latest
    ports:
      - "8002:8000"
    environment:
      - DATABASE_URL=postgresql://mirai:${POSTGRES_PASSWORD:-mirai_secure_pass_2024}@postgres:5432/mirai_production
      - REDIS_URL=redis://:${REDIS_PASSWORD:-redis_secure_pass_2024}@redis:6379
      - DOMAIN=aimirai.info
      - SERVICE_TYPE=services
      - DRY_RUN=false
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
      - ./data:/app/state
    restart: unless-stopped

  # Simple Nginx Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-fast.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - mirai-trading
      - mirai-services
    restart: unless-stopped

networks:
  default:
    name: mirai-fast-network
EOF

# Generate minimal nginx config
cat > deployment/nginx-fast.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream trading {
        server mirai-trading:8000;
    }
    
    upstream services {
        server mirai-services:8000;
    }

    server {
        listen 80;
        server_name aimirai.online;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 80;
        server_name aimirai.info;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name aimirai.online;
        
        location / {
            proxy_pass http://trading;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }

    server {
        listen 443 ssl http2;
        server_name aimirai.info;
        
        location / {
            proxy_pass http://services;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
EOF

cd deployment

# Start services
echo "Starting production services..."
docker-compose -f docker-compose.fast.yml up -d

# Wait for services
echo "Waiting for services to start..."
sleep 30

# Check health
echo "Checking service health..."
for service in postgres redis mirai-trading mirai-services nginx; do
    if docker-compose -f docker-compose.fast.yml ps $service | grep -q "Up"; then
        echo "✅ $service is running"
    else
        echo "❌ $service failed to start"
    fi
done

echo "🎉 Fast deployment complete!"
echo "Trading Platform: http://aimirai.online:80 -> http://localhost:8001"
echo "Services Platform: http://aimirai.info:80 -> http://localhost:8002"
echo ""
echo "Next steps:"
echo "1. Configure SSL certificates"
echo "2. Update DNS records"
echo "3. Monitor logs: docker-compose -f docker-compose.fast.yml logs -f"