"""
User Model
Phase 2: Backend Enhancement

SQLAlchemy 2.0 User model with enhanced fields for SaaS platform
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Boolean, Integer, DateTime, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """
    User model for authentication and subscription management
    """
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Profile information
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    company_name: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Subscription and billing
    subscription_tier: Mapped[str] = mapped_column(
        String(50),
        default="free",
        nullable=False,
        index=True
    )
    subscription_status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        nullable=False
    )
    subscription_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    subscription_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    trial_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Usage tracking
    monthly_transcription_minutes: Mapped[int] = mapped_column(Integer, default=0)
    total_transcription_minutes: Mapped[int] = mapped_column(Integer, default=0)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Account management
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships - temporarily disabled due to schema mismatches
    # meetings: Mapped[List["Meeting"]] = relationship(
    #     "Meeting",
    #     back_populates="user",
    #     cascade="all, delete-orphan",
    #     lazy="selectin"
    # )

    # sessions: Mapped[List["UserSession"]] = relationship(
    #     "UserSession",
    #     back_populates="user",
    #     cascade="all, delete-orphan",
    #     lazy="selectin"
    # )

    # payment_transactions: Mapped[List["PaymentTransaction"]] = relationship(
    #     "PaymentTransaction",
    #     back_populates="user",
    #     cascade="all, delete-orphan",
    #     lazy="selectin"
    # )

    # usage_analytics: Mapped[List["UsageAnalytics"]] = relationship(
    #     "UsageAnalytics",
    #     back_populates="user",
    #     cascade="all, delete-orphan",
    #     lazy="selectin"
    # )
    
    # DICE™ jobs relationship
    dice_jobs: Mapped[List["DiceJob"]] = relationship(
        "DiceJob",
        foreign_keys="DiceJob.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "subscription_tier IN ('free', 'basic', 'premium', 'enterprise')",
            name="ck_users_subscription_tier"
        ),
        CheckConstraint(
            "subscription_status IN ('active', 'cancelled', 'suspended', 'trial')",
            name="ck_users_subscription_status"
        ),
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name="ck_users_valid_email"
        ),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', tier='{self.subscription_tier}')>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email.split('@')[0]
    
    @property
    def display_name(self) -> str:
        """Get display name for UI"""
        return self.full_name or self.email
    
    @property
    def is_premium(self) -> bool:
        """Check if user has premium subscription"""
        return self.subscription_tier in ["premium", "enterprise"]
    
    @property
    def is_trial_active(self) -> bool:
        """Check if trial is still active"""
        if not self.trial_end_date:
            return False
        return datetime.utcnow() < self.trial_end_date
    
    @property
    def is_subscription_active(self) -> bool:
        """Check if subscription is active"""
        if self.subscription_status != "active":
            return False
        
        if self.subscription_end_date:
            return datetime.utcnow() < self.subscription_end_date
        
        return True
    
    @property
    def remaining_minutes(self) -> int:
        """Get remaining transcription minutes for current month"""
        from app.core.config import settings
        
        plan = settings.get_subscription_plan(self.subscription_tier)
        monthly_limit = plan.get("monthly_minutes", 0)
        
        if monthly_limit == -1:  # Unlimited
            return -1
        
        return max(0, monthly_limit - self.monthly_transcription_minutes)
    
    def can_transcribe(self, duration_minutes: int = 0) -> bool:
        """Check if user can perform transcription"""
        if not self.is_active:
            return False
        
        if not self.is_subscription_active and not self.is_trial_active:
            return False
        
        remaining = self.remaining_minutes
        if remaining == -1:  # Unlimited
            return True
        
        return remaining >= duration_minutes
    
    def add_transcription_usage(self, minutes: int) -> None:
        """Add transcription usage to user's monthly total"""
        self.monthly_transcription_minutes += minutes
        self.total_transcription_minutes += minutes
    
    def reset_monthly_usage(self) -> None:
        """Reset monthly usage (called at beginning of each month)"""
        self.monthly_transcription_minutes = 0
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary"""
        data = {
            "id": str(self.id),
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "display_name": self.display_name,
            "company_name": self.company_name,
            "phone": self.phone,
            "subscription_tier": self.subscription_tier,
            "subscription_status": self.subscription_status,
            "subscription_start_date": self.subscription_start_date.isoformat() if self.subscription_start_date else None,
            "subscription_end_date": self.subscription_end_date.isoformat() if self.subscription_end_date else None,
            "trial_end_date": self.trial_end_date.isoformat() if self.trial_end_date else None,
            "monthly_transcription_minutes": self.monthly_transcription_minutes,
            "total_transcription_minutes": self.total_transcription_minutes,
            "remaining_minutes": self.remaining_minutes,
            "email_verified": self.email_verified,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "is_premium": self.is_premium,
            "is_trial_active": self.is_trial_active,
            "is_subscription_active": self.is_subscription_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        if include_sensitive:
            data.update({
                "password_hash": self.password_hash,
            })
        
        return data
