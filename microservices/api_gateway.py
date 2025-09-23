"""
API Gateway - Centralized Service Orchestration with Load Balancing & Authentication
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import asyncio
import logging
import os
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

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure for production
)

# Redis connection
try:
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
    'ai_engine': {
        'hosts': ['http://ai-engine:8001'],
        'health_path': '/healthz',
        'timeout': 30,
        'retry_count': 3,
        'circuit_breaker': True
    },
    'portfolio_manager': {
        'hosts': ['http://portfolio-manager:8002'],
        'health_path': '/healthz',
        'timeout': 15,
        'retry_count': 3,
        'circuit_breaker': True
    },
    'analytics': {
        'hosts': ['http://analytics:8003'],
        'health_path': '/healthz',
        'timeout': 20,
        'retry_count': 2,
        'circuit_breaker': True
    },
    'data_collector': {
        'hosts': ['http://data-collector:8004'],
        'health_path': '/healthz',
        'timeout': 10,
        'retry_count': 3,
        'circuit_breaker': True
    },
    'strategy_engine': {
        'hosts': ['http://strategy-engine:8005'],
        'health_path': '/healthz',
        'timeout': 15,
        'retry_count': 3,
        'circuit_breaker': True
    },
    'risk_engine': {
        'hosts': ['http://risk-engine:8006'],
        'health_path': '/healthz',
        'timeout': 10,
        'retry_count': 3,
        'circuit_breaker': True
    },
    'notifications': {
        'hosts': ['http://notifications:8007'],
        'health_path': '/healthz',
        'timeout': 10,
        'retry_count': 2,
        'circuit_breaker': True
    }
}

# Data Models
class User(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    roles: List[str] = Field(default_factory=list, description="User roles")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    is_active: bool = Field(True, description="Account active status")
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

class LoginRequest(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")
    user: User = Field(..., description="User information")

class ServiceHealth(BaseModel):
    service_name: str = Field(..., description="Service name")
    status: str = Field(..., description="healthy, unhealthy, unknown")
    response_time: float = Field(..., description="Response time in milliseconds")
    last_check: datetime = Field(..., description="Last health check timestamp")
    error_message: Optional[str] = Field(None, description="Error message if unhealthy")

class GatewayStats(BaseModel):
    total_requests: int = Field(0, description="Total requests processed")
    successful_requests: int = Field(0, description="Successful requests")
    failed_requests: int = Field(0, description="Failed requests")
    average_response_time: float = Field(0.0, description="Average response time in ms")
    requests_per_minute: float = Field(0.0, description="Requests per minute")
    active_connections: int = Field(0, description="Active connections")
    service_health: Dict[str, ServiceHealth] = Field(default_factory=dict, description="Service health status")

class RouteRule(BaseModel):
    rule_id: str = Field(..., description="Unique rule identifier")
    path_pattern: str = Field(..., description="URL path pattern")
    target_service: str = Field(..., description="Target service name")
    methods: List[str] = Field(default_factory=list, description="Allowed HTTP methods")
    auth_required: bool = Field(True, description="Authentication required")
    rate_limit: Optional[int] = Field(None, description="Rate limit per minute")
    timeout: Optional[int] = Field(None, description="Request timeout in seconds")
    enabled: bool = Field(True, description="Rule enabled status")

# API Gateway Service
class APIGateway:
    def __init__(self):
        self.service_stats: Dict[str, Dict] = {}
        self.circuit_breakers: Dict[str, Dict] = {}
        self.route_rules: Dict[str, RouteRule] = {}
        self.users: Dict[str, User] = {}
        self.request_count = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        
        # Initialize circuit breakers
        for service_name in MICROSERVICES.keys():
            self.circuit_breakers[service_name] = {
                'state': 'CLOSED',  # CLOSED, OPEN, HALF_OPEN
                'failure_count': 0,
                'last_failure_time': None,
                'timeout': 60  # seconds
            }
        
        # Initialize default users
        self._initialize_default_users()
        self._initialize_default_routes()
    
    def _initialize_default_users(self):
        """Initialize default users for development"""
        admin_user = User(
            user_id="admin",
            username="admin",
            email="admin@mirai.com",
            roles=["admin", "trader"],
            permissions=["read", "write", "admin", "trade"],
            is_active=True
        )
        
        trader_user = User(
            user_id="trader",
            username="trader",
            email="trader@mirai.com",
            roles=["trader"],
            permissions=["read", "write", "trade"],
            is_active=True
        )
        
        readonly_user = User(
            user_id="readonly",
            username="readonly",
            email="readonly@mirai.com",
            roles=["viewer"],
            permissions=["read"],
            is_active=True
        )
        
        self.users["admin"] = admin_user
        self.users["trader"] = trader_user
        self.users["readonly"] = readonly_user
    
    def _initialize_default_routes(self):
        """Initialize default routing rules"""
        routes = [
            RouteRule(
                rule_id="ai_engine_routes",
                path_pattern="/api/ai/*",
                target_service="ai_engine",
                methods=["GET", "POST"],
                auth_required=True,
                rate_limit=100
            ),
            RouteRule(
                rule_id="portfolio_routes", 
                path_pattern="/api/portfolio/*",
                target_service="portfolio_manager",
                methods=["GET", "POST", "PUT", "DELETE"],
                auth_required=True,
                rate_limit=200
            ),
            RouteRule(
                rule_id="analytics_routes",
                path_pattern="/api/analytics/*",
                target_service="analytics",
                methods=["GET", "POST"],
                auth_required=True,
                rate_limit=50
            ),
            RouteRule(
                rule_id="data_routes",
                path_pattern="/api/data/*",
                target_service="data_collector",
                methods=["GET", "POST"],
                auth_required=True,
                rate_limit=500
            ),
            RouteRule(
                rule_id="strategy_routes",
                path_pattern="/api/strategy/*",
                target_service="strategy_engine",
                methods=["GET", "POST"],
                auth_required=True,
                rate_limit=100
            ),
            RouteRule(
                rule_id="risk_routes",
                path_pattern="/api/risk/*",
                target_service="risk_engine",
                methods=["GET", "POST"],
                auth_required=True,
                rate_limit=150
            ),
            RouteRule(
                rule_id="notification_routes",
                path_pattern="/api/notifications/*",
                target_service="notifications",
                methods=["GET", "POST", "DELETE"],
                auth_required=True,
                rate_limit=100
            )
        ]
        
        for route in routes:
            self.route_rules[route.rule_id] = route
    
    async def get_healthy_service_host(self, service_name: str) -> Optional[str]:
        """Get a healthy host for the specified service with load balancing"""
        if service_name not in MICROSERVICES:
            return None
        
        service_config = MICROSERVICES[service_name]
        hosts = service_config['hosts']
        
        # Check circuit breaker
        circuit_breaker = self.circuit_breakers[service_name]
        if circuit_breaker['state'] == 'OPEN':
            # Check if timeout has passed
            if (datetime.now() - circuit_breaker['last_failure_time']).seconds > circuit_breaker['timeout']:
                circuit_breaker['state'] = 'HALF_OPEN'
            else:
                logger.warning(f"🔴 Circuit breaker OPEN for {service_name}")
                return None
        
        # Round-robin load balancing (simple implementation)
        # In production, you might want more sophisticated load balancing
        if not hasattr(self, '_host_indices'):
            self._host_indices = {}
        
        if service_name not in self._host_indices:
            self._host_indices[service_name] = 0
        
        # Try each host in round-robin fashion
        for _ in range(len(hosts)):
            host_index = self._host_indices[service_name] % len(hosts)
            host = hosts[host_index]
            self._host_indices[service_name] = (self._host_indices[service_name] + 1) % len(hosts)
            
            # Check if host is healthy
            if await self._check_service_health(service_name, host):
                return host
        
        # All hosts are unhealthy
        logger.error(f"❌ All hosts unhealthy for service: {service_name}")
        return None
    
    async def _check_service_health(self, service_name: str, host: str) -> bool:
        """Check if a specific service host is healthy"""
        try:
            service_config = MICROSERVICES[service_name]
            health_url = f"{host}{service_config['health_path']}"
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(health_url)
                is_healthy = response.status_code == 200
                
                if is_healthy:
                    # Reset circuit breaker on successful health check
                    self.circuit_breakers[service_name]['failure_count'] = 0
                    if self.circuit_breakers[service_name]['state'] == 'HALF_OPEN':
                        self.circuit_breakers[service_name]['state'] = 'CLOSED'
                
                return is_healthy
                
        except Exception as e:
            logger.warning(f"⚠️ Health check failed for {service_name} at {host}: {e}")
            self._handle_service_failure(service_name)
            return False
    
    def _handle_service_failure(self, service_name: str):
        """Handle service failure and update circuit breaker"""
        circuit_breaker = self.circuit_breakers[service_name]
        circuit_breaker['failure_count'] += 1
        circuit_breaker['last_failure_time'] = datetime.now()
        
        # Open circuit breaker after 5 failures
        if circuit_breaker['failure_count'] >= 5:
            circuit_breaker['state'] = 'OPEN'
            logger.error(f"🔴 Circuit breaker OPENED for {service_name}")

# Initialize gateway
gateway = APIGateway()

# Authentication functions
def create_access_token(user: User) -> str:
    """Create JWT access token"""
    payload = {
        'user_id': user.user_id,
        'username': user.username,
        'roles': user.roles,
        'permissions': user.permissions,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token and return user info"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

# Middleware for request logging and metrics
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    gateway.request_count += 1
    
    try:
        response = await call_next(request)
        
        # Calculate response time
        process_time = (time.time() - start_time) * 1000
        gateway.response_times.append(process_time)
        
        # Keep only last 1000 response times for average calculation
        if len(gateway.response_times) > 1000:
            gateway.response_times = gateway.response_times[-1000:]
        
        if response.status_code < 400:
            gateway.successful_requests += 1
        else:
            gateway.failed_requests += 1
        
        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = str(gateway.request_count)
        
        logger.info(f"📊 {request.method} {request.url.path} - {response.status_code} - {process_time:.2f}ms")
        
        return response
        
    except Exception as e:
        gateway.failed_requests += 1
        logger.error(f"❌ Request failed: {e}")
        raise