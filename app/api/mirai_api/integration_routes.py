"""
Integration routes between FastAPI backend and external Flask site (aimirai.info)
Provides health proxy, status aggregation, and cross-links.
"""
from fastapi import APIRouter
import os
import requests

router = APIRouter(prefix="/api/integration", tags=["integration"]) 

AIMIRAI_BASE = os.getenv("AIMIRAI_BASE", "http://aimirai.info")

@router.get("/health")
def integration_health():
    return {"status": "ok", "aimirai_base": AIMIRAI_BASE}

@router.get("/aimirai/health")
def aimirai_health():
    try:
        r = requests.get(f"{AIMIRAI_BASE}/healthz", timeout=3)
        return {"up": r.ok, "status": r.text[:200]}
    except Exception as e:
        return {"up": False, "error": str(e)}

@router.get("/status")
def combined_status():
    # Placeholder combined status for now
    return {
        "backend": {"status": "running"},
        "frontend": {"status": "unknown"},
        "aimirai": aimirai_health(),
    }
