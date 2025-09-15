#!/bin/bash

# GitHub Secrets Setup Script for Mirai Agent
# This script adds all required secrets for production deployment

REPO="AgeeKey/mirai-agent"

echo "🔐 Setting up GitHub Secrets for ${REPO}..."

# Check required environment variables
required_vars=(
    "GH_TOKEN" "GHCR_USERNAME" "GHCR_TOKEN"
    "SSH_HOST" "SSH_USER" "SSH_KEY"
    "OPENAI_API_KEY" "TELEGRAM_BOT_TOKEN" "TELEGRAM_CHAT_ID_ADMIN"
    "BINANCE_API_KEY" "BINANCE_API_SECRET"
    "DOMAIN_PANEL" "DOMAIN_STUDIO" "ENVIRONMENT"
    "JWT_SECRET" "WEB_USER" "WEB_PASS" "CODEX_TOKEN"
)

echo "🔍 Checking required environment variables..."
missing_vars=()
for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        missing_vars+=("$var")
    fi
done

if [[ ${#missing_vars[@]} -gt 0 ]]; then
    echo "❌ Missing required environment variables:"
    printf "   - %s\n" "${missing_vars[@]}"
    echo ""
    echo "Please set all required variables before running this script."
    echo "Example: export GH_TOKEN='your_token_here'"
    exit 1
fi

echo "✅ All required environment variables are set!"
echo ""

# GitHub / GHCR Secrets
echo "📦 Setting up GitHub Container Registry secrets..."
gh secret set GH_TOKEN --body "${GH_TOKEN}" --repo $REPO
gh secret set GHCR_USERNAME --body "${GHCR_USERNAME}" --repo $REPO  
gh secret set GHCR_TOKEN --body "${GHCR_TOKEN}" --repo $REPO

# SSH / Server Secrets
echo "🔧 Setting up SSH server secrets..."
gh secret set SSH_HOST --body "${SSH_HOST}" --repo $REPO
gh secret set SSH_USER --body "${SSH_USER}" --repo $REPO

# SSH Private Key (multiline)
echo "🔑 Setting up SSH private key..."
gh secret set SSH_KEY --body "${SSH_KEY}" --repo $REPO

# Integration API Keys
echo "🤖 Setting up integration API keys..."
gh secret set OPENAI_API_KEY --body "${OPENAI_API_KEY}" --repo $REPO

gh secret set TELEGRAM_BOT_TOKEN --body "${TELEGRAM_BOT_TOKEN}" --repo $REPO
gh secret set TELEGRAM_CHAT_ID_ADMIN --body "${TELEGRAM_CHAT_ID_ADMIN}" --repo $REPO

gh secret set BINANCE_API_KEY --body "${BINANCE_API_KEY}" --repo $REPO
gh secret set BINANCE_API_SECRET --body "${BINANCE_API_SECRET}" --repo $REPO

# Domain and Environment
echo "🌐 Setting up domain and environment secrets..."
gh secret set DOMAIN_PANEL --body "${DOMAIN_PANEL}" --repo $REPO
gh secret set DOMAIN_STUDIO --body "${DOMAIN_STUDIO}" --repo $REPO
gh secret set ENVIRONMENT --body "${ENVIRONMENT}" --repo $REPO

# Security Secrets
echo "🔐 Setting up security secrets..."
gh secret set JWT_SECRET --body "${JWT_SECRET}" --repo $REPO
gh secret set WEB_USER --body "${WEB_USER}" --repo $REPO
gh secret set WEB_PASS --body "${WEB_PASS}" --repo $REPO

# Additional GitHub Token
echo "📝 Setting up additional GitHub token..."
gh secret set CODEX_TOKEN --body "${CODEX_TOKEN}" --repo $REPO

echo "✅ All GitHub Secrets have been set successfully!"
echo ""
echo "📋 Secrets added:"
echo "  - GH_TOKEN, GHCR_USERNAME, GHCR_TOKEN (GitHub Container Registry)"
echo "  - SSH_HOST, SSH_USER, SSH_KEY (Server deployment)" 
echo "  - OPENAI_API_KEY (AI integration)"
echo "  - TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID_ADMIN (Notifications)"
echo "  - BINANCE_API_KEY, BINANCE_API_SECRET (Trading)"
echo "  - DOMAIN_PANEL, DOMAIN_STUDIO (Domains)"
echo "  - JWT_SECRET, WEB_USER, WEB_PASS (Security)"
echo "  - CODEX_TOKEN (Additional GitHub access)"
echo ""
echo "🚀 Ready for production deployment!"
echo ""
echo "💡 Usage:"
echo "  1. Copy scripts/secrets.env.example to secrets.env"
echo "  2. Fill in your actual secret values"
echo "  3. Run: source secrets.env && ./scripts/setup-github-secrets.sh"