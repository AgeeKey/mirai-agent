"""
Admin routes for Mirai API
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta

from .models import User, UserCreate, UserUpdate
from .auth import db_manager, require_role, UserRole, get_current_active_user

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/users", response_model=List[User])
async def get_all_users(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Get all users (admin only)"""
    try:
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
            
            users = []
            for row in rows:
                users.append(User(
                    id=row['id'],
                    username=row['username'],
                    email=row['email'],
                    role=row['role'],
                    is_active=bool(row['is_active']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None
                ))
            
            return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Update user (admin only)"""
    try:
        # Get existing user
        existing_user = db_manager.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        with db_manager.get_connection() as conn:
            # Build update query dynamically
            updates = []
            params = []
            
            if user_update.username is not None:
                updates.append("username = ?")
                params.append(user_update.username)
            
            if user_update.email is not None:
                updates.append("email = ?")
                params.append(user_update.email)
            
            if user_update.role is not None:
                updates.append("role = ?")
                params.append(user_update.role.value)
            
            if user_update.is_active is not None:
                updates.append("is_active = ?")
                params.append(user_update.is_active)
            
            if user_update.password is not None:
                from .auth import get_password_hash
                updates.append("password_hash = ?")
                params.append(get_password_hash(user_update.password))
            
            if updates:
                params.append(user_id)
                query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
                conn.execute(query, params)
                conn.commit()
            
            return {"message": "User updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Delete user (admin only)"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    try:
        with db_manager.get_connection() as conn:
            # Check if user exists
            existing_user = db_manager.get_user_by_id(user_id)
            if not existing_user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Delete user and related data
            conn.execute("DELETE FROM memory_entries WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM trading_decisions WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM blog_posts WHERE author_id = ?", (user_id,))
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            
            return {"message": f"User {existing_user.username} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_admin_stats(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Get system statistics (admin only)"""
    try:
        with db_manager.get_connection() as conn:
            # User stats
            user_stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_users,
                    COUNT(CASE WHEN role = 'admin' THEN 1 END) as admin_users,
                    COUNT(CASE WHEN role = 'trader' THEN 1 END) as trader_users,
                    COUNT(CASE WHEN role = 'viewer' THEN 1 END) as viewer_users
                FROM users
            """).fetchone()
            
            # Blog stats
            blog_stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_posts,
                    COUNT(CASE WHEN is_published = 1 THEN 1 END) as published_posts,
                    COUNT(CASE WHEN ai_generated = 1 THEN 1 END) as ai_posts,
                    SUM(view_count) as total_views
                FROM blog_posts
            """).fetchone()
            
            # Memory stats
            memory_stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    COUNT(DISTINCT user_id) as users_with_memory,
                    AVG(relevance_score) as avg_relevance
                FROM memory_entries
            """).fetchone()
            
            # Trading decisions stats
            trading_stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_decisions,
                    COUNT(CASE WHEN executed = 1 THEN 1 END) as executed_decisions,
                    AVG(confidence) as avg_confidence,
                    AVG(CASE WHEN result_pnl IS NOT NULL THEN result_pnl END) as avg_pnl
                FROM trading_decisions
            """).fetchone()
            
            # Recent activity (last 7 days)
            recent_activity = conn.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM users WHERE created_at >= datetime('now', '-7 days')) as new_users,
                    (SELECT COUNT(*) FROM blog_posts WHERE created_at >= datetime('now', '-7 days')) as new_posts,
                    (SELECT COUNT(*) FROM memory_entries WHERE created_at >= datetime('now', '-7 days')) as new_memories,
                    (SELECT COUNT(*) FROM trading_decisions WHERE created_at >= datetime('now', '-7 days')) as new_decisions
            """).fetchone()
            
            return {
                "users": {
                    "total": user_stats['total_users'],
                    "active": user_stats['active_users'],
                    "by_role": {
                        "admin": user_stats['admin_users'],
                        "trader": user_stats['trader_users'],
                        "viewer": user_stats['viewer_users']
                    }
                },
                "blog": {
                    "total_posts": blog_stats['total_posts'],
                    "published_posts": blog_stats['published_posts'],
                    "ai_generated": blog_stats['ai_posts'],
                    "total_views": blog_stats['total_views'] or 0
                },
                "memory": {
                    "total_entries": memory_stats['total_entries'],
                    "users_with_memory": memory_stats['users_with_memory'],
                    "avg_relevance": round(memory_stats['avg_relevance'] or 0, 2)
                },
                "trading": {
                    "total_decisions": trading_stats['total_decisions'],
                    "executed_decisions": trading_stats['executed_decisions'],
                    "avg_confidence": round(trading_stats['avg_confidence'] or 0, 2),
                    "avg_pnl": round(trading_stats['avg_pnl'] or 0, 2)
                },
                "recent_activity_7d": {
                    "new_users": recent_activity['new_users'],
                    "new_posts": recent_activity['new_posts'],
                    "new_memories": recent_activity['new_memories'],
                    "new_decisions": recent_activity['new_decisions']
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def system_health(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Get system health status (admin only)"""
    try:
        with db_manager.get_connection() as conn:
            # Check database connectivity
            conn.execute("SELECT 1").fetchone()
            
            # Get database file size
            import os
            db_size = os.path.getsize(db_manager.db_path) / (1024 * 1024)  # MB
            
            # Check table counts
            table_counts = {}
            tables = ["users", "blog_posts", "memory_entries", "trading_decisions"]
            for table in tables:
                count = conn.execute(f"SELECT COUNT(*) as count FROM {table}").fetchone()
                table_counts[table] = count['count']
            
            return {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "size_mb": round(db_size, 2),
                    "table_counts": table_counts
                },
                "system": {
                    "timestamp": datetime.now().isoformat(),
                    "uptime": "System operational"  # Would be actual uptime in production
                }
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }