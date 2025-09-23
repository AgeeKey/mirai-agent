# Mirai Backend API
from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import asyncio
import json
import uuid
import logging
from typing import List, Optional, Dict, Any
import redis
# import aioredis
from contextlib import asynccontextmanager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DATABASE_URL = "sqlite:///./mirai.db"  # В продакшн заменить на PostgreSQL

# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connection established. Total: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed. Total: {len(self.active_connections)}")
        
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
        
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

manager = ConnectionManager()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    api_key = Column(String, unique=True, default=lambda: str(uuid.uuid4()))

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    symbol = Column(String, index=True)
    side = Column(String)  # "LONG" или "SHORT"
    size = Column(Float)
    entry_price = Column(Float)
    current_price = Column(Float)
    pnl = Column(Float)
    pnl_percentage = Column(Float)
    status = Column(String, default="OPEN")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class TradingSignal(Base):
    __tablename__ = "trading_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    signal_type = Column(String)  # "BUY" или "SELL"
    confidence = Column(Float)
    price = Column(Float)
    reasoning = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_executed = Column(Boolean, default=False)

class TradingStats(Base):
    __tablename__ = "trading_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    total_balance = Column(Float, default=100000.0)
    daily_pnl = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    
    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.isalnum(), 'Username must be alphanumeric'
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_premium: bool
    created_at: datetime
    api_key: str
    
    class Config:
        from_attributes = True

class PositionResponse(BaseModel):
    id: int
    symbol: str
    side: str
    size: float
    entry_price: float
    current_price: float
    pnl: float
    pnl_percentage: float
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TradingSignalResponse(BaseModel):
    id: int
    symbol: str
    signal_type: str
    confidence: float
    price: float
    reasoning: str
    timestamp: datetime
    is_executed: bool
    
    class Config:
        from_attributes = True

class TradingStatsResponse(BaseModel):
    total_balance: float
    daily_pnl: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    updated_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Create tables
Base.metadata.create_all(bind=engine)

# Utility functions
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Mock data generators
def generate_mock_positions(user_id: int = 1) -> List[dict]:
    """Генерирует тестовые позиции для демонстрации"""
    import random
    positions = [
        {
            "symbol": "BTC/USDT",
            "side": "LONG",
            "size": 0.25,
            "entry_price": 67250.0,
            "current_price": 68100.0,
            "pnl": 212.50,
            "pnl_percentage": 1.26
        },
        {
            "symbol": "ETH/USDT", 
            "side": "SHORT",
            "size": 5.0,
            "entry_price": 3420.0,
            "current_price": 3385.0,
            "pnl": 175.0,
            "pnl_percentage": 1.02
        },
        {
            "symbol": "SOL/USDT",
            "side": "LONG", 
            "size": 15.0,
            "entry_price": 185.50,
            "current_price": 189.20,
            "pnl": 55.50,
            "pnl_percentage": 1.99
        }
    ]
    return positions

def generate_mock_signals() -> List[dict]:
    """Генерирует тестовые торговые сигналы"""
    signals = [
        {
            "symbol": "BTC/USDT",
            "signal_type": "BUY",
            "confidence": 95.0,
            "price": 68150.0,
            "reasoning": "Пробой ключевого уровня сопротивления, объемы растут",
            "timestamp": datetime.utcnow() - timedelta(minutes=4)
        },
        {
            "symbol": "ETH/USDT",
            "signal_type": "SELL", 
            "confidence": 87.0,
            "price": 3380.0,
            "reasoning": "Медвежья дивергенция на RSI, снижение объемов",
            "timestamp": datetime.utcnow() - timedelta(minutes=8)
        },
        {
            "symbol": "ADA/USDT",
            "signal_type": "BUY",
            "confidence": 92.0, 
            "price": 0.485,
            "reasoning": "Формирование восходящего треугольника, готовность к пробою",
            "timestamp": datetime.utcnow() - timedelta(minutes=11)
        }
    ]
    return signals

# FastAPI app initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Mirai Trading API...")
    
    # Создаем тестового пользователя если его нет
    db = SessionLocal()
    test_user = db.query(User).filter(User.username == "demo").first()
    if not test_user:
        test_user = User(
            username="demo",
            email="demo@aimirai.info",
            hashed_password=get_password_hash("demo123"),
            is_active=True,
            is_premium=True
        )
        db.add(test_user)
        db.commit()
        logger.info("Created demo user")
    db.close()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Mirai Trading API...")

app = FastAPI(
    title="Mirai Trading API",
    description="AI-Powered Autonomous Trading Platform API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://aimirai.info", "https://aimirai.online", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["aimirai.info", "aimirai.online", "localhost", "127.0.0.1"]
)

# Routes
@app.get("/")
async def root():
    return {
        "message": "Mirai Trading API v2.0.0",
        "status": "active",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "auth": "/auth/*",
            "trading": "/trading/*",
            "analytics": "/analytics/*",
            "websocket": "/ws"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {
            "database": "connected",
            "api": "operational",
            "websocket": "active",
            "trading_engine": "running"
        }
    }