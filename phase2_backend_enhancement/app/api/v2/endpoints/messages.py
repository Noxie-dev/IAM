"""
Message API Endpoints
Phase 2: Backend Enhancement

FastAPI endpoints for inbox feature with real-time support
"""

import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.message import Message
from app.models.notification import Notification
from app.schemas.message import (
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    MessageWithUsers,
    MessageListResponse,
    BulkMessageUpdate,
    BulkMessageResponse,
    NotificationResponse,
    NotificationWithMessage,
    NotificationListResponse,
    BulkNotificationUpdate,
    MessageStats,
    NotificationStats,
    MessageError,
    ValidationError
)
from app.services.websocket import WebSocketManager
from app.core.redis_client import redis_client
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])

# WebSocket manager for real-time updates
websocket_manager = WebSocketManager()


@router.get("/", response_model=MessageListResponse)
async def get_messages(
    folder: str = Query("inbox", description="Message folder"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    unread_only: bool = Query(False, description="Show only unread messages"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get messages for the current user with filtering and pagination
    """
    try:
        # Build base query based on folder
        if folder == "inbox":
            base_query = select(Message).where(
                and_(
                    Message.recipient_id == current_user.id,
                    Message.is_archived == False
                )
            )
        elif folder == "sent":
            base_query = select(Message).where(
                and_(
                    Message.sender_id == current_user.id,
                    Message.is_archived == False
                )
            )
        elif folder == "starred":
            base_query = select(Message).where(
                and_(
                    or_(
                        Message.recipient_id == current_user.id,
                        Message.sender_id == current_user.id
                    ),
                    Message.is_starred == True,
                    Message.is_archived == False
                )
            )
        elif folder == "archived":
            base_query = select(Message).where(
                and_(
                    or_(
                        Message.recipient_id == current_user.id,
                        Message.sender_id == current_user.id
                    ),
                    Message.is_archived == True
                )
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid folder parameter"
            )
        
        # Add unread filter if requested
        if unread_only:
            base_query = base_query.where(Message.is_read == False)
        
        # Add relationships and ordering
        query = base_query.options(
            selectinload(Message.sender),
            selectinload(Message.recipient)
        ).order_by(Message.created_at.desc())
        
        # Execute query with pagination
        result = await db.execute(query)
        messages = result.scalars().all()
        
        # Manual pagination
        total = len(messages)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_messages = messages[start_idx:end_idx]
        
        # Convert to response format
        message_responses = [
            MessageWithUsers(
                id=msg.id,
                sender_id=msg.sender_id,
                recipient_id=msg.recipient_id,
                subject=msg.subject,
                body=msg.body,
                is_read=msg.is_read,
                is_starred=msg.is_starred,
                is_archived=msg.is_archived,
                created_at=msg.created_at,
                updated_at=msg.updated_at,
                sender=msg.sender.to_dict() if msg.sender else None,
                recipient=msg.recipient.to_dict() if msg.recipient else None
            ) for msg in paginated_messages
        ]
        
        return MessageListResponse(
            messages=message_responses,
            pagination={
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page,
                "has_next": end_idx < total,
                "has_prev": page > 1
            }
        )
        
    except Exception as e:
        logger.error("Error fetching messages", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch messages"
        )


@router.get("/{message_id}", response_model=MessageWithUsers)
async def get_message(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific message by ID
    """
    try:
        query = select(Message).options(
            selectinload(Message.sender),
            selectinload(Message.recipient)
        ).where(Message.id == message_id)
        
        result = await db.execute(query)
        message = result.scalar_one_or_none()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Check if user has access to this message
        if message.sender_id != current_user.id and message.recipient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Mark as read if recipient is viewing
        if message.recipient_id == current_user.id and not message.is_read:
            message.is_read = True
            await db.commit()
            
            # Send real-time update
            await websocket_manager.broadcast_to_user(
                current_user.id,
                "message_read",
                {"message_id": str(message_id)}
            )
        
        return MessageWithUsers(
            id=message.id,
            sender_id=message.sender_id,
            recipient_id=message.recipient_id,
            subject=message.subject,
            body=message.body,
            is_read=message.is_read,
            is_starred=message.is_starred,
            is_archived=message.is_archived,
            created_at=message.created_at,
            updated_at=message.updated_at,
            sender=message.sender.to_dict() if message.sender else None,
            recipient=message.recipient.to_dict() if message.recipient else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching message", error=str(e), message_id=message_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch message"
        )


@router.post("/", response_model=MessageWithUsers, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new message
    """
    try:
        # Validate recipient exists
        recipient_query = select(User).where(User.id == message_data.recipient_id)
        result = await db.execute(recipient_query)
        recipient = result.scalar_one_or_none()
        
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipient not found"
            )
        
        # Create message
        message = Message(
            sender_id=current_user.id,
            recipient_id=message_data.recipient_id,
            subject=message_data.subject,
            body=message_data.body
        )
        
        db.add(message)
        await db.commit()
        await db.refresh(message)
        
        # Load relationships
        await db.refresh(message, ["sender", "recipient"])
        
        # Create notification for recipient
        notification = Notification.create_message_notification(
            user_id=message_data.recipient_id,
            message_id=message.id,
            sender_name=message.sender_name,
            subject=message.subject
        )
        
        db.add(notification)
        await db.commit()
        
        # Send real-time notifications
        await websocket_manager.broadcast_to_user(
            message_data.recipient_id,
            "new_message",
            {
                "message": message.to_dict(),
                "notification": notification.to_dict()
            }
        )
        
        # Cache message for quick access
        await redis_client.setex(
            f"message:{message.id}",
            3600,  # 1 hour
            message.to_dict()
        )
        
        logger.info(
            "Message created",
            message_id=str(message.id),
            sender_id=str(current_user.id),
            recipient_id=str(message_data.recipient_id)
        )
        
        return MessageWithUsers(
            id=message.id,
            sender_id=message.sender_id,
            recipient_id=message.recipient_id,
            subject=message.subject,
            body=message.body,
            is_read=message.is_read,
            is_starred=message.is_starred,
            is_archived=message.is_archived,
            created_at=message.created_at,
            updated_at=message.updated_at,
            sender=message.sender.to_dict() if message.sender else None,
            recipient=message.recipient.to_dict() if message.recipient else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error creating message", error=str(e), sender_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create message"
        )


@router.put("/{message_id}", response_model=MessageWithUsers)
async def update_message(
    message_id: uuid.UUID,
    message_update: MessageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update message properties (read, starred, archived)
    """
    try:
        query = select(Message).where(Message.id == message_id)
        result = await db.execute(query)
        message = result.scalar_one_or_none()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Check if user has access to this message
        if message.sender_id != current_user.id and message.recipient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Update allowed fields
        if message_update.is_read is not None:
            message.is_read = message_update.is_read
        if message_update.is_starred is not None:
            message.is_starred = message_update.is_starred
        if message_update.is_archived is not None:
            message.is_archived = message_update.is_archived
        
        await db.commit()
        await db.refresh(message, ["sender", "recipient"])
        
        # Send real-time update
        await websocket_manager.broadcast_to_user(
            current_user.id,
            "message_updated",
            {"message": message.to_dict()}
        )
        
        return MessageWithUsers(
            id=message.id,
            sender_id=message.sender_id,
            recipient_id=message.recipient_id,
            subject=message.subject,
            body=message.body,
            is_read=message.is_read,
            is_starred=message.is_starred,
            is_archived=message.is_archived,
            created_at=message.created_at,
            updated_at=message.updated_at,
            sender=message.sender.to_dict() if message.sender else None,
            recipient=message.recipient.to_dict() if message.recipient else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error updating message", error=str(e), message_id=str(message_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update message"
        )


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a message
    """
    try:
        query = select(Message).where(Message.id == message_id)
        result = await db.execute(query)
        message = result.scalar_one_or_none()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Check if user has access to this message
        if message.sender_id != current_user.id and message.recipient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        await db.delete(message)
        await db.commit()
        
        # Remove from cache
        await redis_client.delete(f"message:{message_id}")
        
        # Send real-time update
        await websocket_manager.broadcast_to_user(
            current_user.id,
            "message_deleted",
            {"message_id": str(message_id)}
        )
        
        logger.info("Message deleted", message_id=str(message_id), user_id=str(current_user.id))
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error deleting message", error=str(e), message_id=str(message_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete message"
        )


@router.put("/bulk", response_model=BulkMessageResponse)
async def bulk_update_messages(
    bulk_update: BulkMessageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk update messages (mark as read, starred, archived)
    """
    try:
        # Get messages that user has access to
        query = select(Message).where(
            and_(
                Message.id.in_(bulk_update.message_ids),
                or_(
                    Message.sender_id == current_user.id,
                    Message.recipient_id == current_user.id
                )
            )
        )
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No accessible messages found"
            )
        
        # Update messages
        updated_count = 0
        for message in messages:
            if bulk_update.updates.is_read is not None:
                message.is_read = bulk_update.updates.is_read
            if bulk_update.updates.is_starred is not None:
                message.is_starred = bulk_update.updates.is_starred
            if bulk_update.updates.is_archived is not None:
                message.is_archived = bulk_update.updates.is_archived
            updated_count += 1
        
        await db.commit()
        
        # Send real-time updates
        await websocket_manager.broadcast_to_user(
            current_user.id,
            "messages_bulk_updated",
            {
                "message_ids": [str(msg.id) for msg in messages],
                "updates": bulk_update.updates.dict(exclude_none=True)
            }
        )
        
        logger.info(
            "Bulk message update",
            user_id=str(current_user.id),
            updated_count=updated_count
        )
        
        return BulkMessageResponse(
            message=f"Updated {updated_count} messages",
            updated_count=updated_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error bulk updating messages", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update messages"
        )


@router.get("/stats/summary", response_model=MessageStats)
async def get_message_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get message statistics for the current user
    """
    try:
        # Get counts for different message types
        inbox_query = select(func.count(Message.id)).where(
            and_(
                Message.recipient_id == current_user.id,
                Message.is_archived == False
            )
        )
        
        unread_query = select(func.count(Message.id)).where(
            and_(
                Message.recipient_id == current_user.id,
                Message.is_read == False,
                Message.is_archived == False
            )
        )
        
        starred_query = select(func.count(Message.id)).where(
            and_(
                or_(
                    Message.recipient_id == current_user.id,
                    Message.sender_id == current_user.id
                ),
                Message.is_starred == True,
                Message.is_archived == False
            )
        )
        
        archived_query = select(func.count(Message.id)).where(
            and_(
                or_(
                    Message.recipient_id == current_user.id,
                    Message.sender_id == current_user.id
                ),
                Message.is_archived == True
            )
        )
        
        sent_query = select(func.count(Message.id)).where(
            and_(
                Message.sender_id == current_user.id,
                Message.is_archived == False
            )
        )
        
        # Execute queries
        total_messages = await db.scalar(inbox_query)
        unread_count = await db.scalar(unread_query)
        starred_count = await db.scalar(starred_query)
        archived_count = await db.scalar(archived_query)
        sent_count = await db.scalar(sent_query)
        
        return MessageStats(
            total_messages=total_messages or 0,
            unread_count=unread_count or 0,
            starred_count=starred_count or 0,
            archived_count=archived_count or 0,
            sent_count=sent_count or 0
        )
        
    except Exception as e:
        logger.error("Error fetching message stats", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch message statistics"
        )
