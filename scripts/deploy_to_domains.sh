#!/bin/bash

# 🚀 Mirai Agent - Deploy to Production Domains
# Author: AgeeKey
# Date: $(date +%Y-%m-%d)

set -e

echo "🚀 Starting Mirai Agent Production Deployment..."

# Configuration
REPO_URL="https://github.com/AgeeKey/mirai-agent.git"
DEPLOY_DIR="/opt/mirai-agent"
DOMAINS=("mirai-agent.com" "mirai-chan.com")
WEB_PORT=80
API_PORT=8002
BACKUP_DIR="/backup/mirai-$(date +%Y%m%d_%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root for production deployment"
fi

# 1. System Preparation
log "Preparing system for deployment..."

# Update system
apt-get update && apt-get upgrade -y

# Install required packages
apt-get install -y \
    docker.io \
    docker-compose \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    htop \
    ufw \
    fail2ban

# Start and enable Docker
systemctl start docker
systemctl enable docker

# 2. Firewall Configuration
log "Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8002/tcp
ufw --force enable

# 3. Create backup of existing deployment
if [ -d "$DEPLOY_DIR" ]; then
    log "Creating backup of existing deployment..."
    mkdir -p "$(dirname "$BACKUP_DIR")"
    cp -r "$DEPLOY_DIR" "$BACKUP_DIR"
    success "Backup created at $BACKUP_DIR"
fi

# 4. Clone/Update Repository
log "Setting up application directory..."
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

if [ -d ".git" ]; then
    log "Updating existing repository..."
    git fetch origin
    git reset --hard origin/main
else
    log "Cloning repository..."
    cd /opt
    rm -rf mirai-agent
    git clone "$REPO_URL" mirai-agent
    cd mirai-agent
fi

# 5. Environment Configuration
log "Setting up environment..."

# Create production environment file
cat > .env.production << EOF
# Production Environment
NODE_ENV=production
ENVIRONMENT=production

# API Configuration
API_HOST=0.0.0.0
API_PORT=8002
API_URL=https://api.mirai-agent.com

# Database
DATABASE_URL=sqlite:///state/mirai.db

# Security
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# Trading (TESTNET for initial deployment)
BINANCE_API_KEY=test_api_key
BINANCE_SECRET_KEY=test_secret_key
BINANCE_TESTNET=true

# Domains
PRIMARY_DOMAIN=mirai-agent.com
SECONDARY_DOMAIN=mirai-chan.com

# SSL
SSL_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/mirai-agent/app.log

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true

# AI Features
AI_ENABLED=true
OPENAI_API_KEY=your_openai_key_here

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
EOF

# 6. SSL Certificates Setup
log "Setting up SSL certificates..."
for domain in "${DOMAINS[@]}"; do
    log "Setting up SSL for $domain..."
    
    # Create temporary nginx config for certificate generation
    cat > "/etc/nginx/sites-available/$domain" << EOF
server {
    listen 80;
    server_name $domain www.$domain;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF
    
    ln -sf "/etc/nginx/sites-available/$domain" "/etc/nginx/sites-enabled/$domain"
done

# Remove default nginx site
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t && systemctl restart nginx

# Generate SSL certificates
for domain in "${DOMAINS[@]}"; do
    log "Generating SSL certificate for $domain..."
    certbot --nginx -d "$domain" -d "www.$domain" --non-interactive --agree-tos --email admin@"$domain" || warning "SSL setup for $domain failed, continuing..."
done

# 7. Nginx Production Configuration
log "Setting up production Nginx configuration..."

# Main domain (mirai-agent.com) - Trading Interface
cat > /etc/nginx/sites-available/mirai-agent.com << 'EOF'
upstream api_backend {
    server 127.0.0.1:8002;
}

upstream web_frontend {
    server 127.0.0.1:3002;
}

server {
    listen 80;
    server_name mirai-agent.com www.mirai-agent.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mirai-agent.com www.mirai-agent.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/mirai-agent.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mirai-agent.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' wss: https:; font-src 'self'; object-src 'none';";

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/css text/javascript text/xml text/plain application/javascript application/xml+rss application/json;

    # Root directory for static files
    root /opt/mirai-agent/web/services/out;
    index index.html index.htm;

    # API Proxy
    location /api/ {
        proxy_pass http://api_backend/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location / {
        try_files $uri $uri/ /index.html;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Secondary domain (mirai-chan.com) - AI Companion Interface
cat > /etc/nginx/sites-available/mirai-chan.com << 'EOF'
upstream api_backend_chan {
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name mirai-chan.com www.mirai-chan.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mirai-chan.com www.mirai-chan.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/mirai-chan.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mirai-chan.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' wss: https:; font-src 'self'; object-src 'none';";

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/css text/javascript text/xml text/plain application/javascript application/xml+rss application/json;

    # Root directory for static files
    root /opt/mirai-agent/web/services/out;
    index index.html index.htm;

    # Set domain context for the application
    location / {
        try_files $uri $uri/ /index.html;
        expires 1d;
        add_header Cache-Control "public, immutable";
        add_header X-Domain-Context "mirai-chan";
    }

    # API Proxy with domain context
    location /api/ {
        proxy_pass http://api_backend_chan/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Domain-Context "mirai-chan";
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://api_backend_chan;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Domain-Context "mirai-chan";
    }

    # Health check
    location /health {
        access_log off;
        return 200 "mirai-chan healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable sites
ln -sf /etc/nginx/sites-available/mirai-agent.com /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/mirai-chan.com /etc/nginx/sites-enabled/

# 8. Docker Production Setup
log "Setting up Docker production environment..."

# Create production docker-compose
cat > docker-compose.production.yml << 'EOF'
version: '3.8'

services:
  # API Backend
  api:
    build:
      context: .
      dockerfile: app/api/Dockerfile
    container_name: mirai-api-prod
    ports:
      - "8002:8002"
    environment:
      - NODE_ENV=production
      - API_HOST=0.0.0.0
      - API_PORT=8002
    env_file:
      - .env.production
    volumes:
      - ./state:/app/state
      - ./logs:/app/logs
      - ./configs:/app/configs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - mirai-network

  # Trading Engine
  trader:
    build:
      context: .
      dockerfile: app/trader/Dockerfile
    container_name: mirai-trader-prod
    environment:
      - NODE_ENV=production
    env_file:
      - .env.production
    volumes:
      - ./state:/app/state
      - ./logs:/app/logs
      - ./configs:/app/configs
    restart: unless-stopped
    depends_on:
      - api
    networks:
      - mirai-network

  # Telegram Bot
  telegram-bot:
    build:
      context: .
      dockerfile: app/telegram_bot/Dockerfile
    container_name: mirai-telegram-prod
    environment:
      - NODE_ENV=production
    env_file:
      - .env.production
    volumes:
      - ./state:/app/state
      - ./logs:/app/logs
    restart: unless-stopped
    depends_on:
      - api
    networks:
      - mirai-network

  # Monitoring - Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: mirai-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./infra/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    networks:
      - mirai-network

  # Monitoring - Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: mirai-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infra/grafana:/etc/grafana/provisioning
    restart: unless-stopped
    networks:
      - mirai-network

volumes:
  prometheus_data:
  grafana_data:

networks:
  mirai-network:
    driver: bridge
EOF

# 9. Build and Deploy Application
log "Building and deploying application..."

# Create necessary directories
mkdir -p logs state reports
chmod 755 logs state reports

# Build web frontend for production
cd web/services
npm install
npm run build
cd ../..

# Build and start containers
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d

# 10. System Service Setup
log "Setting up system services..."

# Create systemd service for Mirai Agent
cat > /etc/systemd/system/mirai-agent.service << 'EOF'
[Unit]
Description=Mirai Agent Trading System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/mirai-agent
ExecStart=/usr/bin/docker-compose -f docker-compose.production.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.production.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable mirai-agent
systemctl start mirai-agent

# 11. Log Management
log "Setting up log management..."

# Create log rotation
cat > /etc/logrotate.d/mirai-agent << 'EOF'
/opt/mirai-agent/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        /usr/bin/docker-compose -f /opt/mirai-agent/docker-compose.production.yml restart api trader telegram-bot
    endscript
}
EOF

# 12. Monitoring Setup
log "Setting up monitoring and alerts..."

# Create monitoring script
cat > /opt/mirai-agent/scripts/monitor.sh << 'EOF'
#!/bin/bash

# Mirai Agent Health Monitor
LOG_FILE="/var/log/mirai-agent/monitor.log"
ALERT_EMAIL="admin@mirai-agent.com"

check_service() {
    local service=$1
    local url=$2
    
    if curl -sSf "$url" > /dev/null 2>&1; then
        echo "$(date): $service is healthy" >> "$LOG_FILE"
        return 0
    else
        echo "$(date): $service is DOWN!" >> "$LOG_FILE"
        # Send alert email (requires mail setup)
        echo "$service is down on $(hostname)" | mail -s "Mirai Agent Alert" "$ALERT_EMAIL" 2>/dev/null || true
        return 1
    fi
}

# Check services
check_service "API" "http://localhost:8002/health"
check_service "Main Domain" "https://mirai-agent.com/health"
check_service "Secondary Domain" "https://mirai-chan.com/health"

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "$(date): Disk usage is ${DISK_USAGE}%" >> "$LOG_FILE"
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ "$MEMORY_USAGE" -gt 85 ]; then
    echo "$(date): Memory usage is ${MEMORY_USAGE}%" >> "$LOG_FILE"
fi
EOF

chmod +x /opt/mirai-agent/scripts/monitor.sh

# Add to crontab for regular monitoring
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/mirai-agent/scripts/monitor.sh") | crontab -

# 13. SSL Auto-renewal
log "Setting up SSL auto-renewal..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

# 14. Final Configuration
log "Applying final configuration..."

# Test nginx configuration
nginx -t && systemctl restart nginx

# Wait for services to start
sleep 30

# 15. Health Checks
log "Performing health checks..."

check_health() {
    local service=$1
    local url=$2
    local max_retries=5
    local retry=0
    
    while [ $retry -lt $max_retries ]; do
        if curl -sSf "$url" > /dev/null 2>&1; then
            success "$service is healthy"
            return 0
        else
            retry=$((retry + 1))
            warning "$service check failed, retry $retry/$max_retries"
            sleep 10
        fi
    done
    
    error "$service failed health check"
}

# Health checks
check_health "API Backend" "http://localhost:8002/health"
check_health "Docker Services" "http://localhost:8002/api/status"

# Domain checks (if DNS is configured)
if nslookup mirai-agent.com > /dev/null 2>&1; then
    check_health "Main Domain" "https://mirai-agent.com/health"
fi

if nslookup mirai-chan.com > /dev/null 2>&1; then
    check_health "Secondary Domain" "https://mirai-chan.com/health"
fi

# 16. Deployment Summary
log "Creating deployment summary..."

cat > /opt/mirai-agent/DEPLOYMENT_SUMMARY.md << EOF
# Mirai Agent Production Deployment Summary

## Deployment Information
- **Date**: $(date)
- **Version**: $(git rev-parse --short HEAD)
- **Deploy Directory**: $DEPLOY_DIR
- **Backup Location**: $BACKUP_DIR

## Services Status
$(docker-compose -f docker-compose.production.yml ps)

## Domain Configuration
- **Primary Domain**: mirai-agent.com (Trading Interface)
- **Secondary Domain**: mirai-chan.com (AI Companion)
- **API Endpoint**: https://api.mirai-agent.com
- **Monitoring**: https://mirai-agent.com:3000 (Grafana)

## SSL Certificates
$(certbot certificates)

## Health Endpoints
- API: http://localhost:8002/health
- Main Domain: https://mirai-agent.com/health
- Secondary Domain: https://mirai-chan.com/health

## Important Files
- Environment: /opt/mirai-agent/.env.production
- Nginx Config: /etc/nginx/sites-available/
- SSL Certificates: /etc/letsencrypt/live/
- Logs: /opt/mirai-agent/logs/
- State: /opt/mirai-agent/state/

## Monitoring
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin123)
- Log Monitoring: /var/log/mirai-agent/monitor.log

## Maintenance Commands
- Restart Services: \`systemctl restart mirai-agent\`
- View Logs: \`docker-compose -f docker-compose.production.yml logs -f\`
- Update Application: \`cd /opt/mirai-agent && git pull && docker-compose -f docker-compose.production.yml up -d --build\`
- SSL Renewal: \`certbot renew\`

## Security Notes
- Firewall configured with UFW
- Fail2ban installed for intrusion protection
- SSL/TLS certificates auto-renewing
- Security headers configured in Nginx
- API rate limiting enabled

## Next Steps
1. Configure DNS records for domains
2. Set up external monitoring (e.g., UptimeRobot)
3. Configure backup strategy
4. Set up log aggregation
5. Configure alerts and notifications

## Support
For technical support, check the logs and health endpoints above.
EOF

success "🎉 Mirai Agent has been successfully deployed to production!"
success "📝 Deployment summary: /opt/mirai-agent/DEPLOYMENT_SUMMARY.md"

echo
echo "🌐 Your domains should be accessible at:"
echo "   • https://mirai-agent.com (Trading Interface)"
echo "   • https://mirai-chan.com (AI Companion)"
echo
echo "📊 Monitoring:"
echo "   • Grafana: http://your-server-ip:3000"
echo "   • Prometheus: http://your-server-ip:9090"
echo
echo "🔧 Management:"
echo "   • Restart: systemctl restart mirai-agent"
echo "   • Logs: docker-compose -f docker-compose.production.yml logs -f"
echo "   • Status: docker-compose -f docker-compose.production.yml ps"

log "Deployment completed successfully! 🚀"