#!/bin/bash

# Upload script for production server
# Run this on your production server

SERVER_IP="YOUR_SERVER_IP"
DEPLOY_USER="root"
DEPLOY_PATH="/opt/mirai-agent"

echo "🚀 Uploading Mirai Agent to production server..."

# Upload files
rsync -avz --delete \
    --exclude=node_modules \
    --exclude=.git \
    --exclude=ai_test_env \
    --exclude=mirai_env \
    --exclude=__pycache__ \
    . $DEPLOY_USER@$SERVER_IP:$DEPLOY_PATH/

# Remote deployment
ssh $DEPLOY_USER@$SERVER_IP << 'REMOTE_SCRIPT'
cd /opt/mirai-agent

# Update dependencies
cd web/services
npm install
npm run build
cd ../..

# Restart services
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d --build

# Wait for services
sleep 30

# Health check
curl -f http://localhost:8002/health || echo "API health check failed"

echo "✅ Deployment completed!"
REMOTE_SCRIPT

echo "✅ Upload completed!"