"""
User Session Model
Phase 2: Backend Enhancement

SQLAlchemy model for user session tracking
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey

from app.core.database import Base


class UserSession(Base):
    """
    User session model for tracking active sessions
    """
    __tablename__ = "user_sessions"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Foreign key to user
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Session information
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    device_info: Mapped[Optional[dict]] = mapped_column(Text)  # Store as JSON string

    # Session metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    
    # Session status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)  # Match DB schema

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),  # Match DB schema
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships - disabled since we use Redis for session management
    # user: Mapped["User"] = relationship("User", back_populates="sessions")
    
    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
