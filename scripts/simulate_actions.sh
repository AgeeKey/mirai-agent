#!/bin/bash
# simulate_actions.sh - Script to simulate GitHub Actions locally

set -e

echo "🔍 Simulating GitHub Actions CI/CD Pipeline..."

# Set environment variables as they would be in GitHub Actions
export PYTHONPATH="$(pwd)"
export DRY_RUN="true"
export TESTNET="true"
export WEB_USER="testuser"
export WEB_PASS="testpass"

echo "📦 Environment variables set:"
echo "  PYTHONPATH=$PYTHONPATH"
echo "  DRY_RUN=$DRY_RUN"
echo "  TESTNET=$TESTNET"

echo ""
echo "🧪 Running pytest tests..."
python3 -m pytest -q

echo ""
echo "🔍 Testing API-specific workflow..."
python3 -m pytest -q app/api/tests

echo ""
echo "🔍 Testing trader-specific workflow..."
python3 -m pytest -q app/trader/tests

echo ""
echo "✅ All GitHub Actions simulation tests passed!"
echo ""
echo "📊 Summary:"
echo "  - Main CI workflow: ✅"
echo "  - API-specific workflow: ✅"
echo "  - Trader-specific workflow: ✅"
echo "  - Test configuration: ✅"
echo "  - Actions validation tests: ✅"
echo ""
echo "🎉 GitHub Actions are properly configured and working!"