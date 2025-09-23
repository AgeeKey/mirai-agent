#!/usr/bin/env python3
"""
Standalone API Gateway for Mirai Agent
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import logging
import os
import json
import jwt
import httpx
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mirai API Gateway",
    description="🌐 Centralized API Gateway",
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

# Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'mirai-secret-key-test')
JWT_ALGORITHM = 'HS256'

# Data Models
class User(BaseModel):
    user_id: str
    username: str
    email: str
    roles: List[str] = []
    permissions: List[str] = []
    is_active: bool = True

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User

# Service Configuration
MICROSERVICES = {
    'ai': 'http://localhost:8010',
    'portfolio': 'http://localhost:8011', 
    'analytics': 'http://localhost:8003',
    'data': 'http://localhost:8004',
    'strategy': 'http://localhost:8005',
    'risk': 'http://localhost:8006',
    'notifications': 'http://localhost:8007'
}

# Default users
USERS = {
    "admin": User(
        user_id="admin",
        username="admin", 
        email="admin@mirai.com",
        roles=["admin", "trader"],
        permissions=["read", "write", "admin", "trade"],
        is_active=True
    ),
    "trader": User(
        user_id="trader",
        username="trader",
        email="trader@mirai.com", 
        roles=["trader"],
        permissions=["read", "write", "trade"],
        is_active=True
    )
}

# Authentication functions
def create_access_token(user: User) -> str:
    """Create JWT access token"""
    payload = {
        'user_id': user.user_id,
        'username': user.username,
        'roles': user.roles,
        'permissions': user.permissions,
        'exp': datetime.utcnow() + timedelta(hours=24),
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

# Endpoints
@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "api_gateway",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """User authentication and JWT token generation"""
    try:
        logger.info(f"🔐 Login attempt for user: {request.username}")
        
        # Simple password verification
        valid_credentials = {
            "admin": "admin",
            "trader": "trader"
        }
        
        if request.username not in valid_credentials or valid_credentials[request.username] != request.password:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user = USERS[request.username]
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Account disabled")
        
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

@app.get("/auth/profile", response_model=User)
async def get_profile(current_user: Dict[str, Any] = Depends(verify_token)):
    """Get current user profile"""
    user_id = current_user['user_id']
    if user_id not in USERS:
        raise HTTPException(status_code=404, detail="User not found")
    
    return USERS[user_id]

@app.api_route("/api/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_service(
    service_name: str,
    path: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Proxy requests to microservices"""
    try:
        logger.info(f"🔀 Proxying request: {request.method} /api/{service_name}/{path}")
        
        # Check if service exists
        if service_name not in MICROSERVICES:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
        
        # Build target URL
        target_url = f"{MICROSERVICES[service_name]}/{path}"
        
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
        
        # Remove problematic headers
        headers.pop('host', None)
        headers.pop('content-length', None)
        
        # Make request to target service
        async with httpx.AsyncClient(timeout=30.0) as client:
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
        raise HTTPException(status_code=500, detail=f"Proxy request failed: {str(e)}")

@app.get("/services/health")
async def get_services_health():
    """Get health status of all microservices"""
    try:
        health_status = {}
        
        for service_name, url in MICROSERVICES.items():
            try:
                start_time = time.time()
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{url}/healthz")
                response_time = (time.time() - start_time) * 1000
                
                health_status[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time_ms": response_time,
                    "last_check": datetime.now().isoformat()
                }
            except Exception as e:
                health_status[service_name] = {
                    "status": "unhealthy", 
                    "error": str(e),
                    "last_check": datetime.now().isoformat()
                }
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Get services health failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get services health failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)