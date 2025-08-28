"""
Notification Model
Phase 2: Backend Enhancement

SQLAlchemy 2.0 Notification model for real-time notifications
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Boolean, Text, ForeignKey, TIMESTAMP, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Notification(Base):
    """
    Notification model for real-time user notifications
    """
    __tablename__ = "notifications"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Notification content
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="new_message",
        index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Notification status
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notifications",
        lazy="selectin"
    )
    message: Mapped[Optional["Message"]] = relationship(
        "Message",
        back_populates="notifications",
        lazy="selectin"
    )
    
    # Composite indexes for performance
    __table_args__ = (
        Index("ix_notifications_user_created", "user_id", "created_at"),
        Index("ix_notifications_user_read", "user_id", "is_read"),
        Index("ix_notifications_user_type", "user_id", "type"),
    )
    
    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type='{self.type}', user_id={self.user_id})>"
    
    def to_dict(self) -> dict:
        """Convert notification to dictionary for API responses"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "message_id": str(self.message_id) if self.message_id else None,
            "type": self.type,
            "content": self.content,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user": {
                "id": str(self.user.id),
                "email": self.user.email,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name
            } if self.user else None,
            "message": self.message.to_dict() if self.message else None
        }
    
    def mark_as_read(self) -> None:
        """Mark notification as read"""
        self.is_read = True
    
    @property
    def is_message_notification(self) -> bool:
        """Check if this is a message-related notification"""
        return self.type == "new_message" and self.message_id is not None
    
    @property
    def notification_title(self) -> str:
        """Get notification title based on type"""
        if self.type == "new_message":
            return "New Message"
        elif self.type == "meeting_update":
            return "Meeting Update"
        elif self.type == "system_alert":
            return "System Alert"
        else:
            return "Notification"
    
    @classmethod
    def create_message_notification(
        cls,
        user_id: uuid.UUID,
        message_id: uuid.UUID,
        sender_name: str,
        subject: str
    ) -> "Notification":
        """Create a new message notification"""
        return cls(
            user_id=user_id,
            message_id=message_id,
            type="new_message",
            content=f"New message from {sender_name}: {subject}"
        )
    
    @classmethod
    def create_system_notification(
        cls,
        user_id: uuid.UUID,
        content: str,
        notification_type: str = "system_alert"
    ) -> "Notification":
        """Create a system notification"""
        return cls(
            user_id=user_id,
            message_id=None,
            type=notification_type,
            content=content
        )
