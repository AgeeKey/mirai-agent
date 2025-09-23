#!/bin/bash

# Mirai Agent - Настройка автоматических backup'ов
# Создает cron задачи для регулярного резервного копирования

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_SCRIPT="$PROJECT_ROOT/scripts/backup_system.sh"

echo "⚙️  Настройка автоматических backup'ов Mirai Agent"
echo "================================================="

# Проверяем существование backup скрипта
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "❌ Backup скрипт не найден: $BACKUP_SCRIPT"
    exit 1
fi

# Делаем скрипт исполняемым
chmod +x "$BACKUP_SCRIPT"

echo "📅 Настройка расписания backup'ов:"
echo "  - Ежедневно в 03:00 (полный backup)"
echo "  - Каждые 6 часов (быстрый backup конфигураций)"
echo ""

# Создаем временный crontab файл
TEMP_CRON=$(mktemp)

# Получаем текущий crontab (если есть)
crontab -l 2>/dev/null > "$TEMP_CRON" || touch "$TEMP_CRON"

# Удаляем старые записи Mirai backup (если есть)
grep -v "mirai.*backup" "$TEMP_CRON" > "${TEMP_CRON}.clean" || true
mv "${TEMP_CRON}.clean" "$TEMP_CRON"

# Добавляем новые cron задачи
cat >> "$TEMP_CRON" << EOF

# Mirai Agent - Автоматические backup'ы
# Ежедневный полный backup в 03:00
0 3 * * * $BACKUP_SCRIPT backup >> $PROJECT_ROOT/logs/backup.log 2>&1

# Быстрый backup конфигураций каждые 6 часов
0 */6 * * * $PROJECT_ROOT/scripts/quick_backup.sh >> $PROJECT_ROOT/logs/backup.log 2>&1

EOF

# Применяем новый crontab
crontab "$TEMP_CRON"

if [ $? -eq 0 ]; then
    echo "✅ Cron задачи успешно настроены"
    echo ""
    echo "📋 Текущее расписание:"
    crontab -l | grep -A 10 "Mirai Agent"
else
    echo "❌ Ошибка настройки cron задач"
    rm -f "$TEMP_CRON"
    exit 1
fi

# Очищаем временные файлы
rm -f "$TEMP_CRON"

# Создаем быстрый backup скрипт
cat > "$PROJECT_ROOT/scripts/quick_backup.sh" << 'EOF'
#!/bin/bash

# Mirai Agent - Быстрый backup критических компонентов
# Создает backup только важных конфигураций и состояния

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups/quick"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Создаем директорию для быстрых backup'ов
mkdir -p "$BACKUP_DIR"

# Копируем только критические файлы
cp "$PROJECT_ROOT/state/mirai.db" "$BACKUP_DIR/mirai_db_$TIMESTAMP.db" 2>/dev/null || true
cp -r "$PROJECT_ROOT/configs" "$BACKUP_DIR/configs_$TIMESTAMP" 2>/dev/null || true

# Оставляем только последние 24 быстрых backup'а
find "$BACKUP_DIR" -name "*_$TIMESTAMP*" -mtime +1 -delete 2>/dev/null || true

echo "[$(date)] Quick backup completed: $TIMESTAMP"
EOF

chmod +x "$PROJECT_ROOT/scripts/quick_backup.sh"

# Создаем директории для логов
mkdir -p "$PROJECT_ROOT/logs"

echo ""
echo "📁 Созданы дополнительные компоненты:"
echo "  - $PROJECT_ROOT/scripts/quick_backup.sh (быстрый backup)"
echo "  - $PROJECT_ROOT/logs/backup.log (логи backup'ов)"
echo ""

# Проверяем статус cron демона
if systemctl is-active --quiet cron 2>/dev/null || systemctl is-active --quiet crond 2>/dev/null; then
    echo "✅ Cron демон активен"
else
    echo "⚠️  Cron демон не активен. Запустите его:"
    echo "   sudo systemctl start cron"
    echo "   sudo systemctl enable cron"
fi

echo ""
echo "🎯 Настройка завершена!"
echo ""
echo "Команды для управления backup'ами:"
echo "  $BACKUP_SCRIPT backup           # Создать backup сейчас"
echo "  $BACKUP_SCRIPT list             # Показать backup'ы"
echo "  $BACKUP_SCRIPT restore <file>   # Восстановить из backup"
echo ""
echo "Логи backup'ов: $PROJECT_ROOT/logs/backup.log"