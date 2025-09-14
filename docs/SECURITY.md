# Security Policy

## Overview

Mirai Agent follows security best practices for cryptocurrency trading applications.

## Core Security Measures

### 1. Network Security
- All services bind to `127.0.0.1` only (not exposed externally)
- UFW firewall enabled with only ports 80/443 open
- SSH password authentication disabled
- SSH key-only access

### 2. Authentication & Authorization
- JWT tokens with 12-hour expiration
- Strong password requirements for web interface
- API endpoints protected with Bearer token authentication
- Environment-based credentials (no secrets in code)

### 3. Trading Safety
- **DRY_RUN mode enabled by default** - no real trades until explicitly configured
- **TESTNET mode enabled by default** - uses Binance testnet for safety
- Risk management gates prevent excessive trading
- Manual confirmation required to switch to live trading

### 4. Secret Management
- All secrets stored in GitHub Actions secrets
- `.env.production` generated dynamically during deployment
- No API keys or passwords stored in git repository
- JWT secret must be minimum 32 characters

### 5. Container Security
- Non-root users in Docker containers
- Log rotation to prevent disk space attacks
- Healthchecks for service monitoring
- Restart policies for service resilience

### 6. Data Security
- API keys encrypted in transit
- Local database files protected with file permissions
- Log files rotated and size-limited

## Environment Configuration

### Required Security Settings

```bash
# Strong authentication
WEB_USER=admin
WEB_PASS=use_strong_password_here
JWT_SECRET=random_256_bit_string_here

# Safe trading defaults
DRY_RUN=true
USE_TESTNET=true

# Binance API (testnet initially)
BINANCE_API_KEY=testnet_key
BINANCE_API_SECRET=testnet_secret
```

### Production Checklist

Before enabling live trading:
- [ ] UFW firewall configured
- [ ] SSH password auth disabled  
- [ ] Strong passwords set for all accounts
- [ ] JWT secret is cryptographically secure
- [ ] Binance API keys have appropriate permissions
- [ ] Risk limits configured appropriately
- [ ] Monitoring and alerting set up
- [ ] Backup procedures established

## Incident Response

### If API Keys Are Compromised
1. Immediately disable the API keys in Binance
2. Update GitHub Secrets with new keys
3. Redeploy all services
4. Review recent trading activity

### If Server Is Compromised
1. Stop all trading immediately (`docker compose down`)
2. Investigate the breach
3. Rotate all credentials
4. Rebuild server from clean image
5. Review security measures

## Reporting Security Issues

Please report security vulnerabilities by:
1. Creating a private GitHub security advisory
2. Providing detailed information about the vulnerability
3. Including steps to reproduce if applicable

Do not report security issues in public GitHub issues.

## Updates and Maintenance

- Keep Docker images updated
- Monitor security advisories for dependencies
- Regularly rotate API keys and passwords
- Review access logs periodically
- Update SSL certificates before expiration

## Compliance

This application:
- Does not store personal financial information
- Uses read-only market data APIs where possible
- Implements proper access controls
- Maintains audit logs of all trading decisions
- Follows cryptocurrency trading best practices