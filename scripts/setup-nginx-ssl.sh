#!/bin/bash

# 🔐 Mirai Agent - Настройка SSL сертификатов и Nginx
# Установка Let's Encrypt сертификатов для доменов

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}   MIRAI AGENT - НАСТРОЙКА NGINX SSL  ${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

DOMAINS=("aimirai.info" "aimirai.online")
EMAIL="admin@aimirai.info"  # Замените на свой email

# 1. Установка Certbot если нужно
echo -e "${BLUE}📦 Проверка Certbot${NC}"
echo "----------------------------------------"
if ! command -v certbot &> /dev/null; then
    echo "Устанавливаем Certbot..."
    sudo apt update
    sudo apt install -y certbot python3-certbot-nginx
    echo -e "${GREEN}✅${NC} Certbot установлен"
else
    echo -e "${GREEN}✅${NC} Certbot уже установлен"
fi
echo ""

# 2. Проверка статуса доменов
echo -e "${BLUE}🌐 Проверка доменов${NC}"
echo "----------------------------------------"
for domain in "${DOMAINS[@]}"; do
    echo "Проверяем $domain..."
    if ping -c 1 -W 5 "$domain" >/dev/null 2>&1; then
        ip=$(dig +short "$domain" | head -1)
        echo -e "  ${GREEN}✅${NC} $domain -> $ip"
    else
        echo -e "  ${YELLOW}⚠️${NC} $domain недоступен"
    fi
done
echo ""

# 3. Создание временных конфигураций без SSL
echo -e "${BLUE}⚙️ Создание временных конфигураций${NC}"
echo "----------------------------------------"

# Временная конфигурация для aimirai.info
cat > /tmp/aimirai.info.temp.conf << 'EOF'
server {
    listen 80;
    server_name aimirai.info www.aimirai.info;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Временная конфигурация для aimirai.online
cat > /tmp/aimirai.online.temp.conf << 'EOF'
server {
    listen 80;
    server_name aimirai.online www.aimirai.online;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8085;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Устанавливаем временные конфигурации
sudo cp /tmp/aimirai.info.temp.conf /etc/nginx/sites-available/aimirai.info.temp
sudo cp /tmp/aimirai.online.temp.conf /etc/nginx/sites-available/aimirai.online.temp

# Активируем временные конфигурации
sudo ln -sf /etc/nginx/sites-available/aimirai.info.temp /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/aimirai.online.temp /etc/nginx/sites-enabled/

# Создаем директорию для acme-challenge
sudo mkdir -p /var/www/html/.well-known/acme-challenge
sudo chown -R www-data:www-data /var/www/html

# Тестируем и перезагружаем Nginx
sudo nginx -t && sudo systemctl reload nginx
echo -e "${GREEN}✅${NC} Временные конфигурации установлены"
echo ""

# 4. Получение SSL сертификатов
echo -e "${BLUE}🔐 Получение SSL сертификатов${NC}"
echo "----------------------------------------"

for domain in "${DOMAINS[@]}"; do
    echo "Получаем сертификат для $domain..."
    
    if sudo certbot certonly \
        --webroot \
        --webroot-path=/var/www/html \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --force-renewal \
        -d "$domain" \
        -d "www.$domain"; then
        echo -e "${GREEN}✅${NC} Сертификат для $domain получен"
    else
        echo -e "${RED}❌${NC} Ошибка получения сертификата для $domain"
        echo "Проверьте:"
        echo "  1. Домен указывает на этот сервер"
        echo "  2. Порт 80 открыт"
        echo "  3. Nginx работает"
        
        # Продолжаем с самоподписанным сертификатом
        echo "Создаем самоподписанный сертификат..."
        sudo mkdir -p "/etc/letsencrypt/live/$domain"
        sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "/etc/letsencrypt/live/$domain/privkey.pem" \
            -out "/etc/letsencrypt/live/$domain/fullchain.pem" \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=$domain"
        echo -e "${YELLOW}⚠️${NC} Самоподписанный сертификат создан для $domain"
    fi
done
echo ""

# 5. Установка финальных конфигураций
echo -e "${BLUE}🔧 Установка финальных конфигураций${NC}"
echo "----------------------------------------"

# Копируем подготовленные конфигурации
sudo cp /root/mirai-agent/nginx/aimirai.info.conf /etc/nginx/sites-available/
sudo cp /root/mirai-agent/nginx/aimirai.online.conf /etc/nginx/sites-available/

# Удаляем временные конфигурации
sudo rm -f /etc/nginx/sites-enabled/aimirai.info.temp
sudo rm -f /etc/nginx/sites-enabled/aimirai.online.temp

# Активируем финальные конфигурации
sudo ln -sf /etc/nginx/sites-available/aimirai.info.conf /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/aimirai.online.conf /etc/nginx/sites-enabled/

# Создаем файл паролей для ChromaDB (если нужно)
if [ ! -f /etc/nginx/.htpasswd ]; then
    echo "Создаем пароль для ChromaDB админки..."
    echo "admin:\$(openssl passwd -apr1 'mirai-admin-2025')" | sudo tee /etc/nginx/.htpasswd > /dev/null
    echo -e "${GREEN}✅${NC} Пароль создан (admin/mirai-admin-2025)"
fi

# Тестируем конфигурацию
if sudo nginx -t; then
    echo -e "${GREEN}✅${NC} Конфигурация Nginx корректна"
    sudo systemctl reload nginx
    echo -e "${GREEN}✅${NC} Nginx перезагружен"
else
    echo -e "${RED}❌${NC} Ошибка в конфигурации Nginx"
    echo "Восстанавливаем временные конфигурации..."
    sudo ln -sf /etc/nginx/sites-available/aimirai.info.temp /etc/nginx/sites-enabled/
    sudo ln -sf /etc/nginx/sites-available/aimirai.online.temp /etc/nginx/sites-enabled/
    sudo systemctl reload nginx
    exit 1
fi
echo ""

# 6. Настройка автообновления сертификатов
echo -e "${BLUE}🔄 Настройка автообновления${NC}"
echo "----------------------------------------"

# Создаем cron job для автообновления
CRON_JOB="0 12 * * * /usr/bin/certbot renew --quiet && /usr/bin/systemctl reload nginx"

# Проверяем есть ли уже такая задача
if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | sudo crontab -
    echo -e "${GREEN}✅${NC} Автообновление сертификатов настроено"
else
    echo -e "${GREEN}✅${NC} Автообновление уже настроено"
fi
echo ""

# 7. Проверка конфигурации
echo -e "${BLUE}🧪 Финальная проверка${NC}"
echo "----------------------------------------"

echo "Проверяем доступность сервисов..."

services=("3000:Frontend" "8001:API" "8080:Orchestrator" "8085:SuperAGI")
for service in "${services[@]}"; do
    port=$(echo $service | cut -d: -f1)
    name=$(echo $service | cut -d: -f2)
    
    if curl -f -s "http://localhost:$port" >/dev/null; then
        echo -e "  ${GREEN}✅${NC} $name ($port)"
    else
        echo -e "  ${YELLOW}⚠️${NC} $name ($port) - не отвечает"
    fi
done
echo ""

echo "Проверяем SSL сертификаты..."
for domain in "${DOMAINS[@]}"; do
    if [ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
        expiry=$(sudo openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$domain/fullchain.pem" | cut -d= -f2)
        echo -e "  ${GREEN}✅${NC} $domain - действует до $expiry"
    else
        echo -e "  ${RED}❌${NC} $domain - сертификат не найден"
    fi
done
echo ""

# 8. Итоговая информация
echo -e "${BLUE}📋 ИТОГОВАЯ ИНФОРМАЦИЯ${NC}"
echo "----------------------------------------"
echo "Доступные сайты:"
echo "  🌐 https://aimirai.info - Основной сайт Mirai (Frontend + API)"
echo "  🤖 https://aimirai.online - AI панель управления (SuperAGI + Orchestrator)"
echo ""
echo "AI сервисы:"
echo "  📊 https://aimirai.online/dashboard - AI Dashboard"
echo "  🔧 https://aimirai.online/orchestrator - Orchestrator API"
echo "  🚀 https://aimirai.online/autogpt - AutoGPT API"
echo "  💾 https://aimirai.online/chroma - ChromaDB (admin/mirai-admin-2025)"
echo ""
echo "API endpoints:"
echo "  📈 https://aimirai.info/api - Основной API"
echo "  🔍 https://aimirai.online/api/monitor - Мониторинг AI"
echo "  ❤️ https://aimirai.online/health/all - Health check всех сервисов"
echo ""

if command -v systemctl >/dev/null; then
    nginx_status=$(sudo systemctl is-active nginx)
    echo "Статус Nginx: $nginx_status"
fi

echo ""
echo -e "${GREEN}🎉 Nginx и SSL настроены успешно!${NC}"
echo ""
echo "Следующие шаги:"
echo "1. Проверьте доступность сайтов в браузере"
echo "2. Запустите AI сервисы: ./scripts/start-ai-services.sh"
echo "3. Протестируйте интеграцию: ./scripts/test-ai-integration.sh"

echo ""
echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}      НАСТРОЙКА ЗАВЕРШЕНА             ${NC}"
echo -e "${BLUE}=======================================${NC}"