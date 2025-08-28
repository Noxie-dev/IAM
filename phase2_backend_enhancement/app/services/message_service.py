"""
Message Service
Phase 2: Backend Enhancement

Business logic layer for message operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
import uuid
import structlog

from ..models.message import Message
from ..models.user import User
from ..models.notification import Notification
from ..schemas import message as message_schema

logger = structlog.get_logger(__name__)


def get_messages_for_user(db: Session, user_id: uuid.UUID) -> List[Message]:
    """Get all messages for a user (both sent and received)."""
    try:
        messages = db.query(Message).filter(
            or_(
                Message.sender_id == user_id,
                Message.recipient_id == user_id
            )
        ).order_by(Message.created_at.desc()).all()
        
        return messages
    except Exception as e:
        logger.error("Error fetching messages for user", error=str(e), user_id=str(user_id))
        raise


def get_message(db: Session, message_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Message]:
    """Get a specific message if user has access to it."""
    try:
        message = db.query(Message).filter(
            and_(
                Message.id == message_id,
                or_(
                    Message.sender_id == user_id,
                    Message.recipient_id == user_id
                )
            )
        ).first()
        
        # Mark as read if recipient is viewing
        if message and message.recipient_id == user_id and not message.is_read:
            message.is_read = True
            db.commit()
        
        return message
    except Exception as e:
        logger.error("Error fetching message", error=str(e), message_id=str(message_id))
        raise


def create_message(
    db: Session, 
    sender_id: uuid.UUID, 
    message_data: message_schema.MessageCreate
) -> Message:
    """Create a new message."""
    try:
        # Validate recipient exists
        recipient = db.query(User).filter(User.id == message_data.recipient_id).first()
        if not recipient:
            raise ValueError("Recipient not found")
        
        # Create message
        message = Message(
            sender_id=sender_id,
            recipient_id=message_data.recipient_id,
            subject=message_data.subject,
            body=message_data.body
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # Create notification for recipient
        sender = db.query(User).filter(User.id == sender_id).first()
        notification = Notification.create_message_notification(
            user_id=message_data.recipient_id,
            message_id=message.id,
            sender_name=sender.first_name or sender.email,
            subject=message_data.subject
        )
        
        db.add(notification)
        db.commit()
        
        logger.info(
            "Message created successfully",
            message_id=str(message.id),
            sender_id=str(sender_id),
            recipient_id=str(message_data.recipient_id)
        )
        
        return message
    except Exception as e:
        db.rollback()
        logger.error("Error creating message", error=str(e), sender_id=str(sender_id))
        raise


def update_message(
    db: Session,
    message_id: uuid.UUID,
    user_id: uuid.UUID,
    update_data: message_schema.MessageUpdate
) -> Optional[Message]:
    """Update message status."""
    try:
        # Get message and verify access
        message = db.query(Message).filter(
            and_(
                Message.id == message_id,
                or_(
                    Message.sender_id == user_id,
                    Message.recipient_id == user_id
                )
            )
        ).first()
        
        if not message:
            return None
        
        # Update fields
        if update_data.is_read is not None:
            message.is_read = update_data.is_read
        
        if update_data.is_starred is not None:
            message.is_starred = update_data.is_starred
        
        db.commit()
        db.refresh(message)
        
        logger.info(
            "Message updated",
            message_id=str(message_id),
            user_id=str(user_id),
            updates=update_data.dict(exclude_none=True)
        )
        
        return message
    except Exception as e:
        db.rollback()
        logger.error("Error updating message", error=str(e), message_id=str(message_id))
        raise


def delete_message(db: Session, message_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Delete a message if user has access to it."""
    try:
        message = db.query(Message).filter(
            and_(
                Message.id == message_id,
                or_(
                    Message.sender_id == user_id,
                    Message.recipient_id == user_id
                )
            )
        ).first()
        
        if not message:
            return False
        
        db.delete(message)
        db.commit()
        
        logger.info("Message deleted", message_id=str(message_id), user_id=str(user_id))
        return True
    except Exception as e:
        db.rollback()
        logger.error("Error deleting message", error=str(e), message_id=str(message_id))
        raise


def get_inbox_messages(db: Session, user_id: uuid.UUID) -> List[Message]:
    """Get inbox messages for a user."""
    try:
        messages = db.query(Message).filter(
            and_(
                Message.recipient_id == user_id,
                Message.is_archived == False
            )
        ).order_by(Message.created_at.desc()).all()
        
        return messages
    except Exception as e:
        logger.error("Error fetching inbox messages", error=str(e), user_id=str(user_id))
        raise


def get_sent_messages(db: Session, user_id: uuid.UUID) -> List[Message]:
    """Get sent messages for a user."""
    try:
        messages = db.query(Message).filter(
            and_(
                Message.sender_id == user_id,
                Message.is_archived == False
            )
        ).order_by(Message.created_at.desc()).all()
        
        return messages
    except Exception as e:
        logger.error("Error fetching sent messages", error=str(e), user_id=str(user_id))
        raise


def get_starred_messages(db: Session, user_id: uuid.UUID) -> List[Message]:
    """Get starred messages for a user."""
    try:
        messages = db.query(Message).filter(
            and_(
                or_(
                    Message.sender_id == user_id,
                    Message.recipient_id == user_id
                ),
                Message.is_starred == True,
                Message.is_archived == False
            )
        ).order_by(Message.created_at.desc()).all()
        
        return messages
    except Exception as e:
        logger.error("Error fetching starred messages", error=str(e), user_id=str(user_id))
        raise


def get_message_stats(db: Session, user_id: uuid.UUID) -> dict:
    """Get message statistics for a user."""
    try:
        # Count inbox messages
        inbox_count = db.query(Message).filter(
            and_(
                Message.recipient_id == user_id,
                Message.is_archived == False
            )
        ).count()
        
        # Count unread messages
        unread_count = db.query(Message).filter(
            and_(
                Message.recipient_id == user_id,
                Message.is_read == False,
                Message.is_archived == False
            )
        ).count()
        
        # Count starred messages
        starred_count = db.query(Message).filter(
            and_(
                or_(
                    Message.sender_id == user_id,
                    Message.recipient_id == user_id
                ),
                Message.is_starred == True,
                Message.is_archived == False
            )
        ).count()
        
        # Count sent messages
        sent_count = db.query(Message).filter(
            and_(
                Message.sender_id == user_id,
                Message.is_archived == False
            )
        ).count()
        
        return {
            "inbox_count": inbox_count,
            "unread_count": unread_count,
            "starred_count": starred_count,
            "sent_count": sent_count
        }
    except Exception as e:
        logger.error("Error fetching message stats", error=str(e), user_id=str(user_id))
        raise
