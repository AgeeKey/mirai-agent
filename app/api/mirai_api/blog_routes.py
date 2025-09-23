"""
Blog/CMS routes for Mirai API
"""
import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from .models import BlogPost, BlogPostCreate, BlogPostUpdate, User
from .auth import db_manager, get_current_active_user, require_role, UserRole

router = APIRouter(prefix="/api/blog", tags=["blog"])

@router.post("/posts", response_model=BlogPost)
async def create_blog_post(
    post_data: BlogPostCreate,
    current_user: User = Depends(require_role(UserRole.TRADER))
):
    """Create a new blog post"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO blog_posts (title, content, summary, tags, is_published, ai_generated, author_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                post_data.title,
                post_data.content,
                post_data.summary,
                json.dumps(post_data.tags) if post_data.tags else "[]",
                post_data.is_published,
                post_data.ai_generated,
                current_user.id
            ))
            
            post_id = cursor.lastrowid
            conn.commit()
            
            return get_blog_post_by_id(post_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/posts", response_model=List[BlogPost])
async def get_blog_posts(
    published_only: bool = Query(True, description="Only show published posts"),
    limit: int = Query(10, le=100),
    offset: int = Query(0, ge=0),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)")
):
    """Get blog posts with filtering"""
    try:
        with db_manager.get_connection() as conn:
            query = "SELECT * FROM blog_posts"
            params = []
            conditions = []
            
            if published_only:
                conditions.append("is_published = 1")
            
            if tags:
                tag_list = [tag.strip() for tag in tags.split(",")]
                tag_conditions = []
                for tag in tag_list:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")
                if tag_conditions:
                    conditions.append(f"({' OR '.join(tag_conditions)})")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            rows = conn.execute(query, params).fetchall()
            
            posts = []
            for row in rows:
                posts.append(BlogPost(
                    id=row['id'],
                    title=row['title'],
                    content=row['content'],
                    summary=row['summary'],
                    tags=json.loads(row['tags']) if row['tags'] else [],
                    is_published=bool(row['is_published']),
                    ai_generated=bool(row['ai_generated']),
                    author_id=row['author_id'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
                    view_count=row['view_count']
                ))
            
            return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/posts/{post_id}", response_model=BlogPost)
async def get_blog_post(post_id: int):
    """Get a specific blog post"""
    post = get_blog_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Increment view count
    try:
        with db_manager.get_connection() as conn:
            conn.execute(
                "UPDATE blog_posts SET view_count = view_count + 1 WHERE id = ?",
                (post_id,)
            )
            conn.commit()
    except:
        pass  # Don't fail if view count update fails
    
    return post

@router.put("/posts/{post_id}", response_model=BlogPost)
async def update_blog_post(
    post_id: int,
    post_update: BlogPostUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update a blog post"""
    # Get existing post
    existing_post = get_blog_post_by_id(post_id)
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check permissions (author or admin)
    if existing_post.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to edit this post")
    
    try:
        with db_manager.get_connection() as conn:
            # Build update query dynamically
            updates = []
            params = []
            
            if post_update.title is not None:
                updates.append("title = ?")
                params.append(post_update.title)
            
            if post_update.content is not None:
                updates.append("content = ?")
                params.append(post_update.content)
            
            if post_update.summary is not None:
                updates.append("summary = ?")
                params.append(post_update.summary)
            
            if post_update.tags is not None:
                updates.append("tags = ?")
                params.append(json.dumps(post_update.tags))
            
            if post_update.is_published is not None:
                updates.append("is_published = ?")
                params.append(post_update.is_published)
            
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(post_id)
                
                query = f"UPDATE blog_posts SET {', '.join(updates)} WHERE id = ?"
                conn.execute(query, params)
                conn.commit()
            
            return get_blog_post_by_id(post_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/posts/{post_id}")
async def delete_blog_post(
    post_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a blog post"""
    # Get existing post
    existing_post = get_blog_post_by_id(post_id)
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check permissions (author or admin)
    if existing_post.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    
    try:
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM blog_posts WHERE id = ?", (post_id,))
            conn.commit()
        
        return {"message": "Post deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/posts/ai-generate")
async def ai_generate_post(
    topic: str,
    current_user: User = Depends(require_role(UserRole.TRADER))
):
    """Generate AI blog post about trading topic"""
    # Simulate AI content generation
    ai_content = f"""
# AI-Generated Trading Insights: {topic}

## Market Analysis

Based on current market conditions and AI analysis, here are key insights about {topic}:

### Technical Indicators
- Moving averages show {["bullish", "bearish", "neutral"][hash(topic) % 3]} trends
- RSI levels indicate {["oversold", "overbought", "balanced"][hash(topic) % 3]} conditions
- Volume analysis suggests {["increased", "decreased", "stable"][hash(topic) % 3]} interest

### AI Recommendations
1. Consider position sizing based on current volatility
2. Monitor key support/resistance levels
3. Implement risk management strategies

### Risk Assessment
The AI model assigns a confidence score of {85 + (hash(topic) % 15)}% to this analysis.

*This content was generated by Mirai AI at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

    # Create blog post
    post_data = BlogPostCreate(
        title=f"AI Trading Analysis: {topic}",
        content=ai_content,
        summary=f"AI-generated insights and analysis for {topic} trading opportunities",
        tags=["ai-generated", "trading", "analysis", topic.lower().replace(" ", "-")],
        is_published=False,  # Let user review before publishing
        ai_generated=True
    )
    
    return await create_blog_post(post_data, current_user)

def get_blog_post_by_id(post_id: int) -> Optional[BlogPost]:
    """Helper function to get blog post by ID"""
    try:
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM blog_posts WHERE id = ?", (post_id,)).fetchone()
            
            if row:
                return BlogPost(
                    id=row['id'],
                    title=row['title'],
                    content=row['content'],
                    summary=row['summary'],
                    tags=json.loads(row['tags']) if row['tags'] else [],
                    is_published=bool(row['is_published']),
                    ai_generated=bool(row['ai_generated']),
                    author_id=row['author_id'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
                    view_count=row['view_count']
                )
    except Exception:
        pass
    
    return None