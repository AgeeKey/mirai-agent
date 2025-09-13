"""
FastAPI Web API for Mirai Agent
"""

import logging
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Adjust imports for the web module context
app_root = Path(__file__).parent.parent
sys.path.insert(0, str(app_root))

from trader.binance_client import BinanceClient
from trader.orders import OrderManager

from .ui import ui_router
from .utils import get_agent_state, get_safe_status_data, verify_credentials

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Mirai Web", description="Mirai Agent Web Interface", version="0.1.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include UI router
app.include_router(ui_router)


# Pydantic models for request bodies
class KillRequest(BaseModel):
    symbol: str


class ModeRequest(BaseModel):
    mode: str


@app.get("/status")
async def get_status():
    """Get current agent status"""
    agent_state = get_agent_state()
    agent_state["api_calls"] += 1
    return get_safe_status_data()


@app.post("/kill")
async def kill_switch(request: KillRequest, authorized: bool = Depends(verify_credentials)):
    """Trigger kill switch for a symbol"""
    agent_state = get_agent_state()
    agent_state["api_calls"] += 1

    try:
        symbol = request.symbol.upper()
        logger.info(f"Kill switch triggered for {symbol}")

        # Use existing kill switch logic (dry run mode)
        client = BinanceClient(dry_run=True, testnet=True)
        order_manager = OrderManager(client)

        # Cancel all orders
        order_manager.cancel_all_orders(symbol)

        # Close position
        order_manager.close_position(symbol)

        return {
            "success": True,
            "symbol": symbol,
            "message": f"Kill switch executed for {symbol}",
            "orders_cancelled": True,
            "position_closed": True,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        agent_state["errors_count"] += 1
        logger.error(f"Kill switch error: {e}")
        raise HTTPException(status_code=500, detail={"error": "Kill switch failed", "reason": str(e)}) from e


@app.get("/metrics")
async def get_metrics():
    """Get basic metrics"""
    agent_state = get_agent_state()
    agent_state["api_calls"] += 1
    uptime_sec = int(time.time() - agent_state["start_time"])

    return {
        "apiLatencyMs": 5,  # Placeholder
        "signalsPerMin": 0.5,  # Placeholder
        "riskBlocksToday": 0,  # Placeholder
        "openOrders": 0,  # Placeholder
        "uptimeSec": uptime_sec,
        "apiCalls": agent_state["api_calls"],
        "errorsCount": agent_state["errors_count"],
    }


@app.post("/mode")
async def change_mode(request: ModeRequest, authorized: bool = Depends(verify_credentials)):
    """Change trading mode"""
    agent_state = get_agent_state()
    agent_state["api_calls"] += 1

    valid_modes = ["advisor", "semi", "auto"]
    if request.mode not in valid_modes:
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid mode", "reason": f"Valid modes: {', '.join(valid_modes)}"},
        )

    old_mode = agent_state["mode"]
    agent_state["mode"] = request.mode

    logger.info(f"Trading mode changed from {old_mode} to {request.mode}")

    return {
        "success": True,
        "old_mode": old_mode,
        "new_mode": request.mode,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.post("/pause")
async def pause_agent(authorized: bool = Depends(verify_credentials)):
    """Pause the trading agent"""
    agent_state = get_agent_state()
    agent_state["api_calls"] += 1
    agent_state["paused"] = True

    logger.info("Agent paused via web interface")

    return {"success": True, "paused": True, "timestamp": datetime.now(UTC).isoformat()}


@app.post("/resume")
async def resume_agent(authorized: bool = Depends(verify_credentials)):
    """Resume the trading agent"""
    agent_state = get_agent_state()
    agent_state["api_calls"] += 1
    agent_state["paused"] = False

    logger.info("Agent resumed via web interface")

    return {"success": True, "paused": False, "timestamp": datetime.now(UTC).isoformat()}


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions with JSON response"""
    agent_state = get_agent_state()
    agent_state["errors_count"] += 1
    logger.error(f"Unhandled exception: {exc}")

    return JSONResponse(status_code=500, content={"error": "Internal server error", "reason": str(exc)})


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("WEB_PORT", 8000))
    uvicorn.run(app, host="127.0.0.1", port=port)
