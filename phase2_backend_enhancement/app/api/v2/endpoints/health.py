"""
Health Check Endpoints
Phase 2: Backend Enhancement

Health monitoring endpoints for the FastAPI application
"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

@router.get("/ping")
async def ping() -> Dict[str, str]:
    """Simple ping endpoint"""
    return {"status": "ok", "message": "pong"}

@router.get("/status")
async def status() -> Dict[str, Any]:
    """Basic status endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "service": "iam-saas-api"
    }
