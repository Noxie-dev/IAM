"""
WebSocket Endpoints
Phase 2: Backend Enhancement

Real-time WebSocket connections for transcription updates
"""

import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from app.services.websocket_manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time updates
    
    Query Parameters:
    - token: JWT authentication token
    - user_id: User ID for the connection
    """
    
    if not token or not user_id:
        await websocket.close(code=4000, reason="Missing authentication parameters")
        return
    
    # Attempt to connect
    connected = await connection_manager.connect(websocket, user_id, token)
    
    if not connected:
        return
    
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            
            # Handle the message
            await connection_manager.handle_message(websocket, data)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        # Clean up the connection
        connection_manager.disconnect(websocket)


@router.get("/ws/status")
async def websocket_status():
    """
    Get WebSocket connection status
    """
    return {
        "total_connections": connection_manager.get_connection_count(),
        "active_users": len(connection_manager.active_connections),
        "status": "healthy"
    }


@router.post("/ws/test/{user_id}")
async def test_websocket_message(user_id: str):
    """
    Test endpoint to send a WebSocket message to a specific user
    """
    await connection_manager.send_personal_message({
        "type": "system_notification",
        "data": {
            "message": "Test message from backend!",
            "timestamp": "2025-08-26T18:45:00Z"
        }
    }, user_id)

    return {"message": f"Test message sent to user {user_id}"}
