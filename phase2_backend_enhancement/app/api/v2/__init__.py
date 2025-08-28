"""
API v2 Router
Phase 2: Backend Enhancement

Main API router for version 2 endpoints
"""

from fastapi import APIRouter

from app.api.v2.endpoints import auth, users, meetings, transcription, health, websocket

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

api_router.include_router(
    meetings.router,
    prefix="/meetings",
    tags=["Meetings"]
)

api_router.include_router(
    transcription.router,
    prefix="/transcription",
    tags=["Transcription"]
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"]
)

# WebSocket endpoints (no prefix needed for /ws)
api_router.include_router(
    websocket.router,
    tags=["WebSocket"]
)

__all__ = ["api_router"]
