# Mirai Infrastructure as Code

This directory contains Infrastructure as Code (IaC) configurations for deploying the Mirai Trading System across different environments.

## Architecture Overview

```
Production Environment
├── Kubernetes Cluster (EKS)
│   ├── Mirai API (3 replicas)
│   ├── Mirai Trader (2 replicas)
│   ├── Mirai Web (2 replicas)
│   └── Telegram Bot (1 replica)
├── RDS PostgreSQL (Multi-AZ)
├── ElastiCache Redis (Cluster)
├── Application Load Balancer
├── CloudFront CDN
└── Route53 DNS
```

## Directory Structure

```
infra/
├── terraform/          # Terraform infrastructure
│   ├── modules/        # Reusable modules
│   ├── environments/   # Environment-specific configs
│   └── global/         # Global resources
├── k8s/               # Kubernetes manifests
│   ├── base/          # Base configurations
│   ├── staging/       # Staging overlays
│   └── production/    # Production overlays
├── helm/              # Helm charts
│   └── mirai/         # Mirai application chart
├── monitoring/        # Monitoring configurations
│   ├── prometheus/    # Prometheus configs
│   ├── grafana/       # Grafana dashboards
│   └── alerts/        # Alert rules
├── docker-compose.yml  # Development environment
├── docker-compose.prod.yml # Production environment
├── env/               # Environment configuration files
├── nginx/             # Nginx configuration
├── sql/               # Database initialization scripts
└── scripts/           # Deployment scripts
```

## Prerequisites

- AWS CLI configured
- Terraform >= 1.0
- kubectl >= 1.24
- Helm >= 3.8
- Docker

## Quick Start

### Development Environment

```bash
# Start development environment
docker-compose up -d

# Check services
docker-compose ps
```

### Production Deployment

#### 1. Initialize Infrastructure

```bash
# Initialize Terraform
cd infra/terraform/environments/production
terraform init

# Plan infrastructure
terraform plan -var-file="production.tfvars"

# Apply infrastructure
terraform apply -var-file="production.tfvars"
```

#### 2. Deploy Application

```bash
# Update kubeconfig
aws eks update-kubeconfig --name mirai-production

# Deploy using Helm
cd infra/helm
helm upgrade --install mirai ./mirai \
  --namespace mirai-production \
  --create-namespace \
  --values values-production.yaml
```

#### 3. Setup Monitoring

```bash
# Deploy monitoring stack
kubectl apply -f infra/monitoring/prometheus/
kubectl apply -f infra/monitoring/grafana/

# Import dashboards
cd infra/monitoring/grafana/dashboards
for dashboard in *.json; do
  curl -X POST "https://grafana.example.com/api/dashboards/db" \
    -H "Authorization: Bearer $GRAFANA_API_KEY" \
    -H "Content-Type: application/json" \
    -d @$dashboard
done
```

## Services

### Core Services

- **API**: FastAPI backend service
- **Trader**: Trading engine
- **Web**: Next.js frontend
- **Telegram Bot**: Notification service

### Infrastructure Services

- **PostgreSQL**: Primary database
- **Redis**: Caching and message queue
- **Nginx**: Reverse proxy and load balancer
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards

## Environment Management

### Staging Environment

```bash
# Deploy to staging
cd infra/terraform/environments/staging
terraform init
terraform apply -var-file="staging.tfvars"

# Deploy application
helm upgrade --install mirai-staging ./mirai \
  --namespace mirai-staging \
  --create-namespace \
  --values values-staging.yaml
```

### Production Environment

```bash
# Deploy to production
cd infra/terraform/environments/production
terraform init
terraform apply -var-file="production.tfvars"

# Deploy application with blue-green strategy
./scripts/blue-green-deploy.sh production v1.2.3
```

## Configuration

### Environment Variables

Copy and modify the environment files:

```bash
cp env/api.env.example env/api.env
cp env/postgres.env.example env/postgres.env
cp env/redis.env.example env/redis.env
```

### Secrets Management

For production, use AWS Secrets Manager or Kubernetes secrets:

```bash
# Kubernetes secrets
kubectl create secret generic mirai-secrets \
  --from-literal=database-password=your_password \
  --from-literal=binance-api-key=your_api_key \
  --namespace mirai-production

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name mirai/production/database \
  --secret-string '{"password":"your_password"}'
```

## Security Configuration

### Network Security

- VPC with private subnets for workloads
- Public subnets for load balancers only
- Security groups with least privilege
- NACLs for additional layer of protection

### Application Security

- Pod Security Standards (restricted)
- Network Policies for service isolation
- Secrets managed via AWS Secrets Manager
- Image scanning with Trivy

### Access Control

- IAM roles for service accounts (IRSA)
- RBAC for Kubernetes access
- AWS IAM for infrastructure access
- Multi-factor authentication required

## Monitoring & Alerting

### Prometheus Metrics

Available at `http://localhost:9090` (dev) or `https://prometheus.example.com` (prod)

Key metrics:
- `mirai_trades_total`
- `mirai_positions_active`
- `mirai_api_requests_total`
- `mirai_api_request_duration_seconds`
- `mirai_trading_pnl`
- `mirai_risk_exposure`

### Grafana Dashboards

Available at `http://localhost:3001` (dev) or `https://grafana.example.com` (prod)

Default dev credentials: `admin/admin`

Dashboards:
1. **Trading Overview**: P&L, positions, trades
2. **System Health**: CPU, memory, network
3. **Application Performance**: Response times, errors
4. **Infrastructure**: Kubernetes cluster metrics

### Alert Rules

- High error rates (>5%)
- Response time degradation (>2s)
- Memory usage (>80%)
- Trading system downtime
- Failed deployments

## Scaling

### Horizontal Scaling

```bash
# Docker Compose (Development)
docker-compose up -d --scale api=3

# Kubernetes (Production)
kubectl scale deployment mirai-api --replicas=5 -n mirai-production
```

### Auto Scaling

- Horizontal Pod Autoscaler (HPA) for pods
- Cluster Autoscaler for nodes
- RDS auto scaling for storage
- Redis cluster scaling

### Load Balancing

Nginx is configured to load balance across multiple instances:

```nginx
upstream api_backend {
    server api:8000;
    server api_2:8000;
    server api_3:8000;
}
```

## Disaster Recovery

### Backup Strategy

- Database: Automated RDS backups + manual snapshots
- Configuration: GitOps with version control
- Secrets: AWS Secrets Manager replication
- Application data: S3 cross-region replication

### Recovery Procedures

1. **Database Recovery**
   ```bash
   # Docker (Development)
   docker exec postgres pg_dump -U mirai mirai > backup_$(date +%Y%m%d).sql
   
   # RDS (Production)
   aws rds restore-db-instance-from-db-snapshot \
     --db-instance-identifier mirai-production \
     --db-snapshot-identifier mirai-production-2024-01-01
   ```

2. **Application Recovery**
   ```bash
   # Kubernetes
   helm rollback mirai --namespace mirai-production
   
   # Docker Compose
   docker-compose down && docker-compose up -d
   ```

3. **Infrastructure Recovery**
   ```bash
   # Restore infrastructure
   terraform apply -var-file="production.tfvars"
   ```

## Performance Optimization

### Resource Optimization

- Resource requests and limits
- Quality of Service (QoS) classes
- Node affinity and anti-affinity
- Spot instances for non-critical workloads

### Volume Backup

```bash
# Backup persistent volumes
docker run --rm -v mirai_postgres_data:/source -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /source .
```

## Cost Management

### Cost Optimization

- Spot instances for development
- Reserved instances for production
- Automatic shutdown of dev environments
- Right-sizing recommendations

### Cost Monitoring

- AWS Cost Explorer integration
- Kubecost for Kubernetes costs
- Budget alerts and notifications
- Regular cost reviews

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   # Docker Compose
   docker-compose logs service_name
   
   # Kubernetes
   kubectl describe pod <pod-name> -n mirai-production
   kubectl logs <pod-name> -n mirai-production --previous
   ```

2. **Database connection issues**
   ```bash
   # Docker
   docker exec -it postgres psql -U mirai -d mirai
   
   # Kubernetes
   kubectl exec -it <api-pod> -n mirai-production -- \
     psql $DATABASE_URL -c "SELECT 1"
   ```

3. **Service connectivity**
   ```bash
   kubectl get endpoints -n mirai-production
   kubectl run debug --image=nicolaka/netshoot -it --rm
   ```

4. **High memory usage**
   ```bash
   # Docker
   docker stats
   
   # Kubernetes
   kubectl top pods -n mirai-production
   kubectl describe node <node-name>
   ```

### Health Checks

All services include health checks accessible via:
- API: `http://localhost:8000/health` (dev) or `https://mirai.example.com/api/health` (prod)
- Web: `http://localhost:3000/health` (dev) or `https://mirai.example.com/health` (prod)
- Prometheus: `http://localhost:9090/-/healthy` (dev) or `https://prometheus.example.com/-/healthy` (prod)
- Grafana: `http://localhost:3001/api/health` (dev) or `https://grafana.example.com/api/health` (prod)

## Maintenance

### Regular Maintenance

- **Weekly**: Security updates
- **Monthly**: Dependency updates  
- **Quarterly**: Infrastructure review
- **Annually**: Disaster recovery testing

### Maintenance Windows

- **Staging**: Tuesday 2-4 AM UTC
- **Production**: Sunday 2-6 AM UTC
- **Emergency**: Anytime with approval

### Update Procedures

1. **Application Updates**
   ```bash
   # Blue-green deployment
   ./scripts/blue-green-deploy.sh production v1.2.4
   ```

2. **Infrastructure Updates**
   ```bash
   # Plan and apply incrementally
   terraform plan -var-file="production.tfvars"
   terraform apply -target=module.eks
   ```

3. **Security Updates**
   ```bash
   # Force pod recreation for security updates
   kubectl rollout restart deployment/mirai-api -n mirai-production
   ```

## Support & Escalation

### Support Tiers

1. **L1**: Basic monitoring and alerts
2. **L2**: Application troubleshooting
3. **L3**: Infrastructure and architecture

### Escalation Procedures

1. **Critical Issues** (Trading down)
   - Immediate page to on-call engineer
   - Auto-escalate to L3 after 15 minutes
   - Executive notification after 30 minutes

2. **High Issues** (Performance degraded)
   - Alert to on-call engineer
   - Escalate to L2 after 30 minutes
   - Escalate to L3 after 2 hours

3. **Medium/Low Issues**
   - Create ticket in system
   - Assign to appropriate team
   - Regular status updates

This infrastructure setup ensures high availability, security, and performance for the Mirai Trading System while maintaining cost efficiency and operational excellence.