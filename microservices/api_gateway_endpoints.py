"""
API Gateway Endpoints - Service Orchestration and Authentication
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Response, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import asyncio
import logging
import json
import jwt
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import redis
import aiohttp
import httpx
from dataclasses import dataclass
import random
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mirai API Gateway",
    description="🌐 Centralized API Gateway with Load Balancing, Authentication & Service Orchestration",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security
security = HTTPBearer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
try:
    import os
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        decode_responses=True,
        socket_timeout=5
    )
    redis_client.ping()
    logger.info("✅ Redis connection established")
except Exception as e:
    logger.warning(f"⚠️ Redis connection failed: {e}")
    redis_client = None

# Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'mirai-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = int(os.getenv('JWT_EXPIRY_HOURS', 24))

# Service Configuration
MICROSERVICES = {
    'ai': {
        'hosts': ['http://localhost:8001'],
        'health_path': '/healthz',
        'timeout': 30,
        'retry_count': 3,
        'circuit_breaker': True
    },
    'portfolio': {
        'hosts': ['http://localhost:8002'],
        'health_path': '/healthz',
        'timeout': 15,
        'retry_count': 3,
        'circuit_breaker': True
    },
    'analytics': {
        'hosts': ['http://localhost:8003'],
        'health_path': '/healthz',
        'timeout': 20,
        'retry_count': 2,
        'circuit_breaker': True
    },
    'data': {
        'hosts': ['http://localhost:8004'],
        'health_path': '/healthz',
        'timeout': 10,
        'retry_count': 3,
        'circuit_breaker': True
    },
    'strategy': {
        'hosts': ['http://localhost:8005'],
        'health_path': '/healthz',
        'timeout': 15,
        'retry_count': 3,
        'circuit_breaker': True
    },
    'risk': {
        'hosts': ['http://localhost:8006'],
        'health_path': '/healthz',
        'timeout': 10,
        'retry_count': 3,
        'circuit_breaker': True
    },
    'notifications': {
        'hosts': ['http://localhost:8007'],
        'health_path': '/healthz',
        'timeout': 10,
        'retry_count': 2,
        'circuit_breaker': True
    }
}

# Request/Response Models
class ProxyRequest(BaseModel):
    method: str = "GET"
    path: str
    headers: Dict[str, str] = {}
    body: Optional[Any] = None
    params: Dict[str, str] = {}

class ServiceRequest(BaseModel):
    service: str
    endpoint: str
    method: str = "GET"
    data: Optional[Any] = None
    headers: Dict[str, str] = {}

class UserRegistration(BaseModel):
    username: str
    email: str
    password: str
    roles: List[str] = ["viewer"]

class RouteRequest(BaseModel):
    rule_id: str
    path_pattern: str
    target_service: str
    methods: List[str] = ["GET"]
    auth_required: bool = True
    rate_limit: Optional[int] = None

# Health Check
@app.get("/healthz")
async def health_check():
    """API Gateway health check"""
    try:
        # Check Redis connection
        redis_status = "healthy"
        if gateway.redis_client:
            try:
                gateway.redis_client.ping()
            except:
                redis_status = "unhealthy"
        
        # Get service health summary
        healthy_services = 0
        total_services = len(MICROSERVICES)
        
        for service_name in MICROSERVICES.keys():
            circuit_breaker = gateway.circuit_breakers[service_name]
            if circuit_breaker['state'] == 'CLOSED':
                healthy_services += 1
        
        return {
            "status": "healthy",
            "service": "api_gateway",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "stats": {
                "total_requests": gateway.request_count,
                "successful_requests": gateway.successful_requests,
                "failed_requests": gateway.failed_requests,
                "healthy_services": f"{healthy_services}/{total_services}",
                "redis_status": redis_status
            }
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Gateway unhealthy: {str(e)}")

# Authentication Endpoints
@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    User authentication and JWT token generation
    
    Default credentials:
    - admin/admin (full access)
    - trader/trader (trading access)
    - readonly/readonly (read-only access)
    """
    try:
        logger.info(f"🔐 Login attempt for user: {request.username}")
        
        # Simple password verification (in production, use proper hashing)
        valid_credentials = {
            "admin": "admin",
            "trader": "trader", 
            "readonly": "readonly"
        }
        
        if request.username not in valid_credentials or valid_credentials[request.username] != request.password:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user = gateway.users[request.username]
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Account disabled")
        
        # Update last login
        user.last_login = datetime.now()
        
        # Generate token
        access_token = create_access_token(user)
        expires_in = 24 * 3600  # 24 hours
        
        logger.info(f"✅ Login successful for user: {request.username}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login failed: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/auth/register", response_model=User)
async def register_user(request: UserRegistration):
    """Register a new user"""
    try:
        logger.info(f"👤 Registering new user: {request.username}")
        
        # Check if user already exists
        if request.username in gateway.users:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Create new user
        user = User(
            user_id=request.username,
            username=request.username,
            email=request.email,
            roles=request.roles,
            permissions=["read"] if "viewer" in request.roles else ["read", "write"],
            is_active=True
        )
        
        gateway.users[request.username] = user
        
        # In production, store hashed password
        # For now, we'll store it in the valid_credentials dict
        
        logger.info(f"✅ User registered: {request.username}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ User registration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.get("/auth/profile", response_model=User)
async def get_profile(current_user: Dict[str, Any] = Depends(verify_token)):
    """Get current user profile"""
    try:
        user_id = current_user['user_id']
        if user_id not in gateway.users:
            raise HTTPException(status_code=404, detail="User not found")
        
        return gateway.users[user_id]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get profile failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get profile failed: {str(e)}")

# Service Proxy Endpoints
@app.api_route("/api/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_service(
    service_name: str,
    path: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """
    Proxy requests to microservices with authentication and load balancing
    
    Routes:
    - /api/ai/* → AI Engine (8001)
    - /api/portfolio/* → Portfolio Manager (8002)
    - /api/analytics/* → Analytics (8003)
    - /api/data/* → Data Collector (8004)
    - /api/strategy/* → Strategy Engine (8005)
    - /api/risk/* → Risk Engine (8006)
    - /api/notifications/* → Notifications (8007)
    """
    try:
        logger.info(f"🔀 Proxying request: {request.method} /api/{service_name}/{path}")
        
        # Check if service exists
        if service_name not in MICROSERVICES:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
        
        # Get healthy service host
        host = await gateway.get_healthy_service_host(service_name)
        if not host:
            raise HTTPException(status_code=503, detail=f"Service '{service_name}' unavailable")
        
        # Build target URL
        target_url = f"{host}/{path}"
        
        # Get request body
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
            except:
                body = None
        
        # Prepare headers
        headers = dict(request.headers)
        headers['X-User-ID'] = current_user['user_id']
        headers['X-User-Roles'] = ','.join(current_user['roles'])
        headers['X-User-Permissions'] = ','.join(current_user['permissions'])
        
        # Remove problematic headers
        headers.pop('host', None)
        headers.pop('content-length', None)
        
        # Make request to target service
        service_config = MICROSERVICES[service_name]
        timeout = service_config.get('timeout', 30)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=dict(request.query_params)
            )
        
        # Return response
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get('content-type')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Proxy request failed: {e}")
        gateway._handle_service_failure(service_name)
        raise HTTPException(status_code=500, detail=f"Proxy request failed: {str(e)}")

@app.post("/api/request/{service_name}")
async def service_request(
    service_name: str,
    request: ServiceRequest,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Direct service request with custom data"""
    try:
        logger.info(f"📡 Service request: {service_name} {request.endpoint}")
        
        # Check if service exists
        if service_name not in MICROSERVICES:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
        
        # Get healthy service host
        host = await gateway.get_healthy_service_host(service_name)
        if not host:
            raise HTTPException(status_code=503, detail=f"Service '{service_name}' unavailable")
        
        # Build target URL
        target_url = f"{host}{request.endpoint}"
        
        # Prepare headers
        headers = request.headers.copy()
        headers['X-User-ID'] = current_user['user_id']
        headers['X-User-Roles'] = ','.join(current_user['roles'])
        headers['Content-Type'] = 'application/json'
        
        # Make request
        service_config = MICROSERVICES[service_name]
        timeout = service_config.get('timeout', 30)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            if request.method.upper() == "GET":
                response = await client.get(target_url, headers=headers)
            elif request.method.upper() == "POST":
                response = await client.post(target_url, headers=headers, json=request.data)
            elif request.method.upper() == "PUT":
                response = await client.put(target_url, headers=headers, json=request.data)
            elif request.method.upper() == "DELETE":
                response = await client.delete(target_url, headers=headers)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported method: {request.method}")
        
        return response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Service request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Service request failed: {str(e)}")

# Service Health and Statistics
@app.get("/services/health", response_model=Dict[str, ServiceHealth])
async def get_services_health():
    """Get health status of all microservices"""
    try:
        health_status = {}
        
        for service_name, config in MICROSERVICES.items():
            for host in config['hosts']:
                start_time = time.time()
                is_healthy = await gateway._check_service_health(service_name, host)
                response_time = (time.time() - start_time) * 1000
                
                health_status[f"{service_name}_{host.split('//')[-1]}"] = ServiceHealth(
                    service_name=service_name,
                    status="healthy" if is_healthy else "unhealthy",
                    response_time=response_time,
                    last_check=datetime.now(),
                    error_message=None if is_healthy else "Health check failed"
                )
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Get services health failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get services health failed: {str(e)}")

@app.get("/gateway/stats", response_model=GatewayStats)
async def get_gateway_stats():
    """Get API Gateway statistics"""
    try:
        # Calculate average response time
        avg_response_time = sum(gateway.response_times) / len(gateway.response_times) if gateway.response_times else 0
        
        # Calculate requests per minute (rough estimate)
        requests_per_minute = gateway.request_count / max(1, (time.time() / 60))
        
        # Get service health
        service_health = {}
        for service_name in MICROSERVICES.keys():
            circuit_breaker = gateway.circuit_breakers[service_name]
            service_health[service_name] = ServiceHealth(
                service_name=service_name,
                status="healthy" if circuit_breaker['state'] == 'CLOSED' else "unhealthy",
                response_time=0,  # Would need to track this separately
                last_check=datetime.now(),
                error_message=f"Circuit breaker {circuit_breaker['state']}" if circuit_breaker['state'] != 'CLOSED' else None
            )
        
        return GatewayStats(
            total_requests=gateway.request_count,
            successful_requests=gateway.successful_requests,
            failed_requests=gateway.failed_requests,
            average_response_time=avg_response_time,
            requests_per_minute=requests_per_minute,
            active_connections=0,  # Would need WebSocket tracking
            service_health=service_health
        )
        
    except Exception as e:
        logger.error(f"❌ Get gateway stats failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get gateway stats failed: {str(e)}")

# Route Management
@app.get("/routes", response_model=List[RouteRule])
async def get_routes(current_user: Dict[str, Any] = Depends(verify_token)):
    """Get all routing rules"""
    if "admin" not in current_user['roles']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return list(gateway.route_rules.values())

@app.post("/routes", response_model=RouteRule)
async def create_route(
    request: RouteRequest,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Create a new routing rule"""
    if "admin" not in current_user['roles']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        route = RouteRule(
            rule_id=request.rule_id,
            path_pattern=request.path_pattern,
            target_service=request.target_service,
            methods=request.methods,
            auth_required=request.auth_required,
            rate_limit=request.rate_limit
        )
        
        gateway.route_rules[request.rule_id] = route
        
        logger.info(f"✅ Route created: {request.rule_id}")
        return route
        
    except Exception as e:
        logger.error(f"❌ Create route failed: {e}")
        raise HTTPException(status_code=500, detail=f"Create route failed: {str(e)}")

# Circuit Breaker Management
@app.post("/circuit-breaker/{service_name}/reset")
async def reset_circuit_breaker(
    service_name: str,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Reset circuit breaker for a service"""
    if "admin" not in current_user['roles']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        if service_name not in gateway.circuit_breakers:
            raise HTTPException(status_code=404, detail="Service not found")
        
        gateway.circuit_breakers[service_name] = {
            'state': 'CLOSED',
            'failure_count': 0,
            'last_failure_time': None,
            'timeout': 60
        }
        
        logger.info(f"🔄 Circuit breaker reset for: {service_name}")
        return {"status": "reset", "service": service_name}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Reset circuit breaker failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reset circuit breaker failed: {str(e)}")

@app.get("/circuit-breakers")
async def get_circuit_breakers(current_user: Dict[str, Any] = Depends(verify_token)):
    """Get circuit breaker status for all services"""
    if "admin" not in current_user['roles']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return gateway.circuit_breakers

# Testing Endpoints
@app.get("/test/connectivity")
async def test_service_connectivity(current_user: Dict[str, Any] = Depends(verify_token)):
    """Test connectivity to all microservices"""
    try:
        results = {}
        
        for service_name, config in MICROSERVICES.items():
            service_results = []
            
            for host in config['hosts']:
                start_time = time.time()
                is_healthy = await gateway._check_service_health(service_name, host)
                response_time = (time.time() - start_time) * 1000
                
                service_results.append({
                    "host": host,
                    "healthy": is_healthy,
                    "response_time_ms": response_time
                })
            
            results[service_name] = service_results
        
        return {
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"❌ Connectivity test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Connectivity test failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)