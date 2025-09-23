#!/bin/bash

# 🌐 Mirai Domains Setup Script
# Настройка доменов aimirai.online и aimirai.info

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}                    ${BLUE}🌐 MIRAI DOMAINS SETUP${NC}                     ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}              ${GREEN}aimirai.online & aimirai.info${NC}                 ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_domain_dns() {
    local domain="$1"
    local server_ip="212.56.33.1"
    
    print_info "Проверка DNS для $domain..."
    
    if nslookup "$domain" | grep -q "$server_ip"; then
        print_status "$domain указывает на $server_ip"
        return 0
    else
        local current_ip=$(nslookup "$domain" | grep "Address:" | tail -1 | awk '{print $2}')
        print_warning "$domain указывает на $current_ip, а не на $server_ip"
        return 1
    fi
}

install_nginx() {
    print_info "Проверка Nginx..."
    
    if ! command -v nginx &> /dev/null; then
        print_info "Устанавливаю Nginx..."
        apt update
        apt install -y nginx
        systemctl enable nginx
        print_status "Nginx установлен"
    else
        print_status "Nginx уже установлен"
    fi
}

setup_ssl_certificates() {
    print_info "Настройка SSL сертификатов..."
    
    # Install certbot if not present
    if ! command -v certbot &> /dev/null; then
        print_info "Устанавливаю Certbot..."
        apt install -y certbot python3-certbot-nginx
    fi
    
    # Get certificates for both domains
    local domains=("aimirai.online" "aimirai.info")
    
    for domain in "${domains[@]}"; do
        if [ ! -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
            print_info "Получение SSL сертификата для $domain..."
            
            # First, create a temporary nginx config to pass verification
            cat > "/etc/nginx/sites-available/temp-$domain" << EOF
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
            
            ln -sf "/etc/nginx/sites-available/temp-$domain" "/etc/nginx/sites-enabled/temp-$domain"
            nginx -t && systemctl reload nginx
            
            # Get certificate
            certbot certonly --webroot -w /var/www/html -d "$domain" -d "www.$domain" --non-interactive --agree-tos --email admin@aimirai.online
            
            if [ $? -eq 0 ]; then
                print_status "SSL сертификат получен для $domain"
                rm -f "/etc/nginx/sites-enabled/temp-$domain"
            else
                print_error "Ошибка получения SSL сертификата для $domain"
            fi
        else
            print_status "SSL сертификат для $domain уже существует"
        fi
    done
}

setup_nginx_config() {
    print_info "Настройка конфигурации Nginx..."
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Copy our configuration
    cp /root/mirai-agent/nginx/mirai-domains.conf /etc/nginx/sites-available/mirai-domains
    ln -sf /etc/nginx/sites-available/mirai-domains /etc/nginx/sites-enabled/mirai-domains
    
    # Test configuration
    if nginx -t; then
        print_status "Конфигурация Nginx корректна"
        systemctl reload nginx
        print_status "Nginx перезагружен"
    else
        print_error "Ошибка в конфигурации Nginx"
        return 1
    fi
}

setup_firewall() {
    print_info "Настройка файрвола..."
    
    # Allow HTTP and HTTPS
    ufw allow 80
    ufw allow 443
    ufw allow 8000  # API port
    ufw allow 3000  # Web port
    
    print_status "Файрвол настроен"
}

check_services() {
    print_info "Проверка сервисов..."
    
    # Check if our services are running
    if curl -s http://localhost:8000 > /dev/null; then
        print_status "API сервер работает на порту 8000"
    else
        print_warning "API сервер не отвечает на порту 8000"
    fi
    
    if curl -s http://localhost:3000 > /dev/null; then
        print_status "Web сервер работает на порту 3000"
    else
        print_warning "Web сервер не отвечает на порту 3000"
    fi
}

test_domains() {
    print_info "Тестирование доменов..."
    
    local domains=("aimirai.online" "aimirai.info")
    
    for domain in "${domains[@]}"; do
        print_info "Тестирую $domain..."
        
        # Test HTTP redirect
        local http_status=$(curl -s -o /dev/null -w "%{http_code}" "http://$domain" || echo "000")
        if [ "$http_status" = "301" ] || [ "$http_status" = "302" ]; then
            print_status "$domain: HTTP редирект работает ($http_status)"
        else
            print_warning "$domain: HTTP статус $http_status"
        fi
        
        # Test HTTPS
        if curl -s -k "https://$domain" > /dev/null; then
            print_status "$domain: HTTPS доступен"
        else
            print_warning "$domain: HTTPS недоступен"
        fi
    done
}

create_domain_routing() {
    print_info "Создание маршрутизации для доменов..."
    
    # Create a simple script to help with domain-specific content
    cat > /root/mirai-agent/scripts/domain-router.js << 'EOF'
// Domain-specific routing for Mirai
const domainRouting = {
    'aimirai.online': {
        name: 'Trading Platform',
        theme: 'trading',
        features: ['trading', 'portfolio', 'analytics', 'api'],
        description: 'Professional AI Trading Platform'
    },
    'aimirai.info': {
        name: 'Mirai-chan Studio',
        theme: 'studio',
        features: ['character', 'chat', 'voice', 'personality'],
        description: 'Mirai-chan Personal Space'
    }
};

function getDomainConfig(hostname) {
    const domain = hostname.replace('www.', '');
    return domainRouting[domain] || domainRouting['aimirai.online'];
}

module.exports = { domainRouting, getDomainConfig };
EOF
    
    print_status "Маршрутизация доменов создана"
}

setup_auto_renewal() {
    print_info "Настройка автообновления SSL сертификатов..."
    
    # Add cron job for certificate renewal
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
    
    print_status "Автообновление SSL настроено"
}

show_status() {
    echo ""
    echo "🌐 === СТАТУС ДОМЕНОВ ==="
    echo ""
    
    print_info "Домены:"
    echo "  🔥 aimirai.online  - Торговая платформа"
    echo "  🎨 aimirai.info    - Студия Mirai-chan"
    echo ""
    
    print_info "SSL сертификаты:"
    for domain in "aimirai.online" "aimirai.info"; do
        if [ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
            local expiry=$(openssl x509 -in "/etc/letsencrypt/live/$domain/fullchain.pem" -noout -dates | grep "notAfter" | cut -d= -f2)
            echo "  ✅ $domain - до $expiry"
        else
            echo "  ❌ $domain - сертификат отсутствует"
        fi
    done
    
    echo ""
    print_info "Nginx статус:"
    if systemctl is-active --quiet nginx; then
        echo "  ✅ Nginx активен"
    else
        echo "  ❌ Nginx неактивен"
    fi
    
    echo ""
    print_info "Тестовые ссылки:"
    echo "  🔗 https://aimirai.online     - Торговая платформа"
    echo "  🔗 https://aimirai.online/api - API документация"
    echo "  🔗 https://aimirai.info      - Студия Mirai-chan"
}

main() {
    print_banner
    
    print_info "Настройка доменов для Mirai Agent..."
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        print_error "Запустите скрипт от имени root"
        exit 1
    fi
    
    # Check DNS
    check_domain_dns "aimirai.online"
    check_domain_dns "aimirai.info"
    
    # Install and configure
    install_nginx
    setup_firewall
    setup_ssl_certificates
    setup_nginx_config
    create_domain_routing
    setup_auto_renewal
    
    # Test everything
    check_services
    test_domains
    
    echo ""
    print_status "🎉 Настройка доменов завершена!"
    
    show_status
    
    echo ""
    print_info "Следующие шаги:"
    echo "  1. Убедитесь, что DNS записи указывают на 212.56.33.1"
    echo "  2. Запустите сервисы: ./manage_services.sh start"
    echo "  3. Проверьте работу: https://aimirai.online"
    echo "  4. Настройте контент для aimirai.info"
}

# Parse command line arguments
case "${1:-setup}" in
    "setup") main ;;
    "status") show_status ;;
    "test") test_domains ;;
    "ssl") setup_ssl_certificates ;;
    *) 
        echo "Usage: $0 {setup|status|test|ssl}"
        echo "  setup  - Full domain setup"
        echo "  status - Show current status"
        echo "  test   - Test domain connectivity"
        echo "  ssl    - Renew SSL certificates"
        ;;
esac