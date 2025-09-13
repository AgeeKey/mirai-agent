import os
from datetime import datetime, timedelta, timezone

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

app = FastAPI(title="Mirai API")

# Security
security = HTTPBearer()

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 12


# Auth Models
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class User(BaseModel):
    username: str
    role: str = "admin"


# Authentication utilities
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(payload: dict = Depends(verify_token)) -> User:
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return User(username=username)


# Health endpoints
@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "mirai-api"}


@app.head("/healthz")
def healthz_head():
    return Response(status_code=200)


# Authentication endpoints
@app.post("/auth/login", response_model=LoginResponse)
def login(login_data: LoginRequest):
    """Login with username and password"""
    web_user = os.getenv("WEB_USER")
    web_pass = os.getenv("WEB_PASS")

    if not web_user or not web_pass:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication not configured")

    if login_data.username != web_user or login_data.password != web_pass:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": login_data.username})
    return LoginResponse(access_token=access_token)


@app.get("/auth/me", response_model=User)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user


# Status endpoints
@app.get("/status")
def get_status(current_user: User = Depends(get_current_user)):
    """Get system status and bot information"""
    return {
        "mode": os.getenv("DRY_RUN", "true").lower() == "true" and "DRY_RUN" or "LIVE",
        "testnet": os.getenv("USE_TESTNET", "true").lower() == "true",
        "uptime": "Running",  # Could be calculated from start time
        "version": os.getenv("TAG", "latest"),
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


# Risk configuration endpoints
@app.get("/risk/config")
def get_risk_config(current_user: User = Depends(get_current_user)):
    """Get risk configuration"""
    # This would read from configs/risk.yaml in a real implementation
    return {
        "MAX_TRADES_PER_DAY": 10,
        "COOLDOWN_SEC": 300,
        "DAILY_MAX_LOSS_USDT": 100.0,
        "DAILY_TRAIL_DRAWDOWN": 0.05,
        "ADVISOR_THRESHOLD": 0.6,
    }


@app.patch("/risk/config")
def update_risk_config(config_update: dict, current_user: User = Depends(get_current_user)):
    """Update risk configuration"""
    # In a real implementation, this would:
    # 1. Validate the config_update
    # 2. Update the YAML file
    # 3. Signal the trader to reload config
    # For now, return the updated config
    current_config = {
        "MAX_TRADES_PER_DAY": 10,
        "COOLDOWN_SEC": 300,
        "DAILY_MAX_LOSS_USDT": 100.0,
        "DAILY_TRAIL_DRAWDOWN": 0.05,
        "ADVISOR_THRESHOLD": 0.6,
    }
    current_config.update(config_update)
    return current_config


# Orders endpoints
@app.get("/orders/recent")
def get_recent_orders(limit: int = 50, current_user: User = Depends(get_current_user)):
    """Get recent orders"""
    # This would read from the trader's order storage
    return {"orders": [], "total": 0, "limit": limit}


@app.get("/orders/active")
def get_active_orders(current_user: User = Depends(get_current_user)):
    """Get active orders"""
    # This would read from the trader's active orders
    return {"orders": [], "total": 0}


# Logs endpoint
@app.get("/logs/tail")
def get_logs_tail(lines: int = 100, current_user: User = Depends(get_current_user)):
    """Get recent log lines"""
    # This would read from log files
    return {"logs": ["No logs available"], "lines": lines}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("WEB_PORT", "8000")))
