"""
WebSocket Connection Manager
Phase 2: Backend Enhancement

Manages WebSocket connections for real-time updates
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from fastapi import WebSocket, WebSocketDisconnect
from app.core.auth import auth_service
from app.models.user import User

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket connection manager for handling real-time updates
    """
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, token: str):
        """
        Accept a new WebSocket connection and authenticate the user
        """
        try:
            # Verify the token
            payload = auth_service.token_manager.verify_token(token)
            if not payload or payload.get("sub") != user_id:
                await websocket.close(code=4001, reason="Invalid authentication")
                return False
            
            # Accept the connection
            await websocket.accept()
            
            # Add to active connections
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            
            self.active_connections[user_id].append(websocket)
            
            # Store metadata
            self.connection_metadata[websocket] = {
                "user_id": user_id,
                "connected_at": datetime.utcnow(),
                "last_ping": datetime.utcnow(),
            }
            
            logger.info(f"WebSocket connected for user {user_id}")
            
            # Send welcome message
            await self.send_personal_message({
                "type": "system_notification",
                "data": {
                    "message": "Connected to real-time updates",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            }, user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            await websocket.close(code=4000, reason="Connection failed")
            return False
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection
        """
        try:
            metadata = self.connection_metadata.get(websocket)
            if metadata:
                user_id = metadata["user_id"]
                
                # Remove from active connections
                if user_id in self.active_connections:
                    self.active_connections[user_id] = [
                        conn for conn in self.active_connections[user_id] 
                        if conn != websocket
                    ]
                    
                    # Clean up empty user entries
                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]
                
                # Remove metadata
                del self.connection_metadata[websocket]
                
                logger.info(f"WebSocket disconnected for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {e}")
    
    async def send_personal_message(self, message: Dict[str, Any], user_id: str):
        """
        Send a message to all connections for a specific user
        """
        if user_id not in self.active_connections:
            return
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        message_str = json.dumps(message)
        
        # Send to all user connections
        connections_to_remove = []
        
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.warning(f"Failed to send message to user {user_id}: {e}")
                connections_to_remove.append(websocket)
        
        # Clean up failed connections
        for websocket in connections_to_remove:
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected users
        """
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        message_str = json.dumps(message)
        
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)
    
    async def send_transcription_update(self, user_id: str, transcription_id: str, 
                                      status: str, progress: Optional[int] = None, 
                                      error: Optional[str] = None, result: Optional[Any] = None):
        """
        Send transcription status update to a specific user
        """
        update_message = {
            "type": "transcription_update",
            "data": {
                "transcription_id": transcription_id,
                "status": status,
                "progress": progress,
                "error": error,
                "result": result,
            }
        }
        
        await self.send_personal_message(update_message, user_id)
        logger.info(f"Sent transcription update to user {user_id}: {transcription_id} -> {status}")
    
    async def handle_message(self, websocket: WebSocket, data: str):
        """
        Handle incoming WebSocket messages
        """
        try:
            message = json.loads(data)
            message_type = message.get("type")
            
            metadata = self.connection_metadata.get(websocket)
            if not metadata:
                return
            
            user_id = metadata["user_id"]
            
            if message_type == "ping":
                # Update last ping time
                metadata["last_ping"] = datetime.utcnow()
                
                # Send pong response
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat(),
                }))
            
            elif message_type == "identify":
                # Client identification (already handled in connect)
                logger.info(f"Client identified: {user_id}")
            
            else:
                logger.warning(f"Unknown message type from user {user_id}: {message_type}")
        
        except json.JSONDecodeError:
            logger.error("Invalid JSON received from WebSocket")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    def get_connection_count(self) -> int:
        """
        Get total number of active connections
        """
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_user_connection_count(self, user_id: str) -> int:
        """
        Get number of connections for a specific user
        """
        return len(self.active_connections.get(user_id, []))
    
    async def cleanup_stale_connections(self):
        """
        Clean up stale connections (called periodically)
        """
        current_time = datetime.utcnow()
        stale_connections = []
        
        for websocket, metadata in self.connection_metadata.items():
            # Consider connection stale if no ping for 2 minutes
            if (current_time - metadata["last_ping"]).total_seconds() > 120:
                stale_connections.append(websocket)
        
        for websocket in stale_connections:
            try:
                await websocket.close(code=4002, reason="Connection timeout")
            except:
                pass
            self.disconnect(websocket)
        
        if stale_connections:
            logger.info(f"Cleaned up {len(stale_connections)} stale connections")


# Global connection manager instance
connection_manager = ConnectionManager()
