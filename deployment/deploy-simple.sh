#!/bin/bash

# Simple Production Deployment using Docker Run
set -e

echo "🚀 Mirai Agent - Simple Production Deployment"
echo "Trading: aimirai.online"
echo "Services: aimirai.info"

# Create network
docker network create mirai-simple || true

# Create data directories
mkdir -p /root/mirai-agent/deployment/data/{postgres,redis,sqlite}
touch /root/mirai-agent/deployment/data/sqlite/mirai.db
chmod 666 /root/mirai-agent/deployment/data/sqlite/mirai.db

# Start PostgreSQL
echo "Starting PostgreSQL..."
docker run -d --name mirai-postgres \
  --network mirai-simple \
  -e POSTGRES_DB=mirai_production \
  -e POSTGRES_USER=mirai \
  -e POSTGRES_PASSWORD=mirai_secure_pass_2024 \
  -v /root/mirai-agent/deployment/data/postgres:/var/lib/postgresql/data \
  postgres:15-alpine

# Start Redis
echo "Starting Redis..."
docker run -d --name mirai-redis \
  --network mirai-simple \
  -v /root/mirai-agent/deployment/data/redis:/data \
  redis:7-alpine redis-server --appendonly yes --requirepass redis_secure_pass_2024

# Wait for databases
echo "Waiting for databases..."
sleep 20

# Start Trading Platform
echo "Starting Trading Platform (aimirai.online)..."
docker run -d --name mirai-trading \
  --network mirai-simple \
  -p 8001:8000 \
  -e DATABASE_URL=postgresql://mirai:mirai_secure_pass_2024@mirai-postgres:5432/mirai_production \
  -e REDIS_URL=redis://:redis_secure_pass_2024@mirai-redis:6379 \
  -e DOMAIN=aimirai.online \
  -e SERVICE_TYPE=trading \
  -e DRY_RUN=false \
  -v /root/mirai-agent/deployment/logs:/app/logs \
  -v /root/mirai-agent/deployment/data/sqlite:/app/state \
  mirai-agent:latest uvicorn app.api.mirai_api.main:app --host 0.0.0.0 --port 8000

# Start Services Platform
echo "Starting Services Platform (aimirai.info)..."
docker run -d --name mirai-services \
  --network mirai-simple \
  -p 8002:8000 \
  -e DATABASE_URL=postgresql://mirai:mirai_secure_pass_2024@mirai-postgres:5432/mirai_production \
  -e REDIS_URL=redis://:redis_secure_pass_2024@mirai-redis:6379 \
  -e DOMAIN=aimirai.info \
  -e SERVICE_TYPE=services \
  -e DRY_RUN=false \
  -v /root/mirai-agent/deployment/logs:/app/logs \
  -v /root/mirai-agent/deployment/data/sqlite:/app/state \
  mirai-agent:latest uvicorn app.api.mirai_api.main:app --host 0.0.0.0 --port 8000

# Simple Nginx proxy
echo "Starting Nginx proxy..."
cat > /root/mirai-agent/deployment/nginx-simple.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream trading {
        server host.docker.internal:8001;
    }
    
    upstream services {
        server host.docker.internal:8002;
    }

    server {
        listen 80;
        server_name aimirai.online;
        
        location / {
            proxy_pass http://trading;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }

    server {
        listen 80;
        server_name aimirai.info;
        
        location / {
            proxy_pass http://services;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
EOF

docker run -d --name mirai-nginx \
  --network host \
  -v /root/mirai-agent/deployment/nginx-simple.conf:/etc/nginx/nginx.conf:ro \
  nginx:alpine

# Wait and check
sleep 30

echo "🎉 Deployment complete!"
echo ""
echo "Services status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Testing endpoints:"
echo "Trading Platform: http://localhost:8001"
echo "Services Platform: http://localhost:8002"
echo ""
echo "Public URLs:"
echo "Trading: http://aimirai.online"
echo "Services: http://aimirai.info"

# Test endpoints
echo ""
echo "Health checks:"
if curl -s http://localhost:8001/ >/dev/null 2>&1; then
    echo "✅ Trading platform is responding"
else
    echo "❌ Trading platform is not responding"
fi

if curl -s http://localhost:8002/ >/dev/null 2>&1; then
    echo "✅ Services platform is responding"
else
    echo "❌ Services platform is not responding"
fi