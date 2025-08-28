"""
Authentication Schemas
Phase 2: Backend Enhancement

Pydantic schemas for authentication requests and responses
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class LoginResponse(BaseModel):
    """Login response schema"""
    success: bool = Field(..., description="Whether login was successful")
    message: str = Field(..., description="Response message")
    user: UserResponse = Field(..., description="User information")
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    session_id: str = Field(..., description="Session identifier")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe"
                },
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
                "session_id": "session_123"
            }
        }


class RegisterRequest(BaseModel):
    """User registration request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    company_name: Optional[str] = Field(None, max_length=200, description="Company name")
    
    @validator('password')
    def validate_password(cls, v):
        """Basic password validation"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "first_name": "Jane",
                "last_name": "Smith",
                "company_name": "Acme Corp"
            }
        }


class RegisterResponse(BaseModel):
    """User registration response schema"""
    success: bool = Field(..., description="Whether registration was successful")
    message: str = Field(..., description="Response message")
    user: UserResponse = Field(..., description="Created user information")
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    session_id: str = Field(..., description="Session identifier")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="JWT refresh token")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema"""
    success: bool = Field(..., description="Whether token refresh was successful")
    message: str = Field(..., description="Response message")
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Token refreshed successfully",
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 86400
            }
        }


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Basic password validation"""
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "NewSecurePass123!"
            }
        }


class LogoutResponse(BaseModel):
    """Logout response schema"""
    success: bool = Field(..., description="Whether logout was successful")
    message: str = Field(..., description="Response message")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Logged out successfully"
            }
        }


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr = Field(..., description="User email address")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Basic password validation"""
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "token": "reset_token_123",
                "new_password": "NewSecurePass123!"
            }
        }


class EmailVerificationRequest(BaseModel):
    """Email verification request schema"""
    token: str = Field(..., description="Email verification token")
    
    class Config:
        schema_extra = {
            "example": {
                "token": "verification_token_123"
            }
        }


class TokenValidationResponse(BaseModel):
    """Token validation response schema"""
    valid: bool = Field(..., description="Whether token is valid")
    user_id: Optional[str] = Field(None, description="User ID if token is valid")
    expires_at: Optional[str] = Field(None, description="Token expiration time")
    
    class Config:
        schema_extra = {
            "example": {
                "valid": True,
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "expires_at": "2024-12-27T10:30:00Z"
            }
        }
