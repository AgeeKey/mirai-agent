"""
Shared utilities for the web interface
"""

import logging
import os

# Adjust imports for the web module context
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app_root = Path(__file__).parent.parent
sys.path.insert(0, str(app_root))

from trader.risk_engine import get_risk_engine

logger = logging.getLogger(__name__)

# BasicAuth security
security = HTTPBasic()

# Global state for agent and mode
_agent_state = {
    "mode": "advisor",  # advisor, semi, auto
    "paused": False,
    "start_time": None,
    "errors_count": 0,
    "api_calls": 0,
    "last_decision": None,
}


def get_agent_state() -> Dict[str, Any]:
    """Get the global agent state"""
    import time

    if _agent_state["start_time"] is None:
        _agent_state["start_time"] = time.time()
    return _agent_state


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    """Verify BasicAuth credentials from environment variables"""
    web_user = os.getenv("WEB_USER")
    web_pass = os.getenv("WEB_PASS")

    if not web_user or not web_pass:
        logger.warning("WEB_USER or WEB_PASS not set in environment")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Web authentication not configured. Set WEB_USER and WEB_PASS environment variables.",
            headers={"WWW-Authenticate": "Basic"},
        )

    if credentials.username != web_user or credentials.password != web_pass:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


def get_safe_status_data() -> Dict[str, Any]:
    """Get status data with safe fallbacks"""
    agent_state = get_agent_state()

    try:
        risk_engine = get_risk_engine()
        now_utc = datetime.now(timezone.utc)
        day_state = risk_engine.get_day_state(now_utc)

        # Get advisor data from last decision if available
        last_decision = agent_state.get("last_decision")
        advisor_score = 0.0
        advisor_rationale = "No advisor data"
        advisor_strategy = "none"
        advisor_action = "HOLD"

        if last_decision and isinstance(last_decision, dict):
            advisor_score = last_decision.get("advisor_score", 0.0)
            advisor_rationale = last_decision.get("advisor_rationale", "No advisor data")
            advisor_strategy = last_decision.get("advisor_strategy", "none")
            advisor_action = last_decision.get("advisor_action", "HOLD")

        return {
            "date": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "mode": agent_state["mode"],
            "dayPnL": day_state.day_pnl,
            "maxDayPnL": day_state.max_day_pnl,
            "tradesToday": day_state.trades_today,
            "consecutiveLosses": day_state.consecutive_losses,
            "cooldownUntil": day_state.cooldown_until,
            "openPositions": [],  # Safe fallback - empty list
            "errorsCount": agent_state["errors_count"],
            "lastDecision": agent_state["last_decision"],
            "agentPaused": agent_state["paused"],
            "advisorScore": advisor_score,
            "advisorRationale": advisor_rationale,
            "advisorStrategy": advisor_strategy,
            "advisorAction": advisor_action,
        }
    except Exception as e:
        logger.warning(f"Error getting status data: {e}")
        return {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "mode": agent_state["mode"],
            "dayPnL": 0.0,
            "maxDayPnL": 0.0,
            "tradesToday": 0,
            "consecutiveLosses": 0,
            "cooldownUntil": None,
            "openPositions": [],
            "errorsCount": agent_state["errors_count"],
            "lastDecision": None,
            "agentPaused": agent_state["paused"],
            "advisorScore": 0.0,
            "advisorRationale": "Error getting advisor data",
            "advisorStrategy": "error",
            "advisorAction": "HOLD",
        }
