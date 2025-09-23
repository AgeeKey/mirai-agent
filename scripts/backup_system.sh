#!/bin/bash

# Mirai Agent - Система автоматического резервного копирования
# Создает backup БД, конфигураций, логов и других критических данных

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="mirai_backup_$TIMESTAMP"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Создаем директории для backup
create_backup_structure() {
    log "Создание структуры backup..."
    
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$BACKUP_PATH"
    mkdir -p "$BACKUP_PATH/database"
    mkdir -p "$BACKUP_PATH/configs"
    mkdir -p "$BACKUP_PATH/logs"
    mkdir -p "$BACKUP_PATH/state"
    mkdir -p "$BACKUP_PATH/secrets"
    mkdir -p "$BACKUP_PATH/monitoring"
    mkdir -p "$BACKUP_PATH/scripts"
    
    info "Структура backup создана: $BACKUP_PATH"
}

# Backup базы данных
backup_database() {
    log "Backup базы данных..."
    
    DB_PATH="$PROJECT_ROOT/state/mirai.db"
    
    if [ -f "$DB_PATH" ]; then
        cp "$DB_PATH" "$BACKUP_PATH/database/"
        
        # Создаем также SQL dump
        if command -v sqlite3 &> /dev/null; then
            sqlite3 "$DB_PATH" .dump > "$BACKUP_PATH/database/mirai_dump_$TIMESTAMP.sql"
            info "SQL dump создан"
        fi
        
        info "База данных сохранена"
    else
        warn "База данных не найдена: $DB_PATH"
    fi
}

# Backup конфигураций
backup_configs() {
    log "Backup конфигураций..."
    
    # Копируем конфигурационные файлы
    if [ -d "$PROJECT_ROOT/configs" ]; then
        cp -r "$PROJECT_ROOT/configs/"* "$BACKUP_PATH/configs/" 2>/dev/null || true
        info "Конфигурации сохранены"
    fi
    
    # Backup docker-compose файлов
    find "$PROJECT_ROOT" -name "docker-compose*.yml" -exec cp {} "$BACKUP_PATH/configs/" \; 2>/dev/null || true
    
    # Backup pyproject.toml файлов
    find "$PROJECT_ROOT" -name "pyproject.toml" -exec cp {} "$BACKUP_PATH/configs/" \; 2>/dev/null || true
    
    # Backup Dockerfile'ов
    find "$PROJECT_ROOT" -name "Dockerfile*" -exec cp {} "$BACKUP_PATH/configs/" \; 2>/dev/null || true
    
    info "Конфигурационные файлы сохранены"
}

# Backup логов
backup_logs() {
    log "Backup логов..."
    
    if [ -d "$PROJECT_ROOT/logs" ]; then
        # Копируем только важные логи (не старше 7 дней)
        find "$PROJECT_ROOT/logs" -name "*.log" -mtime -7 -exec cp {} "$BACKUP_PATH/logs/" \; 2>/dev/null || true
        
        # Сжимаем старые логи
        find "$PROJECT_ROOT/logs" -name "*.log" -mtime +7 -exec gzip {} \; 2>/dev/null || true
        
        info "Логи сохранены"
    else
        warn "Директория логов не найдена"
    fi
}

# Backup state файлов
backup_state() {
    log "Backup state файлов..."
    
    if [ -d "$PROJECT_ROOT/state" ]; then
        cp -r "$PROJECT_ROOT/state/"* "$BACKUP_PATH/state/" 2>/dev/null || true
        info "State файлы сохранены"
    fi
}

# Backup секретов (без содержимого)
backup_secrets() {
    log "Backup структуры секретов..."
    
    # Создаем список файлов секретов без их содержимого
    if [ -d "$PROJECT_ROOT/secrets" ]; then
        find "$PROJECT_ROOT/secrets" -type f -exec basename {} \; > "$BACKUP_PATH/secrets/secrets_list.txt" 2>/dev/null || true
        info "Список секретов сохранен (без содержимого)"
    fi
    
    # Backup .env.example файлов
    find "$PROJECT_ROOT" -name ".env.example" -exec cp {} "$BACKUP_PATH/secrets/" \; 2>/dev/null || true
}

# Backup мониторинга
backup_monitoring() {
    log "Backup настроек мониторинга..."
    
    if [ -d "$PROJECT_ROOT/monitoring" ]; then
        # Копируем конфигурации мониторинга
        find "$PROJECT_ROOT/monitoring" -name "*.yml" -exec cp {} "$BACKUP_PATH/monitoring/" \; 2>/dev/null || true
        find "$PROJECT_ROOT/monitoring" -name "*.yaml" -exec cp {} "$BACKUP_PATH/monitoring/" \; 2>/dev/null || true
        find "$PROJECT_ROOT/monitoring" -name "*.json" -exec cp {} "$BACKUP_PATH/monitoring/" \; 2>/dev/null || true
        
        info "Настройки мониторинга сохранены"
    fi
}

# Backup скриптов
backup_scripts() {
    log "Backup скриптов..."
    
    # Копируем важные скрипты
    find "$PROJECT_ROOT" -name "*.sh" -exec cp {} "$BACKUP_PATH/scripts/" \; 2>/dev/null || true
    find "$PROJECT_ROOT" -name "manage_services.sh" -exec cp {} "$BACKUP_PATH/scripts/" \; 2>/dev/null || true
    
    # Копируем Python скрипты верхнего уровня
    find "$PROJECT_ROOT" -maxdepth 1 -name "*.py" -exec cp {} "$BACKUP_PATH/scripts/" \; 2>/dev/null || true
    
    info "Скрипты сохранены"
}

# Создание метаданных backup
create_backup_metadata() {
    log "Создание метаданных backup..."
    
    cat > "$BACKUP_PATH/backup_info.json" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$TIMESTAMP",
    "date": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "user": "$(whoami)",
    "project_root": "$PROJECT_ROOT",
    "backup_version": "1.0",
    "components": {
        "database": $([ -f "$BACKUP_PATH/database/mirai.db" ] && echo "true" || echo "false"),
        "configs": $([ -d "$BACKUP_PATH/configs" ] && echo "true" || echo "false"),
        "logs": $([ -d "$BACKUP_PATH/logs" ] && echo "true" || echo "false"),
        "state": $([ -d "$BACKUP_PATH/state" ] && echo "true" || echo "false"),
        "monitoring": $([ -d "$BACKUP_PATH/monitoring" ] && echo "true" || echo "false"),
        "scripts": $([ -d "$BACKUP_PATH/scripts" ] && echo "true" || echo "false")
    },
    "total_size": "$(du -sh "$BACKUP_PATH" | cut -f1)"
}
EOF

    info "Метаданные backup созданы"
}

# Сжатие backup
compress_backup() {
    log "Сжатие backup..."
    
    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
    
    if [ $? -eq 0 ]; then
        rm -rf "$BACKUP_PATH"
        info "Backup сжат: ${BACKUP_NAME}.tar.gz"
        
        # Показываем размер
        SIZE=$(du -sh "${BACKUP_NAME}.tar.gz" | cut -f1)
        info "Размер backup: $SIZE"
    else
        error "Ошибка сжатия backup"
        return 1
    fi
}

# Очистка старых backup'ов
cleanup_old_backups() {
    log "Очистка старых backup'ов..."
    
    # Оставляем только последние 7 backup'ов
    cd "$BACKUP_DIR"
    ls -t mirai_backup_*.tar.gz 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null || true
    
    REMAINING=$(ls -1 mirai_backup_*.tar.gz 2>/dev/null | wc -l)
    info "Оставлено backup'ов: $REMAINING"
}

# Проверка backup'а
verify_backup() {
    log "Проверка backup'а..."
    
    BACKUP_FILE="$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    
    if [ -f "$BACKUP_FILE" ]; then
        # Проверяем целостность архива
        if tar -tzf "$BACKUP_FILE" >/dev/null 2>&1; then
            info "✅ Backup прошел проверку целостности"
            return 0
        else
            error "❌ Backup поврежден!"
            return 1
        fi
    else
        error "❌ Backup файл не найден!"
        return 1
    fi
}

# Отправка уведомления о backup
send_backup_notification() {
    local status=$1
    local message=$2
    
    # Пытаемся отправить уведомление через Alert API
    if curl -s --max-time 5 "http://localhost:9998/alerts/health" >/dev/null 2>&1; then
        local level="info"
        if [ "$status" != "success" ]; then
            level="warning"
        fi
        
        curl -s -X POST "http://localhost:9998/alerts/manual" \
            -H "Content-Type: application/json" \
            -d "{
                \"title\": \"💾 Backup System\",
                \"message\": \"$message\",
                \"level\": \"$level\",
                \"alert_type\": \"system\"
            }" >/dev/null 2>&1 || true
    fi
}

# Главная функция
main() {
    echo "💾 Mirai Agent - Система резервного копирования"
    echo "=============================================="
    
    log "Начало процедуры backup..."
    
    # Выполняем backup
    create_backup_structure
    backup_database
    backup_configs
    backup_logs
    backup_state
    backup_secrets
    backup_monitoring
    backup_scripts
    create_backup_metadata
    
    # Сжимаем и проверяем
    if compress_backup && verify_backup; then
        cleanup_old_backups
        
        SIZE=$(du -sh "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)
        SUCCESS_MSG="Backup успешно создан: ${BACKUP_NAME}.tar.gz (размер: $SIZE)"
        
        log "✅ $SUCCESS_MSG"
        send_backup_notification "success" "$SUCCESS_MSG"
        
        echo ""
        echo "📁 Backup сохранен в: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
        echo "📊 Размер: $SIZE"
        echo "🕒 Время создания: $(date)"
        
        return 0
    else
        ERROR_MSG="Ошибка создания backup'а"
        error "❌ $ERROR_MSG"
        send_backup_notification "error" "$ERROR_MSG"
        return 1
    fi
}

# Восстановление из backup
restore_backup() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        echo "Использование: $0 restore <backup_file.tar.gz>"
        return 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        error "Backup файл не найден: $backup_file"
        return 1
    fi
    
    log "Восстановление из backup: $backup_file"
    
    # Создаем временную директорию
    TEMP_DIR=$(mktemp -d)
    
    # Распаковываем backup
    tar -xzf "$backup_file" -C "$TEMP_DIR"
    
    BACKUP_CONTENT=$(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d)
    
    if [ -z "$BACKUP_CONTENT" ]; then
        error "Некорректный backup файл"
        rm -rf "$TEMP_DIR"
        return 1
    fi
    
    BACKUP_CONTENT=$(basename "$BACKUP_CONTENT")
    
    log "Восстановление компонентов..."
    
    # Восстановляем базу данных
    if [ -f "$TEMP_DIR/$BACKUP_CONTENT/database/mirai.db" ]; then
        cp "$TEMP_DIR/$BACKUP_CONTENT/database/mirai.db" "$PROJECT_ROOT/state/"
        info "База данных восстановлена"
    fi
    
    # Восстановляем конфигурации
    if [ -d "$TEMP_DIR/$BACKUP_CONTENT/configs" ]; then
        mkdir -p "$PROJECT_ROOT/configs"
        cp -r "$TEMP_DIR/$BACKUP_CONTENT/configs/"* "$PROJECT_ROOT/configs/" 2>/dev/null || true
        info "Конфигурации восстановлены"
    fi
    
    # Восстановляем state
    if [ -d "$TEMP_DIR/$BACKUP_CONTENT/state" ]; then
        mkdir -p "$PROJECT_ROOT/state"
        cp -r "$TEMP_DIR/$BACKUP_CONTENT/state/"* "$PROJECT_ROOT/state/" 2>/dev/null || true
        info "State файлы восстановлены"
    fi
    
    # Очищаем временную директорию
    rm -rf "$TEMP_DIR"
    
    log "✅ Восстановление завершено"
    send_backup_notification "success" "Система восстановлена из backup: $(basename "$backup_file")"
}

# Список доступных backup'ов
list_backups() {
    echo "📋 Доступные backup'ы:"
    echo "======================"
    
    if [ -d "$BACKUP_DIR" ]; then
        ls -lah "$BACKUP_DIR"/mirai_backup_*.tar.gz 2>/dev/null | while read line; do
            echo "$line"
        done
    else
        echo "Backup'ы не найдены"
    fi
}

# Обработка аргументов
case "${1:-backup}" in
    "backup")
        main
        ;;
    "restore")
        restore_backup "$2"
        ;;
    "list")
        list_backups
        ;;
    "help"|"--help"|"-h")
        echo "Использование: $0 [backup|restore|list|help]"
        echo ""
        echo "Команды:"
        echo "  backup          - Создать backup (по умолчанию)"
        echo "  restore <file>  - Восстановить из backup файла"
        echo "  list           - Показать доступные backup'ы"
        echo "  help           - Показать эту справку"
        ;;
    *)
        error "Неизвестная команда: $1"
        echo "Используйте '$0 help' для справки"
        exit 1
        ;;
esac