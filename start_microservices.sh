#!/bin/bash

# Mirai Agent Phase 2 - Quick Start Script
echo "🚀 Starting Mirai Agent Phase 2 Microservices..."

# Activate virtual environment
cd /root/mirai-agent
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install fastapi uvicorn pydantic httpx pyjwt redis
else
    source venv/bin/activate
fi

# Set environment variables
export REDIS_HOST=localhost
export REDIS_PORT=6379
export JWT_SECRET=mirai-jwt-secret-test
export ENVIRONMENT=development

# Function to start a microservice
start_service() {
    local service_name=$1
    local port=$2
    local module_name=$3
    
    echo "🔄 Starting $service_name on port $port..."
    cd microservices
    ../venv/bin/python -m uvicorn "$module_name:app" --host 0.0.0.0 --port $port &
    cd ..
    sleep 1
}

# Kill any existing uvicorn processes
pkill -f uvicorn

# Start microservices on available ports
echo "🌐 Starting microservices..."

# Start API Gateway on port 8000 (free)
start_service "API Gateway" 8000 "gateway"

# Start simple test services on free ports
start_service "AI Engine" 8001 "ai_simple"
start_service "Portfolio Manager" 8002 "portfolio_simple"

echo ""
echo "✅ Core services started!"
echo ""
echo "🌐 API Gateway: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "🔐 Test Authentication:"
echo "curl -X POST 'http://localhost:8000/auth/login' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"username\": \"admin\", \"password\": \"admin\"}'"
echo ""
echo "🧪 Test API Gateway proxy:"
echo "# Get token first, then:"
echo "curl -H 'Authorization: Bearer <token>' \\"
echo "  'http://localhost:8000/api/ai/analyze' \\"
echo "  -X POST -H 'Content-Type: application/json' \\"
echo "  -d '{\"symbol\": \"BTCUSDT\"}'"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "🛑 Stopping services..."; pkill -f uvicorn; exit 0' INT

# Keep script running and show service status
while true; do
    sleep 30
    echo "📊 Services running... ($(date))"
done