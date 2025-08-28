"""
User Schemas
Phase 2: Backend Enhancement

Pydantic schemas for user-related requests and responses
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    company_name: Optional[str] = Field(None, max_length=200, description="Company name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, description="User password")
    
    @validator('password')
    def validate_password(cls, v):
        """Basic password validation"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    company_name: Optional[str] = Field(None, max_length=200, description="Company name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "company_name": "Acme Corp",
                "phone": "+1234567890"
            }
        }


class UserResponse(BaseModel):
    """Schema for user response data"""
    id: UUID = Field(..., description="User unique identifier")
    email: EmailStr = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    full_name: str = Field(..., description="Full name")
    display_name: str = Field(..., description="Display name")
    company_name: Optional[str] = Field(None, description="Company name")
    phone: Optional[str] = Field(None, description="Phone number")
    
    # Subscription information
    subscription_tier: str = Field(..., description="Subscription tier")
    subscription_status: str = Field(..., description="Subscription status")
    subscription_start_date: Optional[datetime] = Field(None, description="Subscription start date")
    subscription_end_date: Optional[datetime] = Field(None, description="Subscription end date")
    trial_end_date: Optional[datetime] = Field(None, description="Trial end date")
    
    # Usage information
    monthly_transcription_minutes: int = Field(..., description="Monthly transcription minutes used")
    total_transcription_minutes: int = Field(..., description="Total transcription minutes used")
    remaining_minutes: int = Field(..., description="Remaining transcription minutes")
    
    # Account status
    email_verified: bool = Field(..., description="Whether email is verified")
    is_active: bool = Field(..., description="Whether account is active")
    is_admin: bool = Field(..., description="Whether user is admin")
    is_premium: bool = Field(..., description="Whether user has premium subscription")
    is_trial_active: bool = Field(..., description="Whether trial is active")
    is_subscription_active: bool = Field(..., description="Whether subscription is active")
    
    # Timestamps
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "display_name": "John Doe",
                "company_name": "Acme Corp",
                "phone": "+1234567890",
                "subscription_tier": "premium",
                "subscription_status": "active",
                "subscription_start_date": "2024-01-01T00:00:00Z",
                "subscription_end_date": "2024-12-31T23:59:59Z",
                "trial_end_date": None,
                "monthly_transcription_minutes": 150,
                "total_transcription_minutes": 1500,
                "remaining_minutes": 1050,
                "email_verified": True,
                "is_active": True,
                "is_admin": False,
                "is_premium": True,
                "is_trial_active": False,
                "is_subscription_active": True,
                "last_login": "2024-12-26T10:30:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-12-26T10:30:00Z"
            }
        }


class UserListResponse(BaseModel):
    """Schema for user list response"""
    users: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of users per page")
    pages: int = Field(..., description="Total number of pages")
    
    class Config:
        schema_extra = {
            "example": {
                "users": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "user1@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "subscription_tier": "premium"
                    }
                ],
                "total": 100,
                "page": 1,
                "per_page": 20,
                "pages": 5
            }
        }


class UserStatsResponse(BaseModel):
    """Schema for user statistics response"""
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    premium_users: int = Field(..., description="Number of premium users")
    trial_users: int = Field(..., description="Number of trial users")
    new_users_this_month: int = Field(..., description="New users this month")
    
    subscription_breakdown: dict = Field(..., description="Subscription tier breakdown")
    monthly_growth: float = Field(..., description="Monthly growth percentage")
    
    class Config:
        schema_extra = {
            "example": {
                "total_users": 1000,
                "active_users": 850,
                "premium_users": 200,
                "trial_users": 50,
                "new_users_this_month": 75,
                "subscription_breakdown": {
                    "free": 600,
                    "basic": 150,
                    "premium": 200,
                    "enterprise": 50
                },
                "monthly_growth": 8.5
            }
        }


class UserUsageResponse(BaseModel):
    """Schema for user usage statistics"""
    user_id: UUID = Field(..., description="User ID")
    current_month_minutes: int = Field(..., description="Current month transcription minutes")
    total_minutes: int = Field(..., description="Total transcription minutes")
    remaining_minutes: int = Field(..., description="Remaining minutes in current plan")
    
    monthly_usage_history: list[dict] = Field(..., description="Monthly usage history")
    average_monthly_usage: float = Field(..., description="Average monthly usage")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "current_month_minutes": 150,
                "total_minutes": 1500,
                "remaining_minutes": 1050,
                "monthly_usage_history": [
                    {"month": "2024-11", "minutes": 200},
                    {"month": "2024-12", "minutes": 150}
                ],
                "average_monthly_usage": 175.0
            }
        }


class UserPreferences(BaseModel):
    """Schema for user preferences"""
    language: str = Field(default="English", description="Preferred language")
    timezone: str = Field(default="Pacific Standard Time", description="User timezone")
    email_notifications: bool = Field(default=True, description="Enable email notifications")
    push_notifications: bool = Field(default=False, description="Enable push notifications")
    sound_enabled: bool = Field(default=True, description="Enable sound notifications")
    auto_save: bool = Field(default=True, description="Enable auto-save")
    dark_mode: bool = Field(default=True, description="Enable dark mode")
    compact_view: bool = Field(default=False, description="Enable compact view")
    
    class Config:
        schema_extra = {
            "example": {
                "language": "English",
                "timezone": "Pacific Standard Time",
                "email_notifications": True,
                "push_notifications": False,
                "sound_enabled": True,
                "auto_save": True,
                "dark_mode": True,
                "compact_view": False
            }
        }


class UserStats(BaseModel):
    """Schema for individual user statistics"""
    total_meetings: int = Field(..., description="Total number of meetings")
    total_hours: float = Field(..., description="Total hours of transcription")
    monthly_minutes: int = Field(..., description="Monthly transcription minutes")
    total_minutes: int = Field(..., description="Total transcription minutes")
    remaining_minutes: int = Field(..., description="Remaining transcription minutes")
    projects_count: int = Field(..., description="Number of projects")
    team_members: int = Field(..., description="Number of team members")
    account_age_days: int = Field(..., description="Account age in days")
    subscription_tier: str = Field(..., description="Current subscription tier")
    is_premium: bool = Field(..., description="Whether user has premium subscription")
    
    class Config:
        schema_extra = {
            "example": {
                "total_meetings": 245,
                "total_hours": 25.5,
                "monthly_minutes": 150,
                "total_minutes": 1530,
                "remaining_minutes": 1050,
                "projects_count": 12,
                "team_members": 5,
                "account_age_days": 365,
                "subscription_tier": "premium",
                "is_premium": True
            }
        }
