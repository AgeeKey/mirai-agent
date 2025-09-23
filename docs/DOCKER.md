# 🐳 Docker Images & Release Guide

## 📦 Available Docker Images

Mirai Agent provides three main Docker images, available with both `latest` and versioned tags:

### 🎯 Core Images
- **API Server**: `ghcr.io/ageekey/mirai-api`
- **Trading Engine**: `ghcr.io/ageekey/mirai-trader`  
- **Web Dashboard**: `ghcr.io/ageekey/mirai-services`

### 🏷️ Tag Strategy
- `latest` - Latest stable build from main branch
- `v{X.Y.Z}` - Specific release version (e.g., `v1.0.0`)
- `main` - Development builds from main branch
- `pr-{number}` - Pull request builds

## 🚀 Using Docker Images

### Quick Start
```bash
# Pull latest images
docker pull ghcr.io/ageekey/mirai-api:latest
docker pull ghcr.io/ageekey/mirai-trader:latest
docker pull ghcr.io/ageekey/mirai-services:latest

# Run with docker-compose
docker-compose -f infra/docker-compose.yml up -d
```

### Specific Version
```bash
# Use specific release
docker pull ghcr.io/ageekey/mirai-api:v1.0.0
docker pull ghcr.io/ageekey/mirai-trader:v1.0.0
docker pull ghcr.io/ageekey/mirai-services:v1.0.0
```

## 🔄 Release Process

### Automated Release
```bash
# Create new release (automatically builds and publishes Docker images)
./scripts/create-release.sh 1.2.3

# Or manually:
git tag v1.2.3
git push origin v1.2.3
```

### Release Features
- ✅ Multi-platform builds (linux/amd64, linux/arm64)
- ✅ Automatic GitHub release creation
- ✅ Docker image publishing to GHCR
- ✅ Release notes generation
- ✅ Build caching for faster deployments

## 📋 CI/CD Workflows

### Main Branch Pushes
- **Trigger**: Push to `main` branch
- **Action**: Build and push `latest` tags
- **Images**: All three services updated

### Release Tags
- **Trigger**: Push tag `v*` (e.g., `v1.0.0`)
- **Action**: Build and push versioned + latest tags
- **Images**: All three services with version tags

### Pull Requests
- **Trigger**: PR creation/update
- **Action**: Build only (no push)
- **Purpose**: Validate Docker builds

## 🏗️ Build Information

### Platforms
- `linux/amd64` - Intel/AMD 64-bit
- `linux/arm64` - ARM 64-bit (Apple Silicon, ARM servers)

### Build Cache
- GitHub Actions cache enabled
- Faster subsequent builds
- Shared across workflows

### Registry
- **Host**: GitHub Container Registry (ghcr.io)
- **Namespace**: `ageekey/`
- **Authentication**: GitHub tokens

## 🎯 Examples

### Production Deployment
```yaml
services:
  mirai-api:
    image: ghcr.io/ageekey/mirai-api:v1.0.0
    ports:
      - "8000:8000"
    
  mirai-trader:
    image: ghcr.io/ageekey/mirai-trader:v1.0.0
    environment:
      - BINANCE_API_KEY=${BINANCE_API_KEY}
      
  mirai-services:
    image: ghcr.io/ageekey/mirai-services:v1.0.0
    ports:
      - "3000:3000"
```

### Development with Latest
```yaml
services:
  mirai-api:
    image: ghcr.io/ageekey/mirai-api:latest
  mirai-trader:
    image: ghcr.io/ageekey/mirai-trader:latest
  mirai-services:
    image: ghcr.io/ageekey/mirai-services:latest
```

## 🔍 Monitoring Builds

### GitHub Actions
- [All Workflows](https://github.com/AgeeKey/mirai-agent/actions)
- [Release Workflow](https://github.com/AgeeKey/mirai-agent/actions/workflows/release.yml)
- [CI Workflows](https://github.com/AgeeKey/mirai-agent/actions)

### Docker Registry
- [GHCR Packages](https://github.com/orgs/AgeeKey/packages)
- [API Images](https://github.com/AgeeKey/mirai-agent/pkgs/container/mirai-api)
- [Trader Images](https://github.com/AgeeKey/mirai-agent/pkgs/container/mirai-trader)
- [Services Images](https://github.com/AgeeKey/mirai-agent/pkgs/container/mirai-services)

## 🚨 Troubleshooting

### Failed Build
```bash
# Check workflow logs
gh run list --workflow=release.yml
gh run view {run-id} --log-failed

# Retry failed release
git tag -d v1.0.0  # Delete locally
git push origin :refs/tags/v1.0.0  # Delete remotely
./scripts/create-release.sh 1.0.0  # Recreate
```

### Image Pull Issues
```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Verify image exists
docker manifest inspect ghcr.io/ageekey/mirai-api:v1.0.0
```

---

**✅ All Docker images are automatically built and published on every release!**
