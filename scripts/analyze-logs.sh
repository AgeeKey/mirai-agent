#!/bin/bash

# Mirai Log Analysis Script
# Анализ логов для выявления проблем

set -e

echo "📊 Анализ логов Mirai Ecosystem"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Анализ системных логов
analyze_system_logs() {
    log "🔍 Анализ системных логов..."
    
    local report_file="/root/mirai-agent/reports/log_analysis_$(date +%Y%m%d_%H%M%S).txt"
    
    echo "=== АНАЛИЗ СИСТЕМНЫХ ЛОГОВ ===" > "$report_file"
    echo "Дата анализа: $(date)" >> "$report_file"
    echo "" >> "$report_file"
    
    # Ошибки в системных логах за последний час
    echo "--- СИСТЕМНЫЕ ОШИБКИ (последний час) ---" >> "$report_file"
    journalctl --since "1 hour ago" --priority=err | tail -20 >> "$report_file"
    echo "" >> "$report_file"
    
    # Предупреждения
    echo "--- ПРЕДУПРЕЖДЕНИЯ (последний час) ---" >> "$report_file"
    journalctl --since "1 hour ago" --priority=warning | tail -20 >> "$report_file"
    echo "" >> "$report_file"
    
    log "✅ Системные логи проанализированы"
}

# Анализ логов приложения
analyze_application_logs() {
    log "📱 Анализ логов приложений..."
    
    local report_file="/root/mirai-agent/reports/log_analysis_$(date +%Y%m%d_%H%M%S).txt"
    
    echo "--- ЛОГИ ПРИЛОЖЕНИЙ ---" >> "$report_file"
    
    # Анализ логов API
    if [ -f "/root/mirai-agent/logs/api.log" ]; then
        echo "API Ошибки (последние 24 часа):" >> "$report_file"
        grep -i "error\|exception\|failed" /root/mirai-agent/logs/api.log | tail -10 >> "$report_file"
        echo "" >> "$report_file"
    fi
    
    # Анализ автономных логов
    if [ -f "/root/mirai-agent/logs/autonomous.log" ]; then
        echo "Автономная система - ошибки:" >> "$report_file"
        grep -i "error\|failed" /root/mirai-agent/logs/autonomous.log | tail -10 >> "$report_file"
        echo "" >> "$report_file"
    fi
    
    # Docker логи
    echo "Docker контейнеры с ошибками:" >> "$report_file"
    for container in $(docker ps --format "{{.Names}}"); do
        local errors=$(docker logs "$container" --since="1h" 2>&1 | grep -i "error\|exception\|failed" | wc -l)
        if [ $errors -gt 0 ]; then
            echo "$container: $errors ошибок" >> "$report_file"
            docker logs "$container" --since="1h" 2>&1 | grep -i "error\|exception\|failed" | tail -5 >> "$report_file"
            echo "" >> "$report_file"
        fi
    done
    
    log "✅ Логи приложений проанализированы"
}

# Анализ производительности
analyze_performance() {
    log "⚡ Анализ производительности..."
    
    local report_file="/root/mirai-agent/reports/log_analysis_$(date +%Y%m%d_%H%M%S).txt"
    
    echo "--- АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ ---" >> "$report_file"
    
    # Медленные запросы в nginx
    if [ -f "/var/log/nginx/access.log" ]; then
        echo "Медленные запросы (>2 сек):" >> "$report_file"
        awk '$NF > 2.0 {print $0}' /var/log/nginx/access.log | tail -10 >> "$report_file"
        echo "" >> "$report_file"
    fi
    
    # Использование ресурсов
    echo "Текущее использование ресурсов:" >> "$report_file"
    echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')" >> "$report_file"
    echo "Memory: $(free | awk 'FNR==2{printf "%.1f%%", $3/($3+$4)*100}')" >> "$report_file"
    echo "Disk: $(df / | awk 'NR==2 {print $5}')" >> "$report_file"
    echo "Load: $(uptime | awk -F'load average:' '{print $2}')" >> "$report_file"
    echo "" >> "$report_file"
    
    log "✅ Производительность проанализирована"
}

# Анализ безопасности
analyze_security() {
    log "🔒 Анализ безопасности..."
    
    local report_file="/root/mirai-agent/reports/log_analysis_$(date +%Y%m%d_%H%M%S).txt"
    
    echo "--- АНАЛИЗ БЕЗОПАСНОСТИ ---" >> "$report_file"
    
    # Неудачные попытки входа
    echo "Неудачные попытки SSH (последние 24 часа):" >> "$report_file"
    grep "Failed password" /var/log/auth.log | tail -10 >> "$report_file"
    echo "" >> "$report_file"
    
    # Подозрительная активность
    echo "Подозрительные подключения:" >> "$report_file"
    netstat -tnp | grep ESTABLISHED | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -nr | head -10 >> "$report_file"
    echo "" >> "$report_file"
    
    # Проверка открытых портов
    echo "Открытые порты:" >> "$report_file"
    netstat -tlnp | grep LISTEN >> "$report_file"
    echo "" >> "$report_file"
    
    log "✅ Безопасность проанализирована"
}

# Создание сводки
create_summary() {
    log "📋 Создание сводки анализа..."
    
    local report_file="/root/mirai-agent/reports/log_analysis_$(date +%Y%m%d_%H%M%S).txt"
    local summary_file="/root/mirai-agent/reports/log_summary_$(date +%Y%m%d).json"
    
    # Подсчет различных типов событий
    local system_errors=$(journalctl --since "1 hour ago" --priority=err | wc -l)
    local system_warnings=$(journalctl --since "1 hour ago" --priority=warning | wc -l)
    local failed_logins=$(grep "Failed password" /var/log/auth.log | wc -l)
    local docker_errors=0
    
    for container in $(docker ps --format "{{.Names}}"); do
        local errors=$(docker logs "$container" --since="1h" 2>&1 | grep -i "error\|exception\|failed" | wc -l)
        docker_errors=$((docker_errors + errors))
    done
    
    # Создаем JSON сводку
    cat > "$summary_file" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "analysis_period": "1 hour",
    "summary": {
        "system_errors": $system_errors,
        "system_warnings": $system_warnings,
        "failed_logins": $failed_logins,
        "docker_errors": $docker_errors,
        "total_issues": $((system_errors + system_warnings + failed_logins + docker_errors))
    },
    "recommendations": [
EOF

    # Добавляем рекомендации
    local has_recommendations=false
    
    if [ $system_errors -gt 5 ]; then
        echo '        "Высокое количество системных ошибок - требуется проверка"' >> "$summary_file"
        has_recommendations=true
    fi
    
    if [ $failed_logins -gt 10 ]; then
        if [ "$has_recommendations" = true ]; then
            echo ',' >> "$summary_file"
        fi
        echo '        "Множественные неудачные попытки входа - проверить безопасность"' >> "$summary_file"
        has_recommendations=true
    fi
    
    if [ $docker_errors -gt 0 ]; then
        if [ "$has_recommendations" = true ]; then
            echo ',' >> "$summary_file"
        fi
        echo '        "Ошибки в Docker контейнерах - требуется диагностика"' >> "$summary_file"
        has_recommendations=true
    fi
    
    if [ "$has_recommendations" = false ]; then
        echo '        "Серьезных проблем не обнаружено"' >> "$summary_file"
    fi
    
    echo '    ]' >> "$summary_file"
    echo '}' >> "$summary_file"
    
    echo "" >> "$report_file"
    echo "--- СВОДКА АНАЛИЗА ---" >> "$report_file"
    echo "Системные ошибки: $system_errors" >> "$report_file"
    echo "Предупреждения: $system_warnings" >> "$report_file"
    echo "Неудачные входы: $failed_logins" >> "$report_file"
    echo "Ошибки Docker: $docker_errors" >> "$report_file"
    echo "Всего проблем: $((system_errors + system_warnings + failed_logins + docker_errors))" >> "$report_file"
    
    log "✅ Сводка создана: $summary_file"
    log "📄 Полный отчет: $report_file"
}

# Отправка алертов при критических проблемах
send_alerts() {
    local summary_file="/root/mirai-agent/reports/log_summary_$(date +%Y%m%d).json"
    
    if [ -f "$summary_file" ]; then
        local total_issues=$(cat "$summary_file" | grep -o '"total_issues": [0-9]*' | grep -o '[0-9]*')
        
        if [ $total_issues -gt 20 ]; then
            log "🚨 КРИТИЧЕСКИЙ АЛЕРТ: Обнаружено $total_issues проблем!"
            
            # Отправляем алерт в API (если доступен)
            curl -s -X POST http://localhost:8001/api/alerts \
                -H "Content-Type: application/json" \
                -d "{\"level\": \"critical\", \"message\": \"Обнаружено $total_issues проблем в логах\", \"source\": \"log_analysis\"}" || true
        fi
    fi
}

# Основная функция
main() {
    log "Начинаем анализ логов..."
    
    # Создаем директорию для отчетов если её нет
    mkdir -p /root/mirai-agent/reports
    
    analyze_system_logs
    analyze_application_logs
    analyze_performance
    analyze_security
    create_summary
    send_alerts
    
    log "🎉 Анализ логов завершен!"
}

# Запуск
main