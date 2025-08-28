"""
Subscription and Payment Models
Phase 2: Backend Enhancement

SQLAlchemy models for subscription management and payments
"""

import uuid
from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlalchemy import String, DateTime, Text, DECIMAL, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey

from app.core.database import Base


class SubscriptionPlan(Base):
    """
    Subscription plan model
    """
    __tablename__ = "subscription_plans"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Plan details
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tier: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Pricing
    price_zar: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    price_usd: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    
    # Limits
    monthly_minutes: Mapped[int] = mapped_column(Integer, nullable=False)  # -1 for unlimited
    max_file_size_mb: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<SubscriptionPlan(tier='{self.tier}', name='{self.name}')>"


class PaymentTransaction(Base):
    """
    Payment transaction model
    """
    __tablename__ = "payment_transactions"
    
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
    
    # Transaction details
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)  # ZAR, USD
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Payment gateway information
    gateway: Mapped[str] = mapped_column(String(50), nullable=False)  # stripe, paygate, etc.
    gateway_transaction_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Subscription information
    subscription_tier: Mapped[str] = mapped_column(String(50), nullable=False)
    billing_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    billing_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships - disabled due to schema mismatch
    # user: Mapped["User"] = relationship("User", back_populates="payment_transactions")
    
    def __repr__(self) -> str:
        return f"<PaymentTransaction(id={self.id}, amount={self.amount}, status='{self.status}')>"
