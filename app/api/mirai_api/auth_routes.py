"""
Authentication routes for Mirai API
"""
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from .models import User, UserCreate, Token, LoginForm
from .auth import (
    db_manager, create_access_token, 
    get_current_active_user, require_role, UserRole,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.post("/register", response_model=User)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    # Check if user already exists
    existing_user = db_manager.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Create user
    user = db_manager.create_user(user_data)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Could not create user"
        )
    
    return user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user and return JWT token"""
    user = db_manager.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/login/form", response_model=Token)
async def login_form(login_data: LoginForm):
    """Login via JSON form data"""
    user = db_manager.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@router.get("/verify")
async def verify_token(current_user: User = Depends(get_current_active_user)):
    """Verify if token is valid"""
    return {"valid": True, "user": current_user.username, "role": current_user.role}

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout user (client should remove token)"""
    return {"message": "Successfully logged out"}

# Protected endpoints examples
@router.get("/admin-only")
async def admin_only(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Admin-only endpoint"""
    return {"message": "This is admin-only content", "user": current_user.username}

@router.get("/trader-plus")
async def trader_plus(current_user: User = Depends(require_role(UserRole.TRADER))):
    """Trader+ role required"""
    return {"message": "This requires trader role or higher", "user": current_user.username}