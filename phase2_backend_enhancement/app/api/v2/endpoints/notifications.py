"""
Notification API Endpoints
Phase 2: Backend Enhancement

FastAPI endpoints for notification management with real-time support
"""

import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.message import (
    NotificationResponse,
    NotificationWithMessage,
    NotificationListResponse,
    BulkNotificationUpdate,
    NotificationStats
)
from app.services.websocket import WebSocketManager
from app.core.redis_client import redis_client
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])

# WebSocket manager for real-time updates
websocket_manager = WebSocketManager()


@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    unread_only: bool = Query(False, description="Show only unread notifications"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get notifications for the current user with filtering and pagination
    """
    try:
        # Build base query
        base_query = select(Notification).where(Notification.user_id == current_user.id)
        
        # Add unread filter if requested
        if unread_only:
            base_query = base_query.where(Notification.is_read == False)
        
        # Add relationships and ordering
        query = base_query.options(
            selectinload(Notification.message).selectinload(Notification.message.sender),
            selectinload(Notification.message).selectinload(Notification.message.recipient)
        ).order_by(Notification.created_at.desc())
        
        # Execute query with pagination
        result = await db.execute(query)
        notifications = result.scalars().all()
        
        # Manual pagination
        total = len(notifications)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_notifications = notifications[start_idx:end_idx]
        
        # Convert to response format
        notification_responses = []
        for notif in paginated_notifications:
            notification_data = {
                "id": notif.id,
                "user_id": notif.user_id,
                "message_id": notif.message_id,
                "type": notif.type,
                "content": notif.content,
                "is_read": notif.is_read,
                "created_at": notif.created_at,
                "message": None
            }
            
            # Add message details if available
            if notif.message:
                notification_data["message"] = {
                    "id": str(notif.message.id),
                    "sender_id": str(notif.message.sender_id),
                    "recipient_id": str(notif.message.recipient_id),
                    "subject": notif.message.subject,
                    "body": notif.message.body,
                    "is_read": notif.message.is_read,
                    "is_starred": notif.message.is_starred,
                    "is_archived": notif.message.is_archived,
                    "created_at": notif.message.created_at,
                    "updated_at": notif.message.updated_at,
                    "sender": notif.message.sender.to_dict() if notif.message.sender else None,
                    "recipient": notif.message.recipient.to_dict() if notif.message.recipient else None
                }
            
            notification_responses.append(NotificationWithMessage(**notification_data))
        
        return NotificationListResponse(
            notifications=notification_responses,
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
        logger.error("Error fetching notifications", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notifications"
        )


@router.get("/{notification_id}", response_model=NotificationWithMessage)
async def get_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific notification by ID
    """
    try:
        query = select(Notification).options(
            selectinload(Notification.message).selectinload(Notification.message.sender),
            selectinload(Notification.message).selectinload(Notification.message.recipient)
        ).where(Notification.id == notification_id)
        
        result = await db.execute(query)
        notification = result.scalar_one_or_none()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        # Check if user owns this notification
        if notification.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Mark as read if not already read
        if not notification.is_read:
            notification.is_read = True
            await db.commit()
            
            # Send real-time update
            await websocket_manager.broadcast_to_user(
                current_user.id,
                "notification_read",
                {"notification_id": str(notification_id)}
            )
        
        # Convert to response format
        notification_data = {
            "id": notification.id,
            "user_id": notification.user_id,
            "message_id": notification.message_id,
            "type": notification.type,
            "content": notification.content,
            "is_read": notification.is_read,
            "created_at": notification.created_at,
            "message": None
        }
        
        # Add message details if available
        if notification.message:
            notification_data["message"] = {
                "id": str(notification.message.id),
                "sender_id": str(notification.message.sender_id),
                "recipient_id": str(notification.message.recipient_id),
                "subject": notification.message.subject,
                "body": notification.message.body,
                "is_read": notification.message.is_read,
                "is_starred": notification.message.is_starred,
                "is_archived": notification.message.is_archived,
                "created_at": notification.message.created_at,
                "updated_at": notification.message.updated_at,
                "sender": notification.message.sender.to_dict() if notification.message.sender else None,
                "recipient": notification.message.recipient.to_dict() if notification.message.recipient else None
            }
        
        return NotificationWithMessage(**notification_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching notification", error=str(e), notification_id=str(notification_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notification"
        )


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a notification as read
    """
    try:
        query = select(Notification).where(Notification.id == notification_id)
        result = await db.execute(query)
        notification = result.scalar_one_or_none()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        # Check if user owns this notification
        if notification.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Mark as read
        notification.is_read = True
        await db.commit()
        
        # Send real-time update
        await websocket_manager.broadcast_to_user(
            current_user.id,
            "notification_read",
            {"notification_id": str(notification_id)}
        )
        
        return NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            message_id=notification.message_id,
            type=notification.type,
            content=notification.content,
            is_read=notification.is_read,
            created_at=notification.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error marking notification as read", error=str(e), notification_id=str(notification_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )


@router.put("/bulk/read", response_model=dict)
async def bulk_mark_notifications_read(
    bulk_update: BulkNotificationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk mark notifications as read
    """
    try:
        # Get notifications that user owns
        query = select(Notification).where(
            and_(
                Notification.id.in_(bulk_update.notification_ids),
                Notification.user_id == current_user.id
            )
        )
        
        result = await db.execute(query)
        notifications = result.scalars().all()
        
        if not notifications:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No accessible notifications found"
            )
        
        # Mark notifications as read
        updated_count = 0
        for notification in notifications:
            if not notification.is_read:
                notification.is_read = True
                updated_count += 1
        
        await db.commit()
        
        # Send real-time updates
        await websocket_manager.broadcast_to_user(
            current_user.id,
            "notifications_bulk_read",
            {
                "notification_ids": [str(notif.id) for notif in notifications],
                "updated_count": updated_count
            }
        )
        
        logger.info(
            "Bulk notification read",
            user_id=str(current_user.id),
            updated_count=updated_count
        )
        
        return {
            "message": f"Marked {updated_count} notifications as read",
            "updated_count": updated_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error bulk marking notifications as read", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read"
        )


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a notification
    """
    try:
        query = select(Notification).where(Notification.id == notification_id)
        result = await db.execute(query)
        notification = result.scalar_one_or_none()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        # Check if user owns this notification
        if notification.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        await db.delete(notification)
        await db.commit()
        
        # Send real-time update
        await websocket_manager.broadcast_to_user(
            current_user.id,
            "notification_deleted",
            {"notification_id": str(notification_id)}
        )
        
        logger.info("Notification deleted", notification_id=str(notification_id), user_id=str(current_user.id))
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error deleting notification", error=str(e), notification_id=str(notification_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification"
        )


@router.get("/stats/summary", response_model=NotificationStats)
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get notification statistics for the current user
    """
    try:
        # Get counts for different notification types
        total_query = select(func.count(Notification.id)).where(Notification.user_id == current_user.id)
        unread_query = select(func.count(Notification.id)).where(
            and_(
                Notification.user_id == current_user.id,
                Notification.is_read == False
            )
        )
        new_message_query = select(func.count(Notification.id)).where(
            and_(
                Notification.user_id == current_user.id,
                Notification.type == "new_message"
            )
        )
        system_query = select(func.count(Notification.id)).where(
            and_(
                Notification.user_id == current_user.id,
                Notification.type == "system_alert"
            )
        )
        
        # Execute queries
        total_notifications = await db.scalar(total_query)
        unread_count = await db.scalar(unread_query)
        new_message_count = await db.scalar(new_message_query)
        system_count = await db.scalar(system_query)
        
        return NotificationStats(
            total_notifications=total_notifications or 0,
            unread_count=unread_count or 0,
            new_message_count=new_message_count or 0,
            system_count=system_count or 0
        )
        
    except Exception as e:
        logger.error("Error fetching notification stats", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notification statistics"
        )


@router.post("/system", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_system_notification(
    user_id: uuid.UUID,
    content: str,
    notification_type: str = "system_alert",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a system notification (admin only)
    """
    try:
        # Check if current user is admin
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Validate target user exists
        user_query = select(User).where(User.id == user_id)
        result = await db.execute(user_query)
        target_user = result.scalar_one_or_none()
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found"
            )
        
        # Create system notification
        notification = Notification.create_system_notification(
            user_id=user_id,
            content=content,
            notification_type=notification_type
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        
        # Send real-time notification
        await websocket_manager.broadcast_to_user(
            user_id,
            "new_notification",
            {"notification": notification.to_dict()}
        )
        
        logger.info(
            "System notification created",
            admin_id=str(current_user.id),
            target_user_id=str(user_id),
            notification_type=notification_type
        )
        
        return NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            message_id=notification.message_id,
            type=notification.type,
            content=notification.content,
            is_read=notification.is_read,
            created_at=notification.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error creating system notification", error=str(e), admin_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create system notification"
        )
