"""
Database models for Mirai API
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    TRADER = "trader"
    VIEWER = "viewer"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.VIEWER
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None

class LoginForm(BaseModel):
    username: str
    password: str

# Blog/CMS models
class BlogPostBase(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    tags: Optional[List[str]] = []
    is_published: bool = False
    ai_generated: bool = False

class BlogPostCreate(BlogPostBase):
    pass

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    is_published: Optional[bool] = None

class BlogPost(BlogPostBase):
    id: int
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    view_count: int = 0
    
    class Config:
        from_attributes = True

# Memory/Context models
class MemoryEntry(BaseModel):
    id: Optional[int] = None
    user_id: int
    context_type: str  # "trading_decision", "user_preference", "conversation"
    content: str
    metadata: Optional[dict] = {}
    created_at: Optional[datetime] = None
    relevance_score: Optional[float] = 1.0

class TradingDecision(BaseModel):
    id: Optional[int] = None
    symbol: str
    action: str  # "buy", "sell", "hold"
    reasoning: str
    confidence: float
    user_id: int
    created_at: Optional[datetime] = None
    executed: bool = False
    result_pnl: Optional[float] = None

# Voice command models
class VoiceCommand(BaseModel):
    command: str
    intent: str
    parameters: Optional[dict] = {}
    user_id: int

class VoiceResponse(BaseModel):
    response_text: str
    action_taken: Optional[str] = None
    data: Optional[dict] = {}