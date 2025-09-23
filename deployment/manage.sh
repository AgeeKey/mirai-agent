#!/bin/bash

# Mirai Agent Deployment Management Script
# Manage production deployment for aimirai.online and aimirai.info

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.production.yml"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[WARNING] $1${NC}"; }
error() { echo -e "${RED}[ERROR] $1${NC}" >&2; }
info() { echo -e "${BLUE}[INFO] $1${NC}"; }

# Show usage
usage() {
    echo "Mirai Agent Deployment Manager"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  start           Start all services"
    echo "  stop            Stop all services"
    echo "  restart         Restart all services"
    echo "  status          Show services status"
    echo "  logs [service]  Show logs (optionally for specific service)"
    echo "  update          Update and restart services"
    echo "  backup          Create backup of data and state"
    echo "  restore <path>  Restore from backup"
    echo "  health          Check health of all services"
    echo "  scale <service> <count>  Scale a service to N replicas"
    echo "  ssl-renew       Renew SSL certificates"
    echo "  cleanup         Clean up unused Docker resources"
    echo
    echo "Service names:"
    echo "  - nginx"
    echo "  - mirai-api-trading"
    echo "  - mirai-api-services"
    echo "  - mirai-dashboard-trading"
    echo "  - mirai-dashboard-services"
    echo "  - postgres"
    echo "  - redis"
    echo "  - prometheus"
    echo "  - grafana"
    echo
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs nginx"
    echo "  $0 scale mirai-api-trading 3"
    echo "  $0 backup"
}

# Check if docker-compose file exists
check_compose_file() {
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Docker Compose file not found: $COMPOSE_FILE"
        error "Please run setup first"
        exit 1
    fi
}

# Load environment
load_environment() {
    if [[ -f "$PROJECT_ROOT/.env.production" ]]; then
        set -a
        source "$PROJECT_ROOT/.env.production"
        set +a
    else
        warn "Production environment file not found"
        warn "Some operations may not work correctly"
    fi
}

# Start services
start_services() {
    log "Starting Mirai Agent services..."
    check_compose_file
    
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log "✅ Services started"
    log "Access points:"
    log "  - Trading Platform: https://aimirai.online"
    log "  - Services Platform: https://aimirai.info"
}

# Stop services
stop_services() {
    log "Stopping Mirai Agent services..."
    check_compose_file
    
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" down
    
    log "✅ Services stopped"
}

# Restart services
restart_services() {
    log "Restarting Mirai Agent services..."
    stop_services
    sleep 5
    start_services
}

# Show status
show_status() {
    log "Mirai Agent Services Status:"
    check_compose_file
    
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo
    info "Service Health:"
    
    # Check key endpoints
    endpoints=(
        "https://aimirai.online/health:Trading Platform"
        "https://aimirai.info/status:Services Platform"
    )
    
    for endpoint in "${endpoints[@]}"; do
        url=$(echo "$endpoint" | cut -d: -f1)
        name=$(echo "$endpoint" | cut -d: -f2)
        
        if curl -f -s "$url" > /dev/null 2>&1; then
            echo -e "  ✅ $name: ${GREEN}Healthy${NC}"
        else
            echo -e "  ❌ $name: ${RED}Unhealthy${NC}"
        fi
    done
}

# Show logs
show_logs() {
    check_compose_file
    
    if [[ -n "${1:-}" ]]; then
        log "Showing logs for service: $1"
        cd "$PROJECT_ROOT"
        docker-compose -f "$COMPOSE_FILE" logs -f "$1"
    else
        log "Showing logs for all services..."
        cd "$PROJECT_ROOT"
        docker-compose -f "$COMPOSE_FILE" logs -f
    fi
}

# Update services
update_services() {
    log "Updating Mirai Agent services..."
    check_compose_file
    
    cd "$PROJECT_ROOT"
    
    # Pull latest images
    info "Pulling latest images..."
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Rebuild custom images
    info "Rebuilding custom images..."
    docker build -t mirai-agent:latest -f Dockerfile .
    docker build -t mirai-api:latest -f app/api/Dockerfile ./app/api
    docker build -t mirai-dashboard:latest -f web/services/Dockerfile ./web/services
    docker build -t mirai-microservices:latest -f microservices/Dockerfile ./microservices
    
    # Restart services
    info "Restarting services with new images..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log "✅ Services updated"
}

# Create backup
create_backup() {
    log "Creating backup..."
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_dir="$SCRIPT_DIR/backup/$timestamp"
    mkdir -p "$backup_dir"
    
    # Backup database
    info "Backing up database..."
    docker exec mirai-postgres pg_dumpall -U mirai_admin > "$backup_dir/database.sql"
    
    # Backup application state
    info "Backing up application state..."
    if [[ -d "$SCRIPT_DIR/data/state" ]]; then
        cp -r "$SCRIPT_DIR/data/state" "$backup_dir/"
    fi
    
    # Backup logs
    info "Backing up logs..."
    if [[ -d "$SCRIPT_DIR/logs" ]]; then
        tar -czf "$backup_dir/logs.tar.gz" -C "$SCRIPT_DIR" logs/
    fi
    
    # Create backup info
    cat > "$backup_dir/backup_info.txt" << EOF
Mirai Agent Backup
Created: $(date)
Version: $(git rev-parse HEAD 2>/dev/null || echo "unknown")
Services: $(docker-compose -f "$COMPOSE_FILE" ps --services | tr '\n' ' ')
EOF
    
    log "✅ Backup created: $backup_dir"
}

# Restore from backup
restore_backup() {
    local backup_path="${1:-}"
    
    if [[ -z "$backup_path" ]]; then
        error "Backup path required"
        echo "Usage: $0 restore <backup_path>"
        exit 1
    fi
    
    if [[ ! -d "$backup_path" ]]; then
        error "Backup directory not found: $backup_path"
        exit 1
    fi
    
    log "Restoring from backup: $backup_path"
    
    # Stop services
    warn "Stopping services for restore..."
    stop_services
    
    # Restore database
    if [[ -f "$backup_path/database.sql" ]]; then
        info "Restoring database..."
        docker-compose -f "$COMPOSE_FILE" up -d postgres
        sleep 10
        docker exec -i mirai-postgres psql -U mirai_admin < "$backup_path/database.sql"
    fi
    
    # Restore state
    if [[ -d "$backup_path/state" ]]; then
        info "Restoring application state..."
        rm -rf "$SCRIPT_DIR/data/state"
        cp -r "$backup_path/state" "$SCRIPT_DIR/data/"
    fi
    
    # Start services
    start_services
    
    log "✅ Restore completed"
}

# Health check
health_check() {
    log "Performing comprehensive health check..."
    
    # Check Docker services
    info "Checking Docker services..."
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" ps
    
    # Check endpoints
    info "Checking service endpoints..."
    endpoints=(
        "https://aimirai.online/health"
        "https://aimirai.info/status"
        "https://aimirai.online/api/healthz"
        "https://aimirai.info/api/healthz"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f -s "$endpoint" > /dev/null; then
            echo "✅ $endpoint"
        else
            echo "❌ $endpoint"
        fi
    done
    
    # Check SSL certificates
    info "Checking SSL certificates..."
    for domain in "aimirai.online" "aimirai.info"; do
        exp_date=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | \
                   openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
        if [[ -n "$exp_date" ]]; then
            echo "✅ $domain SSL expires: $exp_date"
        else
            echo "❌ $domain SSL check failed"
        fi
    done
    
    log "✅ Health check completed"
}

# Scale service
scale_service() {
    local service="${1:-}"
    local count="${2:-}"
    
    if [[ -z "$service" ]] || [[ -z "$count" ]]; then
        error "Service name and replica count required"
        echo "Usage: $0 scale <service> <count>"
        exit 1
    fi
    
    log "Scaling $service to $count replicas..."
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" up -d --scale "$service=$count"
    
    log "✅ Service scaled"
}

# Renew SSL certificates
renew_ssl() {
    log "Renewing SSL certificates..."
    
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" exec certbot certbot renew
    docker-compose -f "$COMPOSE_FILE" restart nginx
    
    log "✅ SSL certificates renewed"
}

# Cleanup unused resources
cleanup() {
    log "Cleaning up unused Docker resources..."
    
    # Remove unused containers
    docker container prune -f
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    warn "This will remove unused Docker volumes. Continue? (y/N)"
    read -p "" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume prune -f
    fi
    
    # Remove unused networks
    docker network prune -f
    
    log "✅ Cleanup completed"
}

# Main function
main() {
    local command="${1:-}"
    
    if [[ -z "$command" ]]; then
        usage
        exit 1
    fi
    
    load_environment
    
    case "$command" in
        "start")
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "${2:-}"
            ;;
        "update")
            update_services
            ;;
        "backup")
            create_backup
            ;;
        "restore")
            restore_backup "${2:-}"
            ;;
        "health")
            health_check
            ;;
        "scale")
            scale_service "${2:-}" "${3:-}"
            ;;
        "ssl-renew")
            renew_ssl
            ;;
        "cleanup")
            cleanup
            ;;
        *)
            error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi