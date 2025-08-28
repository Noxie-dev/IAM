"""
Authentication Endpoints
Phase 2: Backend Enhancement

JWT-based authentication endpoints with enhanced error handling
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.database import get_db
from app.core.auth import auth_service, get_current_user, PasswordManager
from app.models.user import User
from app.schemas.auth import (
    LoginRequest, 
    LoginResponse, 
    RegisterRequest, 
    RegisterResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ChangePasswordRequest,
    LogoutResponse
)
from app.schemas.user import UserResponse
from app.core.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> RegisterResponse:
    """
    Register a new user account
    
    Creates a new user with email and password. Email verification may be required
    depending on system configuration.
    """
    try:
        # Check if registration is enabled
        if not settings.ENABLE_REGISTRATION:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration is currently disabled"
            )
        
        # Check if user already exists
        stmt = select(User).where(User.email == request.email.lower())
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        # Validate password strength
        password_validation = PasswordManager.validate_password_strength(request.password)
        if not password_validation["is_valid"]:
            error_message = "Password does not meet requirements: " + "; ".join(password_validation["errors"])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Create new user
        hashed_password = PasswordManager.hash_password(request.password)
        
        new_user = User(
            email=request.email.lower(),
            password_hash=hashed_password,
            first_name=request.first_name,
            last_name=request.last_name,
            company_name=request.company_name,
            subscription_tier="free",
            is_active=True,
            email_verified=False  # Will be verified via email
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info("User registered successfully", 
                   user_id=str(new_user.id), 
                   email=new_user.email)
        
        # Create session and tokens
        session_data = await auth_service.create_user_session(new_user)
        
        # Create user response manually to avoid relationship issues
        user_data = {
            "id": new_user.id,
            "email": new_user.email,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
            "full_name": new_user.full_name,
            "display_name": new_user.display_name,
            "company_name": new_user.company_name,
            "phone": new_user.phone,
            "subscription_tier": new_user.subscription_tier,
            "subscription_status": new_user.subscription_status,
            "subscription_start_date": new_user.subscription_start_date,
            "subscription_end_date": new_user.subscription_end_date,
            "trial_end_date": new_user.trial_end_date,
            "monthly_transcription_minutes": new_user.monthly_transcription_minutes,
            "total_transcription_minutes": new_user.total_transcription_minutes,
            "remaining_minutes": new_user.remaining_minutes,
            "email_verified": new_user.email_verified,
            "is_active": new_user.is_active,
            "is_admin": new_user.is_admin,
            "is_premium": new_user.is_premium,
            "is_trial_active": new_user.is_trial_active,
            "is_subscription_active": new_user.is_subscription_active,
            "last_login": new_user.last_login,
            "created_at": new_user.created_at,
            "updated_at": new_user.updated_at,
        }

        return RegisterResponse(
            success=True,
            message="User registered successfully",
            user=UserResponse(**user_data),
            **session_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration failed", error=str(e), email=request.email)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """
    Authenticate user and create session
    
    Validates user credentials and returns JWT tokens for API access.
    """
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(request.email, request.password, db)
        
        if not user:
            # Generic error message to prevent user enumeration
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create session and tokens
        session_data = await auth_service.create_user_session(user)
        
        logger.info("User logged in successfully", 
                   user_id=str(user.id), 
                   email=user.email)
        
        # Create user response manually to avoid relationship issues
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

        return LoginResponse(
            success=True,
            message="Login successful",
            user=UserResponse(**user_data),
            **session_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e), email=request.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest
) -> RefreshTokenResponse:
    """
    Refresh access token using refresh token
    
    Generates a new access token when the current one expires.
    """
    try:
        token_data = await auth_service.refresh_access_token(request.refresh_token)
        
        return RefreshTokenResponse(
            success=True,
            message="Token refreshed successfully",
            **token_data
        )
        
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

@router.post("/logout", response_model=LogoutResponse)
async def logout(
    session_id: str = Body(..., embed=True),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> LogoutResponse:
    """
    Logout user and invalidate session
    
    Removes the user session and invalidates tokens.
    """
    try:
        success = await auth_service.logout_user(session_id)
        
        if success:
            logger.info("User logged out successfully", 
                       user_id=current_user["id"], 
                       session_id=session_id)
            
            return LogoutResponse(
                success=True,
                message="Logged out successfully"
            )
        else:
            return LogoutResponse(
                success=False,
                message="Session not found or already expired"
            )
            
    except Exception as e:
        logger.error("Logout failed", error=str(e), user_id=current_user["id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed. Please try again."
        )

@router.post("/logout-all", response_model=LogoutResponse)
async def logout_all_sessions(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> LogoutResponse:
    """
    Logout user from all sessions
    
    Invalidates all active sessions for the current user.
    """
    try:
        count = await auth_service.logout_all_sessions(current_user["id"])
        
        logger.info("All sessions logged out", 
                   user_id=current_user["id"], 
                   session_count=count)
        
        return LogoutResponse(
            success=True,
            message=f"Logged out from {count} sessions"
        )
        
    except Exception as e:
        logger.error("Logout all failed", error=str(e), user_id=current_user["id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed. Please try again."
        )

@router.post("/change-password", response_model=Dict[str, Any])
async def change_password(
    request: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Change user password
    
    Updates the user's password after verifying the current password.
    """
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
        
        # Verify current password
        if not PasswordManager.verify_password(request.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password strength
        password_validation = PasswordManager.validate_password_strength(request.new_password)
        if not password_validation["is_valid"]:
            error_message = "New password does not meet requirements: " + "; ".join(password_validation["errors"])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Update password
        user.password_hash = PasswordManager.hash_password(request.new_password)
        await db.commit()
        
        # Logout from all sessions (force re-login with new password)
        await auth_service.logout_all_sessions(current_user["id"])
        
        logger.info("Password changed successfully", user_id=current_user["id"])
        
        return {
            "success": True,
            "message": "Password changed successfully. Please log in again."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password change failed", error=str(e), user_id=current_user["id"])
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed. Please try again."
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Get current user information
    
    Returns detailed information about the authenticated user.
    """
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
        
        # Create user response manually to avoid relationship issues
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
        logger.error("Get user info failed", error=str(e), user_id=current_user["id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )
