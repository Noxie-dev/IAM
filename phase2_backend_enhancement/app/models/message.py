"""
Message Model
Phase 2: Backend Enhancement

SQLAlchemy 2.0 Message model for inbox feature with enhanced relationships
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Boolean, Text, ForeignKey, TIMESTAMP, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Message(Base):
    """
    Message model for inbox feature with enhanced relationships and indexing
    """
    __tablename__ = "messages"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Foreign keys
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Message content
    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Message status
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    is_starred: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    is_archived: Mapped[bool] = mapped_column(
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
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    sender: Mapped["User"] = relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="sent_messages",
        lazy="selectin"
    )
    recipient: Mapped["User"] = relationship(
        "User",
        foreign_keys=[recipient_id],
        back_populates="received_messages",
        lazy="selectin"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="message",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Composite indexes for performance
    __table_args__ = (
        Index("ix_messages_recipient_created", "recipient_id", "created_at"),
        Index("ix_messages_sender_created", "sender_id", "created_at"),
        Index("ix_messages_recipient_read", "recipient_id", "is_read"),
        Index("ix_messages_recipient_starred", "recipient_id", "is_starred"),
        Index("ix_messages_recipient_archived", "recipient_id", "is_archived"),
    )
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, subject='{self.subject}', sender_id={self.sender_id}, recipient_id={self.recipient_id})>"
    
    def to_dict(self) -> dict:
        """Convert message to dictionary for API responses"""
        return {
            "id": str(self.id),
            "sender_id": str(self.sender_id),
            "recipient_id": str(self.recipient_id),
            "subject": self.subject,
            "body": self.body,
            "is_read": self.is_read,
            "is_starred": self.is_starred,
            "is_archived": self.is_archived,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "sender": {
                "id": str(self.sender.id),
                "email": self.sender.email,
                "first_name": self.sender.first_name,
                "last_name": self.sender.last_name
            } if self.sender else None,
            "recipient": {
                "id": str(self.recipient.id),
                "email": self.recipient.email,
                "first_name": self.recipient.first_name,
                "last_name": self.recipient.last_name
            } if self.recipient else None
        }
    
    @property
    def sender_name(self) -> str:
        """Get sender's display name"""
        if self.sender:
            if self.sender.first_name and self.sender.last_name:
                return f"{self.sender.first_name} {self.sender.last_name}"
            elif self.sender.first_name:
                return self.sender.first_name
            else:
                return self.sender.email
        return "Unknown Sender"
    
    @property
    def recipient_name(self) -> str:
        """Get recipient's display name"""
        if self.recipient:
            if self.recipient.first_name and self.recipient.last_name:
                return f"{self.recipient.first_name} {self.recipient.last_name}"
            elif self.recipient.first_name:
                return self.recipient.first_name
            else:
                return self.recipient.email
        return "Unknown Recipient"
    
    def mark_as_read(self) -> None:
        """Mark message as read"""
        self.is_read = True
    
    def toggle_star(self) -> None:
        """Toggle star status"""
        self.is_starred = not self.is_starred
    
    def archive(self) -> None:
        """Archive message"""
        self.is_archived = True
    
    def unarchive(self) -> None:
        """Unarchive message"""
        self.is_archived = False
