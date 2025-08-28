"""
Authentication Service
Phase 2: Backend Enhancement

Simple authentication service for testing and development
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from unittest.mock import Mock

# Simple bearer token security
security = HTTPBearer()


class MockUser:
    """Mock user for testing"""
    def __init__(self, user_id: str = "test-user-123", email: str = "test@example.com"):
        self.id = user_id
        self.email = email
        self.subscription_tier = "premium"
        self.remaining_minutes = 100


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> MockUser:
    """
    Get current authenticated user (mock implementation for testing)
    
    In production, this would validate JWT tokens and return real user data
    """
    # For testing, just return a mock user
    # In production, you would:
    # 1. Validate the JWT token
    # 2. Extract user ID from token
    # 3. Query database for user details
    # 4. Return user object
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Mock validation - in production, validate JWT token here
    token = credentials.credentials
    if not token or token == "invalid":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Return mock user for testing
    return MockUser()


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[MockUser]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None


# For testing purposes, provide a way to bypass authentication
def get_current_user_test() -> MockUser:
    """Get mock user for testing without authentication"""
    return MockUser()
