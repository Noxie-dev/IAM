"""
User Management Endpoints
Phase 2: Backend Enhancement

User CRUD operations and management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserPreferences, UserStats
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Get current user profile information"""
    try:
        # Get fresh user data from database
        stmt = select(User).where(User.id == current_user["id"])
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create user response
        user_data = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "display_name": user.display_name,
            "company_name": user.company_name,
            "phone": user.phone,
            "subscription_tier": user.subscription_tier,
            "subscription_status": user.subscription_status,
            "subscription_start_date": user.subscription_start_date,
            "subscription_end_date": user.subscription_end_date,
            "trial_end_date": user.trial_end_date,
            "monthly_transcription_minutes": user.monthly_transcription_minutes,
            "total_transcription_minutes": user.total_transcription_minutes,
            "remaining_minutes": user.remaining_minutes,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_premium": user.is_premium,
            "is_trial_active": user.is_trial_active,
            "is_subscription_active": user.is_subscription_active,
            "last_login": user.last_login,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

        return UserResponse(**user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )

@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Update current user profile information"""
    try:
        # Get user from database
        stmt = select(User).where(User.id == current_user["id"])
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update user fields
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"User profile updated: {user.id}")
        
        # Return updated user data
        return await get_current_user_profile(current_user, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )

@router.get("/me/stats", response_model=UserStats)
async def get_user_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserStats:
    """Get user activity statistics"""
    try:
        # Get user from database
        stmt = select(User).where(User.id == current_user["id"])
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Calculate stats (mock data for now - implement with real meeting data later)
        stats = UserStats(
            total_meetings=245,  # TODO: Calculate from meetings table
            total_hours=user.total_transcription_minutes / 60 if user.total_transcription_minutes else 0,
            monthly_minutes=user.monthly_transcription_minutes,
            total_minutes=user.total_transcription_minutes,
            remaining_minutes=user.remaining_minutes,
            projects_count=12,  # TODO: Calculate from projects table
            team_members=0,  # TODO: Calculate from team table
            account_age_days=(datetime.utcnow() - user.created_at).days,
            subscription_tier=user.subscription_tier,
            is_premium=user.is_premium
        )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )

@router.post("/me/preferences")
async def save_user_preferences(
    preferences: UserPreferences,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Save user preferences"""
    try:
        # Get user from database
        stmt = select(User).where(User.id == current_user["id"])
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Store preferences in user preferences field (JSON)
        user.preferences = preferences.model_dump()
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"User preferences saved: {user.id}")
        
        return {"message": "Preferences saved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving user preferences: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save preferences"
        )

@router.get("/me/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserPreferences:
    """Get user preferences"""
    try:
        # Get user from database
        stmt = select(User).where(User.id == current_user["id"])
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Return stored preferences or defaults
        if user.preferences:
            return UserPreferences(**user.preferences)
        else:
            # Return default preferences
            return UserPreferences()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preferences"
        )
