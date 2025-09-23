#!/bin/bash

# Mirai Disk Cleanup Script
# Скрипт очистки диска для автономной системы

set -e

echo "🧹 Очистка диска Mirai Ecosystem"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Проверка места на диске перед очисткой
check_disk_usage() {
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    echo $usage
}

# Очистка логов
cleanup_logs() {
    log "🗂️ Очистка старых логов..."
    
    # Очищаем логи старше 30 дней
    find /root/mirai-agent/logs -name "*.log" -mtime +30 -delete
    find /var/log -name "*.log.*" -mtime +7 -delete
    
    # Очищаем журналы systemd старше 7 дней
    journalctl --vacuum-time=7d
    
    log "✅ Логи очищены"
}

# Очистка Docker
cleanup_docker() {
    log "🐳 Очистка Docker..."
    
    # Удаляем остановленные контейнеры
    docker container prune -f
    
    # Удаляем неиспользуемые образы
    docker image prune -a -f
    
    # Удаляем неиспользуемые volume
    docker volume prune -f
    
    # Удаляем неиспользуемые сети
    docker network prune -f
    
    # Полная очистка системы
    docker system prune -a -f --volumes
    
    log "✅ Docker очищен"
}

# Очистка кешей
cleanup_caches() {
    log "💾 Очистка кешей..."
    
    # APT кеш
    apt-get clean
    apt-get autoremove -y
    
    # NPM кеш
    if command -v npm &> /dev/null; then
        npm cache clean --force
    fi
    
    # Python кеш
    find /root -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find /root -name "*.pyc" -delete 2>/dev/null || true
    
    log "✅ Кеши очищены"
}

# Очистка временных файлов
cleanup_temp() {
    log "🗑️ Очистка временных файлов..."
    
    # Системные временные файлы
    rm -rf /tmp/*
    rm -rf /var/tmp/*
    
    # Старые backup файлы (старше 60 дней)
    find /root/mirai-agent/backups -name "*.tar.gz" -mtime +60 -delete 2>/dev/null || true
    
    log "✅ Временные файлы очищены"
}

# Сжатие логов
compress_logs() {
    log "🗜️ Сжатие больших логов..."
    
    # Сжимаем логи больше 10MB
    find /root/mirai-agent/logs -name "*.log" -size +10M -exec gzip {} \;
    
    log "✅ Логи сжаты"
}

# Основная функция
main() {
    local usage_before=$(check_disk_usage)
    log "Использование диска до очистки: ${usage_before}%"
    
    # Проверяем, нужна ли очистка
    if [ $usage_before -lt 80 ]; then
        log "Диск заполнен менее чем на 80%, очистка не требуется"
        exit 0
    fi
    
    cleanup_logs
    cleanup_docker
    cleanup_caches
    cleanup_temp
    compress_logs
    
    # Освобождаем память
    sync
    echo 3 > /proc/sys/vm/drop_caches
    
    local usage_after=$(check_disk_usage)
    local freed=$((usage_before - usage_after))
    
    log "Использование диска после очистки: ${usage_after}%"
    log "Освобождено: ${freed}%"
    
    if [ $usage_after -gt 90 ]; then
        log "⚠️ ПРЕДУПРЕЖДЕНИЕ: Диск все еще заполнен более чем на 90%"
        log "Рекомендуется ручная проверка и очистка"
    else
        log "✅ Очистка диска завершена успешно"
    fi
}

# Запуск
main