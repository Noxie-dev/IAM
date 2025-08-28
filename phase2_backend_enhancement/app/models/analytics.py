"""
Analytics Models
Phase 2: Backend Enhancement

SQLAlchemy models for usage analytics and tracking
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import String, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey

from app.core.database import Base


class UsageAnalytics(Base):
    """
    Usage analytics model for tracking user behavior
    """
    __tablename__ = "usage_analytics"
    
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
    
    # Event information
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Session information
    session_id: Mapped[Optional[str]] = mapped_column(String(255))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Relationships - disabled due to schema mismatch
    # user: Mapped["User"] = relationship("User", back_populates="usage_analytics")
    
    def __repr__(self) -> str:
        return f"<UsageAnalytics(id={self.id}, event_type='{self.event_type}')>"
