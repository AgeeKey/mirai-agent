"""
Memory/Context management routes for Mirai API
"""
import json
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from .models import MemoryEntry, TradingDecision, User
from .auth import db_manager, get_current_active_user, require_role, UserRole

router = APIRouter(prefix="/api/memory", tags=["memory"])

@router.post("/entries")
async def create_memory_entry(
    entry: MemoryEntry,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new memory entry"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO memory_entries (user_id, context_type, content, metadata, relevance_score)
                VALUES (?, ?, ?, ?, ?)
            """, (
                current_user.id,
                entry.context_type,
                entry.content,
                json.dumps(entry.metadata) if entry.metadata else "{}",
                entry.relevance_score or 1.0
            ))
            
            entry_id = cursor.lastrowid
            conn.commit()
            
            return {"id": entry_id, "message": "Memory entry created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entries", response_model=List[MemoryEntry])
async def get_memory_entries(
    context_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    min_relevance: float = Query(0.0, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_active_user)
):
    """Get memory entries for current user"""
    try:
        with db_manager.get_connection() as conn:
            query = """
                SELECT * FROM memory_entries 
                WHERE user_id = ? AND relevance_score >= ?
            """
            params = [current_user.id, min_relevance]
            
            if context_type:
                query += " AND context_type = ?"
                params.append(context_type)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(query, params).fetchall()
            
            entries = []
            for row in rows:
                entries.append(MemoryEntry(
                    id=row['id'],
                    user_id=row['user_id'],
                    context_type=row['context_type'],
                    content=row['content'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    created_at=datetime.fromisoformat(row['created_at']),
                    relevance_score=row['relevance_score']
                ))
            
            return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entries/search")
async def search_memory_entries(
    query: str = Query(..., min_length=3),
    context_type: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """Search memory entries by content"""
    try:
        with db_manager.get_connection() as conn:
            search_query = """
                SELECT * FROM memory_entries 
                WHERE user_id = ? AND content LIKE ?
            """
            params = [current_user.id, f"%{query}%"]
            
            if context_type:
                search_query += " AND context_type = ?"
                params.append(context_type)
            
            search_query += " ORDER BY relevance_score DESC, created_at DESC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(search_query, params).fetchall()
            
            entries = []
            for row in rows:
                entries.append(MemoryEntry(
                    id=row['id'],
                    user_id=row['user_id'],
                    context_type=row['context_type'],
                    content=row['content'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    created_at=datetime.fromisoformat(row['created_at']),
                    relevance_score=row['relevance_score']
                ))
            
            return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/entries/{entry_id}")
async def delete_memory_entry(
    entry_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a memory entry"""
    try:
        with db_manager.get_connection() as conn:
            # Check if entry belongs to user or user is admin
            row = conn.execute(
                "SELECT user_id FROM memory_entries WHERE id = ?", (entry_id,)
            ).fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Memory entry not found")
            
            if row['user_id'] != current_user.id and current_user.role != UserRole.ADMIN:
                raise HTTPException(status_code=403, detail="Not authorized to delete this entry")
            
            conn.execute("DELETE FROM memory_entries WHERE id = ?", (entry_id,))
            conn.commit()
            
            return {"message": "Memory entry deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Trading decisions endpoints
@router.post("/trading-decisions")
async def record_trading_decision(
    decision: TradingDecision,
    current_user: User = Depends(require_role(UserRole.TRADER))
):
    """Record a trading decision"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO trading_decisions (symbol, action, reasoning, confidence, user_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                decision.symbol,
                decision.action,
                decision.reasoning,
                decision.confidence,
                current_user.id
            ))
            
            decision_id = cursor.lastrowid
            conn.commit()
            
            # Also create a memory entry for this decision
            memory_content = f"Trading decision: {decision.action} {decision.symbol} with {decision.confidence:.1%} confidence. Reasoning: {decision.reasoning}"
            
            conn.execute("""
                INSERT INTO memory_entries (user_id, context_type, content, metadata, relevance_score)
                VALUES (?, ?, ?, ?, ?)
            """, (
                current_user.id,
                "trading_decision",
                memory_content,
                json.dumps({
                    "decision_id": decision_id,
                    "symbol": decision.symbol,
                    "action": decision.action,
                    "confidence": decision.confidence
                }),
                decision.confidence  # Use confidence as relevance score
            ))
            conn.commit()
            
            return {"id": decision_id, "message": "Trading decision recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trading-decisions", response_model=List[TradingDecision])
async def get_trading_decisions(
    symbol: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user)
):
    """Get trading decisions history"""
    try:
        with db_manager.get_connection() as conn:
            query = """
                SELECT * FROM trading_decisions 
                WHERE user_id = ? AND created_at >= datetime('now', '-{} days')
            """.format(days)
            params = [current_user.id]
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            if action:
                query += " AND action = ?"
                params.append(action)
            
            query += " ORDER BY created_at DESC"
            
            rows = conn.execute(query, params).fetchall()
            
            decisions = []
            for row in rows:
                decisions.append(TradingDecision(
                    id=row['id'],
                    symbol=row['symbol'],
                    action=row['action'],
                    reasoning=row['reasoning'],
                    confidence=row['confidence'],
                    user_id=row['user_id'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    executed=bool(row['executed']),
                    result_pnl=row['result_pnl']
                ))
            
            return decisions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/trading-decisions/{decision_id}/result")
async def update_decision_result(
    decision_id: int,
    executed: bool,
    result_pnl: Optional[float] = None,
    current_user: User = Depends(require_role(UserRole.TRADER))
):
    """Update trading decision execution result"""
    try:
        with db_manager.get_connection() as conn:
            # Check if decision exists and belongs to user
            row = conn.execute(
                "SELECT user_id, symbol, action FROM trading_decisions WHERE id = ?", 
                (decision_id,)
            ).fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Trading decision not found")
            
            if row['user_id'] != current_user.id and current_user.role != UserRole.ADMIN:
                raise HTTPException(status_code=403, detail="Not authorized to update this decision")
            
            # Update decision
            conn.execute("""
                UPDATE trading_decisions 
                SET executed = ?, result_pnl = ?
                WHERE id = ?
            """, (executed, result_pnl, decision_id))
            conn.commit()
            
            # Create memory entry for result
            if executed and result_pnl is not None:
                result_text = "profit" if result_pnl > 0 else "loss"
                memory_content = f"Trading result: {row['action']} {row['symbol']} executed with ${result_pnl:.2f} {result_text}"
                
                conn.execute("""
                    INSERT INTO memory_entries (user_id, context_type, content, metadata, relevance_score)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    current_user.id,
                    "trading_result",
                    memory_content,
                    json.dumps({
                        "decision_id": decision_id,
                        "symbol": row['symbol'],
                        "action": row['action'],
                        "pnl": result_pnl
                    }),
                    0.8  # High relevance for actual results
                ))
                conn.commit()
            
            return {"message": "Trading decision result updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/context-types")
async def get_context_types(current_user: User = Depends(get_current_active_user)):
    """Get available context types for memory entries"""
    return {
        "context_types": [
            "trading_decision",
            "trading_result", 
            "user_preference",
            "conversation",
            "market_observation",
            "strategy_insight",
            "risk_assessment",
            "performance_note"
        ],
        "descriptions": {
            "trading_decision": "AI trading decisions and reasoning",
            "trading_result": "Results of executed trades",
            "user_preference": "User preferences and settings",
            "conversation": "Important conversation points",
            "market_observation": "Market insights and observations",
            "strategy_insight": "Strategy performance and insights",
            "risk_assessment": "Risk analysis and recommendations",
            "performance_note": "Performance tracking and notes"
        }
    }

@router.get("/stats")
async def get_memory_stats(current_user: User = Depends(get_current_active_user)):
    """Get memory usage statistics"""
    try:
        with db_manager.get_connection() as conn:
            # Get total entries by context type
            context_stats = conn.execute("""
                SELECT context_type, COUNT(*) as count
                FROM memory_entries 
                WHERE user_id = ?
                GROUP BY context_type
            """, (current_user.id,)).fetchall()
            
            # Get recent activity (last 7 days)
            recent_activity = conn.execute("""
                SELECT COUNT(*) as count
                FROM memory_entries 
                WHERE user_id = ? AND created_at >= datetime('now', '-7 days')
            """, (current_user.id,)).fetchone()
            
            # Get trading decisions stats
            trading_stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_decisions,
                    COUNT(CASE WHEN executed = 1 THEN 1 END) as executed_decisions,
                    AVG(CASE WHEN result_pnl IS NOT NULL THEN result_pnl END) as avg_pnl
                FROM trading_decisions 
                WHERE user_id = ?
            """, (current_user.id,)).fetchone()
            
            return {
                "total_entries": sum(row['count'] for row in context_stats),
                "entries_by_type": {row['context_type']: row['count'] for row in context_stats},
                "recent_activity_7d": recent_activity['count'],
                "trading_decisions": {
                    "total": trading_stats['total_decisions'],
                    "executed": trading_stats['executed_decisions'],
                    "avg_pnl": trading_stats['avg_pnl'] or 0
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))