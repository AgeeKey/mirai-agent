#!/bin/bash

# Blue-Green Deployment Script for Mirai Trading System
# Usage: ./blue-green-deploy.sh <environment> <version> [service]

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse arguments
ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
SERVICE=${3:-all}

# Validate arguments
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    error "Environment must be 'staging' or 'production'"
    exit 1
fi

# Configuration based on environment
case $ENVIRONMENT in
    staging)
        NAMESPACE="mirai-staging"
        CLUSTER_NAME="mirai-staging"
        DOMAIN="mirai-staging.example.com"
        ;;
    production)
        NAMESPACE="mirai-production"
        CLUSTER_NAME="mirai-production"
        DOMAIN="mirai.example.com"
        ;;
esac

# Registry configuration
REGISTRY="ghcr.io"
IMAGE_BASE="${REGISTRY}/mirai-agent"

# Services to deploy
if [[ "$SERVICE" == "all" ]]; then
    SERVICES=("api" "trader" "web" "telegram-bot")
else
    SERVICES=("$SERVICE")
fi

log "Starting blue-green deployment"
log "Environment: $ENVIRONMENT"
log "Version: $VERSION"
log "Services: ${SERVICES[*]}"
log "Namespace: $NAMESPACE"

# Pre-deployment checks
log "Running pre-deployment checks..."

# Check kubectl connectivity
if ! kubectl cluster-info > /dev/null 2>&1; then
    error "Cannot connect to Kubernetes cluster"
    exit 1
fi

# Check namespace exists
if ! kubectl get namespace "$NAMESPACE" > /dev/null 2>&1; then
    warning "Namespace $NAMESPACE does not exist, creating..."
    kubectl create namespace "$NAMESPACE"
fi

# Check if images exist
log "Verifying container images..."
for service in "${SERVICES[@]}"; do
    image="${IMAGE_BASE}-${service}:${VERSION}"
    log "Checking image: $image"
    
    if ! docker manifest inspect "$image" > /dev/null 2>&1; then
        error "Image not found: $image"
        exit 1
    fi
done

success "Pre-deployment checks passed"

# Function to wait for deployment rollout
wait_for_rollout() {
    local deployment=$1
    local timeout=${2:-300}
    
    log "Waiting for rollout of $deployment (timeout: ${timeout}s)..."
    
    if kubectl rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout="${timeout}s"; then
        success "Rollout completed for $deployment"
        return 0
    else
        error "Rollout failed for $deployment"
        return 1
    fi
}

# Function to perform health check
health_check() {
    local service=$1
    local max_attempts=${2:-10}
    local attempt=1
    
    log "Performing health check for $service..."
    
    while [[ $attempt -le $max_attempts ]]; do
        case $service in
            api)
                if curl -f -s "https://$DOMAIN/api/health" > /dev/null; then
                    success "Health check passed for $service"
                    return 0
                fi
                ;;
            web)
                if curl -f -s "https://$DOMAIN/health" > /dev/null; then
                    success "Health check passed for $service"
                    return 0
                fi
                ;;
            *)
                # For services without external endpoints, check pod status
                if kubectl get pods -n "$NAMESPACE" -l "app=mirai-${service}" | grep -q "Running"; then
                    success "Health check passed for $service"
                    return 0
                fi
                ;;
        esac
        
        log "Health check attempt $attempt/$max_attempts failed, retrying in 10s..."
        sleep 10
        ((attempt++))
    done
    
    error "Health check failed for $service after $max_attempts attempts"
    return 1
}

# Function to create backup of current deployment
create_backup() {
    local service=$1
    local timestamp=$(date +%Y%m%d-%H%M%S)
    local backup_name="mirai-${service}-backup-${timestamp}"
    
    log "Creating backup for $service..."
    
    # Export current deployment
    kubectl get deployment "mirai-${service}" -n "$NAMESPACE" -o yaml > "/tmp/${backup_name}.yaml" 2>/dev/null || {
        warning "No existing deployment found for $service"
        return 0
    }
    
    # Create configmap with backup
    kubectl create configmap "$backup_name" \
        --from-file="/tmp/${backup_name}.yaml" \
        -n "$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    success "Backup created: $backup_name"
}

# Function to deploy green version
deploy_green() {
    local service=$1
    local green_name="mirai-${service}-green"
    
    log "Deploying green version for $service..."
    
    # Create green deployment manifest
    cat > "/tmp/${green_name}.yaml" << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${green_name}
  namespace: ${NAMESPACE}
  labels:
    app: mirai-${service}
    version: green
    deployment-version: ${VERSION}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mirai-${service}
      version: green
  template:
    metadata:
      labels:
        app: mirai-${service}
        version: green
    spec:
      containers:
      - name: mirai-${service}
        image: ${IMAGE_BASE}-${service}:${VERSION}
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: ${ENVIRONMENT}
        - name: VERSION
          value: ${VERSION}
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
EOF

    # Apply green deployment
    kubectl apply -f "/tmp/${green_name}.yaml"
    
    # Wait for green deployment to be ready
    if ! wait_for_rollout "$green_name" 600; then
        error "Failed to deploy green version for $service"
        return 1
    fi
    
    # Perform health check on green deployment
    sleep 30 # Give services time to fully start
    
    success "Green deployment ready for $service"
}

# Function to switch traffic to green
switch_to_green() {
    local service=$1
    
    log "Switching traffic to green for $service..."
    
    # Update service selector to point to green
    kubectl patch service "mirai-${service}" -n "$NAMESPACE" \
        -p '{"spec":{"selector":{"version":"green"}}}' || {
        warning "Service mirai-${service} does not exist, creating..."
        
        # Create service if it doesn't exist
        cat > "/tmp/service-${service}.yaml" << EOF
apiVersion: v1
kind: Service
metadata:
  name: mirai-${service}
  namespace: ${NAMESPACE}
spec:
  selector:
    app: mirai-${service}
    version: green
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
EOF
        kubectl apply -f "/tmp/service-${service}.yaml"
    }
    
    success "Traffic switched to green for $service"
}

# Function to cleanup blue deployment
cleanup_blue() {
    local service=$1
    local blue_name="mirai-${service}-blue"
    
    log "Cleaning up blue deployment for $service..."
    
    # Delete blue deployment if it exists
    kubectl delete deployment "$blue_name" -n "$NAMESPACE" --ignore-not-found=true
    
    # Rename green to blue for next deployment
    kubectl patch deployment "mirai-${service}-green" -n "$NAMESPACE" \
        -p '{"metadata":{"name":"mirai-'${service}'"}}' || {
        warning "Failed to rename green deployment for $service"
    }
    
    success "Blue deployment cleaned up for $service"
}

# Function to rollback to blue
rollback_to_blue() {
    local service=$1
    local blue_name="mirai-${service}-blue"
    
    error "Rolling back to blue for $service..."
    
    # Switch service back to blue
    kubectl patch service "mirai-${service}" -n "$NAMESPACE" \
        -p '{"spec":{"selector":{"version":"blue"}}}'
    
    # Delete failed green deployment
    kubectl delete deployment "mirai-${service}-green" -n "$NAMESPACE" --ignore-not-found=true
    
    warning "Rollback completed for $service"
}

# Main deployment logic
log "Starting blue-green deployment process..."

# Track deployment status
DEPLOYMENT_SUCCESS=true
DEPLOYED_SERVICES=()
FAILED_SERVICES=()

for service in "${SERVICES[@]}"; do
    log "Processing service: $service"
    
    # Create backup of current deployment
    create_backup "$service"
    
    # Deploy green version
    if deploy_green "$service"; then
        # Test green deployment
        if health_check "$service" 15; then
            # Switch traffic to green
            switch_to_green "$service"
            
            # Final health check after traffic switch
            sleep 15
            if health_check "$service" 10; then
                # Cleanup blue deployment
                cleanup_blue "$service"
                DEPLOYED_SERVICES+=("$service")
                success "Blue-green deployment completed for $service"
            else
                error "Post-switch health check failed for $service"
                rollback_to_blue "$service"
                FAILED_SERVICES+=("$service")
                DEPLOYMENT_SUCCESS=false
            fi
        else
            error "Green deployment health check failed for $service"
            rollback_to_blue "$service"
            FAILED_SERVICES+=("$service")
            DEPLOYMENT_SUCCESS=false
        fi
    else
        error "Failed to deploy green version for $service"
        FAILED_SERVICES+=("$service")
        DEPLOYMENT_SUCCESS=false
    fi
done

# Final status report
log "Deployment Summary:"
log "Environment: $ENVIRONMENT"
log "Version: $VERSION"

if [[ ${#DEPLOYED_SERVICES[@]} -gt 0 ]]; then
    success "Successfully deployed: ${DEPLOYED_SERVICES[*]}"
fi

if [[ ${#FAILED_SERVICES[@]} -gt 0 ]]; then
    error "Failed to deploy: ${FAILED_SERVICES[*]}"
fi

# Post-deployment verification
if $DEPLOYMENT_SUCCESS; then
    log "Running post-deployment verification..."
    
    # Extended health checks
    sleep 30
    
    # Check main application endpoints
    if health_check "api" 5 && health_check "web" 5; then
        success "Post-deployment verification passed"
        
        # Update deployment annotation
        for service in "${DEPLOYED_SERVICES[@]}"; do
            kubectl annotate deployment "mirai-${service}" -n "$NAMESPACE" \
                deployment.kubernetes.io/revision="$(date +%s)" \
                deployment.mirai.io/version="$VERSION" \
                deployment.mirai.io/deployed-at="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
                --overwrite
        done
        
        success "🎉 Blue-green deployment completed successfully!"
        
        # Send success notification (if webhook configured)
        if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
            curl -X POST "$SLACK_WEBHOOK_URL" \
                -H "Content-Type: application/json" \
                -d "{
                    \"text\": \"✅ Mirai deployment successful\",
                    \"attachments\": [{
                        \"color\": \"good\",
                        \"fields\": [
                            {\"title\": \"Environment\", \"value\": \"$ENVIRONMENT\", \"short\": true},
                            {\"title\": \"Version\", \"value\": \"$VERSION\", \"short\": true},
                            {\"title\": \"Services\", \"value\": \"${DEPLOYED_SERVICES[*]}\", \"short\": false}
                        ]
                    }]
                }" 2>/dev/null || true
        fi
        
        exit 0
    else
        error "Post-deployment verification failed"
        DEPLOYMENT_SUCCESS=false
    fi
fi

if ! $DEPLOYMENT_SUCCESS; then
    error "🚨 Blue-green deployment failed!"
    
    # Send failure notification (if webhook configured)
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{
                \"text\": \"❌ Mirai deployment failed\",
                \"attachments\": [{
                    \"color\": \"danger\",
                    \"fields\": [
                        {\"title\": \"Environment\", \"value\": \"$ENVIRONMENT\", \"short\": true},
                        {\"title\": \"Version\", \"value\": \"$VERSION\", \"short\": true},
                        {\"title\": \"Failed Services\", \"value\": \"${FAILED_SERVICES[*]}\", \"short\": false}
                    ]
                }]
            }" 2>/dev/null || true
    fi
    
    exit 1
fi