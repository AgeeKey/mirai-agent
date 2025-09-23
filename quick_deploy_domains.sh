#!/bin/bash

# 🚀 Quick Deploy to Domains - Mirai Agent
# Быстрый деплой всех изменений на домены

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log() {
    echo -e "${BLUE}🔄 $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo "🚀 Mirai Agent - Quick Domain Deploy"
echo "===================================="

# 1. Commit current changes
log "Committing current changes..."
git add .
git commit -m "Production deploy: $(date '+%Y-%m-%d %H:%M:%S')" || warning "No changes to commit"

# 2. Push to repository
log "Pushing to GitHub..."
git push origin main

# 3. Build production version
log "Building web frontend for production..."
cd web/services
npm run build
cd ../..

# 4. Create production bundle
log "Creating production bundle..."
mkdir -p dist/
tar -czf dist/mirai-agent-$(date +%Y%m%d_%H%M%S).tar.gz \
    --exclude=node_modules \
    --exclude=.git \
    --exclude=dist \
    --exclude=ai_test_env \
    --exclude=mirai_env \
    --exclude=__pycache__ \
    .

# 5. Prepare deployment package
log "Preparing deployment package..."

# Create deployment info
cat > DEPLOY_INFO.json << EOF
{
    "version": "$(git rev-parse --short HEAD)",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "branch": "$(git branch --show-current)",
    "commit_message": "$(git log -1 --pretty=%B | tr '\n' ' ')",
    "domains": ["mirai-agent.com", "mirai-chan.com"],
    "services": {
        "api": "http://localhost:8002",
        "web": "http://localhost:3002",
        "monitoring": "http://localhost:3000"
    }
}
EOF

# 6. Test local build
log "Testing local build..."
if [ ! -f "web/services/out/index.html" ]; then
    warning "Web build not found, building now..."
    cd web/services
    npm run build
    cd ../..
fi

if [ -f "web/services/out/index.html" ]; then
    success "Web build verified"
else
    echo -e "${RED}❌ Web build failed${NC}"
    exit 1
fi

# 7. Create simple upload script
log "Creating upload script..."
cat > upload_to_server.sh << 'EOF'
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
EOF

chmod +x upload_to_server.sh

# 8. Create GitHub Actions deployment workflow
log "Creating GitHub Actions workflow..."
mkdir -p .github/workflows

cat > .github/workflows/deploy-domains.yml << 'EOF'
name: Deploy to Production Domains

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: web/services/package-lock.json
        
    - name: Install dependencies
      run: |
        cd web/services
        npm ci
        
    - name: Build web application
      run: |
        cd web/services
        npm run build
        
    - name: Create deployment package
      run: |
        tar -czf mirai-agent-deploy.tar.gz \
          --exclude=node_modules \
          --exclude=.git \
          --exclude=ai_test_env \
          --exclude=mirai_env \
          --exclude=__pycache__ \
          .
          
    - name: Deploy to server
      if: github.event_name == 'workflow_dispatch'
      run: |
        echo "Manual deployment triggered"
        echo "Upload deployment package to your server and run:"
        echo "cd /opt/mirai-agent && tar -xzf mirai-agent-deploy.tar.gz"
        echo "docker-compose -f docker-compose.production.yml up -d --build"
EOF

# 9. Create domain-specific configurations
log "Creating domain-specific configurations..."

# Domain configuration for nginx
cat > configs/domains.yaml << 'EOF'
domains:
  primary:
    name: "mirai-agent.com"
    type: "trading"
    features:
      - trading_interface
      - portfolio_management
      - risk_monitoring
      - real_time_charts
    analytics:
      google_analytics: "G-TRADING-ID"
      
  secondary:
    name: "mirai-chan.com"
    type: "ai_companion"
    features:
      - ai_chat
      - creative_studio
      - personality_engine
      - social_features
    analytics:
      google_analytics: "G-AI-COMPANION-ID"

shared_features:
  - api_access
  - user_authentication
  - health_monitoring
  - ssl_termination
EOF

# 10. Create quick update script
log "Creating quick update script..."
cat > quick_update.sh << 'EOF'
#!/bin/bash

# Quick update for production
echo "🔄 Quick update starting..."

# Build web
cd web/services && npm run build && cd ../..

# Restart web container only
docker-compose -f docker-compose.production.yml restart api

# Health check
sleep 10
curl -f http://localhost:8002/health && echo "✅ Update completed!" || echo "❌ Update failed!"
EOF

chmod +x quick_update.sh

# 11. Create monitoring dashboard
log "Creating monitoring dashboard..."
cat > monitoring_check.sh << 'EOF'
#!/bin/bash

# Quick monitoring check
echo "📊 Mirai Agent Status Check"
echo "=========================="

# API Health
echo -n "API Status: "
if curl -sf http://localhost:8002/health > /dev/null; then
    echo "✅ Healthy"
else
    echo "❌ Down"
fi

# Docker containers
echo -e "\n🐳 Docker Containers:"
docker-compose -f docker-compose.production.yml ps

# Disk space
echo -e "\n💾 Disk Usage:"
df -h /

# Memory usage
echo -e "\n🧠 Memory Usage:"
free -h

# Recent logs
echo -e "\n📝 Recent API Logs:"
docker-compose -f docker-compose.production.yml logs --tail=10 api

echo -e "\n✅ Status check completed!"
EOF

chmod +x monitoring_check.sh

# 12. Final summary
success "🎉 Quick deploy package created!"

echo ""
echo "📦 Created files:"
echo "   • DEPLOY_INFO.json - Deployment information"
echo "   • upload_to_server.sh - Server upload script"
echo "   • .github/workflows/deploy-domains.yml - GitHub Actions"
echo "   • configs/domains.yaml - Domain configuration"
echo "   • quick_update.sh - Quick production updates"
echo "   • monitoring_check.sh - Status monitoring"
echo ""

echo "🚀 To deploy to your domains:"
echo "   1. Configure your production server IP in upload_to_server.sh"
echo "   2. Run: ./upload_to_server.sh"
echo "   3. Or use the full deployment: ./scripts/deploy_to_domains.sh"
echo ""

echo "⚡ For quick updates:"
echo "   • Local: ./quick_update.sh"
echo "   • Monitor: ./monitoring_check.sh"
echo ""

echo "🌐 Your domains will be:"
echo "   • https://mirai-agent.com (Trading Interface)"
echo "   • https://mirai-chan.com (AI Companion)"
echo ""

success "All files prepared! Ready for domain deployment! 🚀"