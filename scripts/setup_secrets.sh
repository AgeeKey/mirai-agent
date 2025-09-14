#!/bin/bash

# Setup script for Mirai Agent secrets management
# This script helps set up secure storage for API keys and sensitive data

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

# Check if required Python packages are installed
print_status "Checking required Python packages..."
python3 -c "import cryptography" 2>/dev/null || {
    print_warning "cryptography package not found. Installing..."
    pip3 install cryptography
}

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Create secrets directory
SECRETS_DIR="$PROJECT_ROOT/app/security"
mkdir -p "$SECRETS_DIR"

# Initialize secrets manager
print_status "Initializing secrets manager..."
python3 -c "
import sys
sys.path.append('$PROJECT_ROOT')
from app.security.secrets_manager import SecretsManager
sm = SecretsManager(key_file='$SECRETS_DIR/secret.key')
print('Secrets manager initialized successfully')
"

# Create secrets file
SECRETS_FILE="$SECRETS_DIR/secrets.enc"
echo "{}" > "$SECRETS_FILE"

# Prompt for API keys
print_status "Please enter your API keys (press Enter to skip):"

read -p "Binance API Key: " BINANCE_API_KEY
read -p "Binance Secret Key: " BINANCE_SECRET_KEY
read -p "Telegram Bot Token: " TELEGRAM_BOT_TOKEN
read -p "Telegram Chat ID: " TELEGRAM_CHAT_ID

# Create secrets dictionary
SECRETS="{}"

# Add secrets if provided
if [ -n "$BINANCE_API_KEY" ]; then
    SECRETS=$(echo "$SECRETS" | jq --arg key "$BINANCE_API_KEY" ".BINANCE_API_KEY = \$key")
fi

if [ -n "$BINANCE_SECRET_KEY" ]; then
    SECRETS=$(echo "$SECRETS" | jq --arg key "$BINANCE_SECRET_KEY" ".BINANCE_SECRET_KEY = \$key")
fi

if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    SECRETS=$(echo "$SECRETS" | jq --arg key "$TELEGRAM_BOT_TOKEN" ".TELEGRAM_BOT_TOKEN = \$key")
fi

if [ -n "$TELEGRAM_CHAT_ID" ]; then
    SECRETS=$(echo "$SECRETS" | jq --arg key "$TELEGRAM_CHAT_ID" ".TELEGRAM_CHAT_ID = \$key")
fi

# Save secrets
print_status "Saving encrypted secrets..."
python3 -c "
import sys
sys.path.append('$PROJECT_ROOT')
from app.security.secrets_manager import SecretsManager
import json

# Load secrets
with open('$SECRETS_FILE', 'r') as f:
    secrets = json.load(f)

# Update with new secrets
updated_secrets = json.loads('$SECRETS')
secrets.update(updated_secrets)

# Save
sm = SecretsManager(key_file='$SECRETS_DIR/secret.key')
sm.save_secrets(secrets, '$SECRETS_FILE')
print('Secrets saved successfully')
"

# Set file permissions
chmod 600 "$SECRETS_DIR/secret.key"
chmod 600 "$SECRETS_FILE"

# Create environment template
print_status "Creating environment template..."
cat > "$PROJECT_ROOT/.env.template" << EOF
# Environment variables for Mirai Agent
# Copy this file to .env and fill in your actual values

# Binance API Keys
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# JWT Secret
JWT_SECRET=your_jwt_secret_here_change_this

# Other settings
# Add your custom settings here
EOF

print_status "Setup completed successfully!"
print_status "Your secrets have been encrypted and stored in $SECRETS_FILE"
print_status "Environment template created at $PROJECT_ROOT/.env.template"
print_status "Remember to copy .env.template to .env and fill in your actual values"
