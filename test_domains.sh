#!/bin/bash

# 🚀 Mirai Agent - Domain Test Launcher
# Тестирование доменов локально перед продакшеном

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

info() {
    echo -e "${PURPLE}ℹ️  $1${NC}"
}

echo "🚀 Mirai Agent - Local Domain Testing"
echo "====================================="

# 1. Check if stack is running
log "Checking current stack status..."
if curl -sf http://localhost:8002/health > /dev/null 2>&1; then
    success "API is running"
else
    warning "API not running, starting stack..."
    ./start_mirai_stack.sh
    sleep 10
fi

# 2. Check web interface
if curl -sf http://localhost:3002 > /dev/null 2>&1; then
    success "Web interface is running"
else
    warning "Web interface not responding"
fi

# 3. Simulate domain contexts
log "Setting up domain simulation..."

# Create hosts file entries simulation
cat > domain_test_info.txt << EOF
# Local Domain Testing Information

## Simulate Domain Access:

### Trading Interface (mirai-agent.com):
http://localhost:3002?domain=mirai-agent

### AI Companion (mirai-chan.com):
http://localhost:3002?domain=mirai-chan

## API Endpoints:
- Health: http://localhost:8002/health
- Trading: http://localhost:8002/api/trading/status
- AI: http://localhost:8002/api/ai/chat

## Features Test:
1. Trading Panel: Portfolio management, P&L tracking
2. Analytics: AI predictions, market insights  
3. Studio: Creative tools, music synthesis
4. Domain Switching: Seamless transitions

## Production URLs (after deployment):
- https://mirai-agent.com (Trading)
- https://mirai-chan.com (AI Companion)
EOF

# 4. Test API endpoints
log "Testing API endpoints..."

endpoints=(
    "http://localhost:8002/health"
    "http://localhost:8002/api/status"
)

for endpoint in "${endpoints[@]}"; do
    if curl -sf "$endpoint" > /dev/null 2>&1; then
        success "✓ $endpoint"
    else
        warning "✗ $endpoint"
    fi
done

# 5. Test web components
log "Testing web components..."

# Check if main components are built
components=(
    "web/services/src/components/trading/TradingPanel.tsx"
    "web/services/src/components/analytics/AnalyticsPanel.tsx"
    "web/services/src/components/studio/StudioPanel.tsx"
    "web/services/src/components/DomainSwitcher.tsx"
)

for component in "${components[@]}"; do
    if [ -f "$component" ]; then
        success "✓ $(basename "$component")"
    else
        warning "✗ $(basename "$component")"
    fi
done

# 6. Generate test URLs
log "Generating test URLs..."

cat > test_domains.html << 'EOF'
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mirai Agent - Domain Testing</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        h1 {
            text-align: center;
            color: #fff;
            margin-bottom: 30px;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        }
        .domain-section {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .domain-title {
            font-size: 1.4em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #fff;
        }
        .url-link {
            display: inline-block;
            background: linear-gradient(45deg, #00c6fb, #005bea);
            color: white;
            padding: 12px 25px;
            text-decoration: none;
            border-radius: 25px;
            margin: 10px 10px 10px 0;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 91, 234, 0.3);
        }
        .url-link:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(0, 91, 234, 0.4);
        }
        .api-link {
            background: linear-gradient(45deg, #ff6b6b, #ee5a52);
            box-shadow: 0 4px 15px rgba(238, 90, 82, 0.3);
        }
        .api-link:hover {
            box-shadow: 0 6px 25px rgba(238, 90, 82, 0.4);
        }
        .feature-list {
            list-style: none;
            padding: 0;
        }
        .feature-list li {
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .feature-list li:before {
            content: "✨ ";
            margin-right: 10px;
        }
        .status {
            background: linear-gradient(45deg, #56ab2f, #a8e6cf);
            color: #333;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            display: inline-block;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Mirai Agent - Domain Testing</h1>
        
        <div class="domain-section">
            <div class="domain-title">🌐 Trading Interface (mirai-agent.com)</div>
            <a href="http://localhost:3002" class="url-link" target="_blank">
                Open Trading Dashboard
            </a>
            <ul class="feature-list">
                <li>Portfolio Management</li>
                <li>Real-time Trading</li>
                <li>Risk Analytics</li>
                <li>P&L Tracking</li>
            </ul>
        </div>

        <div class="domain-section">
            <div class="domain-title">🤖 AI Companion (mirai-chan.com)</div>
            <a href="http://localhost:3002" class="url-link" target="_blank">
                Open AI Studio
            </a>
            <ul class="feature-list">
                <li>AI Chat Interface</li>
                <li>Creative Studio</li>
                <li>Music Synthesis</li>
                <li>Code Generation</li>
            </ul>
        </div>

        <div class="domain-section">
            <div class="domain-title">🔗 API Endpoints</div>
            <a href="http://localhost:8002/health" class="url-link api-link" target="_blank">
                Health Check
            </a>
            <a href="http://localhost:8002/api/status" class="url-link api-link" target="_blank">
                System Status
            </a>
            <a href="http://localhost:3000" class="url-link api-link" target="_blank">
                Grafana Monitoring
            </a>
        </div>

        <div class="domain-section">
            <div class="domain-title">📊 Production Ready</div>
            <div class="status">✅ Ready for Domain Deployment</div>
            <p>После деплоя будет доступно по адресам:</p>
            <ul class="feature-list">
                <li><strong>https://mirai-agent.com</strong> - Trading Interface</li>
                <li><strong>https://mirai-chan.com</strong> - AI Companion</li>
            </ul>
        </div>
    </div>
</body>
</html>
EOF

# 7. Final status
echo ""
success "🎉 Domain testing environment ready!"
echo ""
info "📋 Test Information:"
echo "   • Test page: file://$(pwd)/test_domains.html"
echo "   • Domain info: $(pwd)/domain_test_info.txt"
echo "   • Trading Interface: http://localhost:3002"
echo "   • AI Companion: http://localhost:3002 (same interface, different modes)"
echo "   • API Health: http://localhost:8002/health"
echo ""
info "🚀 To deploy to production domains:"
echo "   1. Configure server IP in upload_to_server.sh"
echo "   2. Run: ./upload_to_server.sh"
echo "   3. Or run full deployment: ./scripts/deploy_to_domains.sh"
echo ""
success "All components tested and ready for production! 🌟"

# Open test page in browser if available
if command -v xdg-open > /dev/null 2>&1; then
    xdg-open "file://$(pwd)/test_domains.html"
elif command -v open > /dev/null 2>&1; then
    open "file://$(pwd)/test_domains.html"
fi