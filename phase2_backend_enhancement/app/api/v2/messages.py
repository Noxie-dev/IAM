"""
Message API Router
Phase 2: Backend Enhancement

Simplified FastAPI router for message operations with WebSocket support
"""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import structlog

from ..core.database import get_db
from ..schemas import message as message_schema
from ..services import message_service, websocket_manager
from ..core.auth import get_current_active_user
from ..models.user import User

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.get("/", response_model=List[message_schema.MessageRead])
def get_user_messages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve all messages for the current user."""
    try:
        messages = message_service.get_messages_for_user(db, user_id=current_user.id)
        return messages
    except Exception as e:
        logger.error("Error fetching messages", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch messages"
        )


@router.get("/{message_id}", response_model=message_schema.MessageRead)
def get_message(
    message_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific message by ID."""
    try:
        message = message_service.get_message(db, message_id=message_id, user_id=current_user.id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        return message
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching message", error=str(e), message_id=str(message_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch message"
        )


@router.post("/", response_model=message_schema.MessageRead, status_code=201)
async def send_message(
    message: message_schema.MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Send a new message to another user."""
    try:
        new_message = message_service.create_message(
            db, 
            sender_id=current_user.id, 
            message_data=message
        )
        
        # Convert to response model
        message_response = message_schema.MessageRead.from_orm(new_message)
        
        # Send real-time update to recipient
        await websocket_manager.send_personal_message(
            {
                "type": "new_message", 
                "data": message_response.dict()
            },
            recipient_id=str(new_message.recipient_id)
        )
        
        logger.info(
            "Message sent successfully",
            sender_id=str(current_user.id),
            recipient_id=str(message.recipient_id),
            message_id=str(new_message.id)
        )
        
        return message_response
        
    except Exception as e:
        logger.error("Error sending message", error=str(e), sender_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )


@router.patch("/{message_id}", response_model=message_schema.MessageRead)
def update_message_status(
    message_id: uuid.UUID,
    update_data: message_schema.MessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update message status (read, starred)."""
    try:
        updated_message = message_service.update_message(
            db,
            message_id=message_id,
            user_id=current_user.id,
            update_data=update_data
        )
        
        if not updated_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or access denied"
            )
        
        return updated_message
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating message", error=str(e), message_id=str(message_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update message"
        )


@router.delete("/{message_id}", status_code=204)
def delete_message(
    message_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a message."""
    try:
        success = message_service.delete_message(
            db,
            message_id=message_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or access denied"
            )
        
        logger.info("Message deleted", message_id=str(message_id), user_id=str(current_user.id))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting message", error=str(e), message_id=str(message_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete message"
        )


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        """Connect a user to WebSocket."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info("WebSocket connected", user_id=user_id)

    def disconnect(self, user_id: str):
        """Disconnect a user from WebSocket."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info("WebSocket disconnected", user_id=user_id)

    async def send_personal_message(self, message: dict, recipient_id: str):
        """Send a message to a specific user."""
        if recipient_id in self.active_connections:
            try:
                websocket = self.active_connections[recipient_id]
                await websocket.send_json(message)
                logger.debug("WebSocket message sent", recipient_id=recipient_id)
            except Exception as e:
                logger.error("Error sending WebSocket message", error=str(e), recipient_id=recipient_id)
                # Remove broken connection
                self.disconnect(recipient_id)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected users."""
        disconnected_users = []
        
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error("Error broadcasting message", error=str(e), user_id=user_id)
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)


# Global WebSocket manager instance
websocket_manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time updates."""
    await websocket_manager.connect(user_id, websocket)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "user_id": user_id,
            "message": "Connected to message service"
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for any message (ping/pong or other)
                data = await websocket.receive_text()
                
                # Handle ping messages
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", user_id=user_id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e), user_id=user_id)
    finally:
        websocket_manager.disconnect(user_id)


# Health check endpoint
@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "message-api",
        "websocket_connections": len(websocket_manager.active_connections)
    }
