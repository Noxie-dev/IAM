"""
Authentication System
Phase 2: Backend Enhancement

JWT-based authentication with Redis session management
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

from app.core.config import settings
from app.core.redis_client import session_manager
from app.models.user import User

logger = structlog.get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token security
security = HTTPBearer(auto_error=False)

class AuthenticationError(Exception):
    """Custom authentication error"""
    pass

class AuthorizationError(Exception):
    """Custom authorization error"""
    pass

class TokenManager:
    """
    JWT token management with Redis session storage
    """
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create JWT refresh token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify and decode JWT token
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                raise AuthenticationError(f"Invalid token type. Expected {token_type}")
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                raise AuthenticationError("Token has expired")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.JWTError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
    
    def get_token_payload(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get token payload without verification (for debugging)
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except jwt.JWTError:
            return None

class PasswordManager:
    """
    Password hashing and verification
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using bcrypt
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """
        Validate password strength
        """
        errors = []
        
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "strength": "strong" if len(errors) == 0 else "weak"
        }

class AuthService:
    """
    Main authentication service
    """
    
    def __init__(self):
        self.token_manager = TokenManager()
        self.password_manager = PasswordManager()
    
    async def authenticate_user(self, email: str, password: str, db_session) -> Optional[User]:
        """
        Authenticate user with email and password
        """
        from sqlalchemy import select
        
        try:
            # Get user by email
            stmt = select(User).where(User.email == email.lower())
            result = await db_session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning("Authentication failed: user not found", email=email)
                return None
            
            if not user.is_active:
                logger.warning("Authentication failed: user inactive", email=email, user_id=str(user.id))
                return None
            
            if not user.password_hash:
                logger.warning("Authentication failed: no password set", email=email, user_id=str(user.id))
                return None
            
            # Verify password
            if not self.password_manager.verify_password(password, user.password_hash):
                logger.warning("Authentication failed: invalid password", email=email, user_id=str(user.id))
                return None
            
            # Update last login
            user.last_login = datetime.utcnow()
            await db_session.commit()

            # Refresh user object to get updated timestamps from database triggers
            await db_session.refresh(user)

            logger.info("User authenticated successfully", email=email, user_id=str(user.id))
            return user
            
        except Exception as e:
            logger.error("Authentication error", email=email, error=str(e))
            return None
    
    async def create_user_session(self, user: User) -> Dict[str, str]:
        """
        Create user session with JWT tokens
        """
        # Create token payload
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "subscription_tier": user.subscription_tier,
            "is_admin": user.is_admin,
        }
        
        # Create tokens
        access_token = self.token_manager.create_access_token(token_data)
        refresh_token = self.token_manager.create_refresh_token({"sub": str(user.id)})
        
        # Store session in Redis
        session_data = {
            "user_id": str(user.id),
            "email": user.email,
            "subscription_tier": user.subscription_tier,
            "is_admin": user.is_admin,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        
        session_id = await session_manager.create_session(str(user.id), session_data)
        
        logger.info("User session created", user_id=str(user.id), session_id=session_id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.token_manager.access_token_expire_minutes * 60,
            "session_id": session_id
        }
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresh access token using refresh token
        """
        try:
            # Verify refresh token
            payload = self.token_manager.verify_token(refresh_token, "refresh")
            user_id = payload.get("sub")
            
            if not user_id:
                raise AuthenticationError("Invalid refresh token payload")
            
            # Get user session from Redis
            user_sessions = await session_manager.redis.get(f"user_sessions:{user_id}", [])
            
            # Find session with matching refresh token
            session_data = None
            for session_id in user_sessions:
                session = await session_manager.get_session(session_id)
                if session and session.get("refresh_token") == refresh_token:
                    session_data = session
                    break
            
            if not session_data:
                raise AuthenticationError("Refresh token not found in active sessions")
            
            # Create new access token
            token_data = {
                "sub": user_id,
                "email": session_data["email"],
                "subscription_tier": session_data["subscription_tier"],
                "is_admin": session_data["is_admin"],
            }
            
            new_access_token = self.token_manager.create_access_token(token_data)
            
            # Update session with new access token
            session_data["access_token"] = new_access_token
            await session_manager.redis.set(
                f"session:{session_data['session_id']}", 
                session_data, 
                self.token_manager.access_token_expire_minutes * 60
            )
            
            logger.info("Access token refreshed", user_id=user_id)
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": self.token_manager.access_token_expire_minutes * 60
            }
            
        except Exception as e:
            logger.error("Token refresh failed", error=str(e))
            raise AuthenticationError("Failed to refresh token")
    
    async def logout_user(self, session_id: str) -> bool:
        """
        Logout user by deleting session
        """
        try:
            success = await session_manager.delete_session(session_id)
            if success:
                logger.info("User logged out", session_id=session_id)
            return success
        except Exception as e:
            logger.error("Logout failed", session_id=session_id, error=str(e))
            return False
    
    async def logout_all_sessions(self, user_id: str) -> int:
        """
        Logout user from all sessions
        """
        try:
            count = await session_manager.delete_user_sessions(user_id)
            logger.info("All user sessions logged out", user_id=user_id, count=count)
            return count
        except Exception as e:
            logger.error("Logout all sessions failed", user_id=user_id, error=str(e))
            return 0

# Global auth service instance
auth_service = AuthService()

# Dependency functions for FastAPI
async def get_current_user_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """
    Extract JWT token from Authorization header
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials

async def get_current_user_payload(token: str = Depends(get_current_user_token)) -> Dict[str, Any]:
    """
    Get current user payload from JWT token
    """
    try:
        payload = auth_service.token_manager.verify_token(token)
        return payload
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(payload: Dict[str, Any] = Depends(get_current_user_payload)) -> Dict[str, Any]:
    """
    Get current user information from token payload
    """
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "id": user_id,
        "email": payload.get("email"),
        "subscription_tier": payload.get("subscription_tier"),
        "is_admin": payload.get("is_admin", False),
    }

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get current active user (additional validation can be added here)
    """
    return current_user

async def require_admin(current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, Any]:
    """
    Require admin privileges
    """
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

# Export commonly used items
__all__ = [
    "AuthService",
    "TokenManager", 
    "PasswordManager",
    "AuthenticationError",
    "AuthorizationError",
    "auth_service",
    "get_current_user",
    "get_current_active_user",
    "require_admin",
]
