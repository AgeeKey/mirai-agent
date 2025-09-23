#!/bin/bash

# Mirai Security Hardening Script
# Настройка безопасности для production

set -e

echo "🔐 Настройка безопасности Mirai Ecosystem"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Настройка файрвола
setup_firewall() {
    log "🔥 Настройка UFW файрвола..."
    
    # Устанавливаем UFW если не установлен
    apt-get update && apt-get install -y ufw
    
    # Сбрасываем правила
    ufw --force reset
    
    # Базовые правила
    ufw default deny incoming
    ufw default allow outgoing
    
    # SSH
    ufw allow 22/tcp
    
    # HTTP/HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Разработка (временно)
    ufw allow 3001/tcp
    ufw allow 8001/tcp
    ufw allow 8002/tcp
    
    # Включаем файрвол
    ufw --force enable
    
    log "✅ UFW настроен"
}

# Настройка fail2ban
setup_fail2ban() {
    log "🛡️ Настройка Fail2Ban..."
    
    apt-get install -y fail2ban
    
    # Создаем конфигурацию
    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-noscript]
enabled = true
port = http,https
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6

[nginx-badbots]
enabled = true
port = http,https
filter = nginx-badbots
logpath = /var/log/nginx/access.log
maxretry = 2
EOF

    systemctl enable fail2ban
    systemctl restart fail2ban
    
    log "✅ Fail2Ban настроен"
}

# Настройка SSL
setup_ssl() {
    log "🔒 Подготовка SSL сертификатов..."
    
    # Устанавливаем certbot
    apt-get install -y certbot python3-certbot-nginx
    
    # Создаем скрипт для получения сертификатов
    cat > /root/mirai-agent/scripts/setup-ssl.sh << 'EOF'
#!/bin/bash

echo "Настройка SSL сертификатов для доменов"

# Останавливаем nginx на время получения сертификатов
docker stop mirai-nginx-ecosystem 2>/dev/null || true

# Получаем сертификаты
certbot certonly --standalone -d aimirai.online --non-interactive --agree-tos --email admin@aimirai.online
certbot certonly --standalone -d aimirai.info --non-interactive --agree-tos --email admin@aimirai.info

# Создаем новую nginx конфигурацию с SSL
cat > /root/mirai-agent/deployment/nginx-ssl.conf << 'NGINXEOF'
events {
    worker_connections 1024;
}

http {
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=general:10m rate=30r/s;

    # aimirai.online - Trading Platform
    server {
        listen 80;
        server_name aimirai.online;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name aimirai.online;

        ssl_certificate /etc/letsencrypt/live/aimirai.online/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/aimirai.online/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # API routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://127.0.0.1:8001;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Frontend
        location / {
            limit_req zone=general burst=50 nodelay;
            proxy_pass http://127.0.0.1:3001;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }

    # aimirai.info - Services Platform
    server {
        listen 80;
        server_name aimirai.info;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name aimirai.info;

        ssl_certificate /etc/letsencrypt/live/aimirai.info/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/aimirai.info/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # API routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://127.0.0.1:8002;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Frontend (будет добавлен позже)
        location / {
            limit_req zone=general burst=50 nodelay;
            proxy_pass http://127.0.0.1:8002;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
NGINXEOF

# Перезапускаем nginx с SSL
docker run -d --name mirai-nginx-ssl \
    --network host \
    -v /root/mirai-agent/deployment/nginx-ssl.conf:/etc/nginx/nginx.conf:ro \
    -v /etc/letsencrypt:/etc/letsencrypt:ro \
    nginx:alpine

echo "✅ SSL сертификаты настроены"
EOF

    chmod +x /root/mirai-agent/scripts/setup-ssl.sh
    
    log "✅ SSL скрипт подготовлен (запустите /root/mirai-agent/scripts/setup-ssl.sh)"
}

# Настройка секретов
setup_secrets() {
    log "🔑 Настройка секретов..."
    
    # Создаем директорию для секретов
    mkdir -p /root/mirai-agent/secrets
    chmod 700 /root/mirai-agent/secrets
    
    # Генерируем случайные пароли
    generate_password() {
        openssl rand -base64 32
    }
    
    # Создаем файл с секретами
    cat > /root/mirai-agent/secrets/production.env << EOF
# Database
POSTGRES_PASSWORD=$(generate_password)
REDIS_PASSWORD=$(generate_password)

# JWT
JWT_SECRET=$(generate_password)
JWT_ALGORITHM=HS256

# API Keys
API_SECRET_KEY=$(generate_password)

# Encryption
ENCRYPTION_KEY=$(generate_password)

# Admin
ADMIN_PASSWORD=$(generate_password)
EOF

    chmod 600 /root/mirai-agent/secrets/production.env
    
    log "✅ Секреты созданы в /root/mirai-agent/secrets/production.env"
}

# Настройка backup
setup_backup() {
    log "💾 Настройка системы резервного копирования..."
    
    mkdir -p /root/mirai-agent/backups
    
    # Создаем скрипт backup
    cat > /root/mirai-agent/scripts/backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/root/mirai-agent/backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "Создание резервной копии - $DATE"

# Создаем директорию для backup
mkdir -p "$BACKUP_DIR/$DATE"

# Backup базы данных
docker exec mirai-postgres pg_dump -U mirai mirai_production > "$BACKUP_DIR/$DATE/database.sql"

# Backup данных приложения
cp -r /root/mirai-agent/deployment/data "$BACKUP_DIR/$DATE/"

# Backup конфигураций
cp -r /root/mirai-agent/deployment/*.conf "$BACKUP_DIR/$DATE/"
cp -r /root/mirai-agent/secrets "$BACKUP_DIR/$DATE/"

# Создаем архив
tar -czf "$BACKUP_DIR/mirai_backup_$DATE.tar.gz" -C "$BACKUP_DIR" "$DATE"
rm -rf "$BACKUP_DIR/$DATE"

# Удаляем старые backup (старше 30 дней)
find "$BACKUP_DIR" -name "mirai_backup_*.tar.gz" -mtime +30 -delete

echo "✅ Backup создан: mirai_backup_$DATE.tar.gz"
EOF

    chmod +x /root/mirai-agent/scripts/backup.sh
    
    # Добавляем в cron (ежедневно в 02:00)
    (crontab -l 2>/dev/null; echo "0 2 * * * /root/mirai-agent/scripts/backup.sh >> /root/mirai-agent/deployment/logs/backup.log 2>&1") | crontab -
    
    log "✅ Система backup настроена (ежедневно в 02:00)"
}

# Настройка логирования
setup_logging() {
    log "📝 Настройка централизованного логирования..."
    
    mkdir -p /root/mirai-agent/deployment/logs
    
    # Создаем конфигурацию rsyslog для централизованного логирования
    cat > /etc/rsyslog.d/50-mirai.conf << 'EOF'
# Mirai Ecosystem Logging
$template MiraiFormat,"%TIMESTAMP% %HOSTNAME% %syslogtag%%msg%\n"
:programname, isequal, "mirai" /root/mirai-agent/deployment/logs/mirai.log;MiraiFormat
& stop
EOF

    systemctl restart rsyslog
    
    # Настраиваем ротацию логов
    cat > /etc/logrotate.d/mirai << 'EOF'
/root/mirai-agent/deployment/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload rsyslog
    endscript
}
EOF

    log "✅ Логирование настроено"
}

# Основная функция
main() {
    log "Начинаем настройку безопасности..."
    
    setup_firewall
    setup_fail2ban
    setup_ssl
    setup_secrets
    setup_backup
    setup_logging
    
    log "🎉 Настройка безопасности завершена!"
    log ""
    log "Следующие шаги:"
    log "1. Запустите /root/mirai-agent/scripts/setup-ssl.sh для настройки SSL"
    log "2. Обновите DNS записи для доменов"
    log "3. Проверьте секреты в /root/mirai-agent/secrets/production.env"
    log "4. Настройте мониторинг и алерты"
}

# Запуск
main