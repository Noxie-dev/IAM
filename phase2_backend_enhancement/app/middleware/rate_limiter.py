"""
Rate Limiter Middleware
Phase 2: Backend Enhancement

Redis-based rate limiting middleware with subscription tier support
"""

import time
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.core.config import settings
from app.core.redis_client import rate_limiter
from app.core.auth import auth_service

logger = structlog.get_logger(__name__)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware based on user subscription tier
    """
    
    def __init__(self, app, window_seconds: int = 3600):  # 1 hour window
        super().__init__(app)
        self.window_seconds = window_seconds
        
        # Paths that are exempt from rate limiting
        self.exempt_paths = [
            "/health",
            "/api/v2/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics"
        ]
        
        # Different rate limits for different endpoint types
        self.endpoint_multipliers = {
            "/api/v2/auth/login": 0.5,      # Less restrictive for development
            "/api/v2/auth/register": 0.5,   # Less restrictive for development
            "/api/v2/transcription": 2.0,   # More generous for main feature
            "/api/v2/meetings": 1.0,        # Standard rate
            "/api/v2/users": 0.5,           # More restrictive for user management
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Apply rate limiting based on user subscription tier
        """
        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Get user information for rate limiting
        user_info = await self._get_user_info(request)
        
        # Determine rate limit
        rate_limit = self._get_rate_limit(user_info)
        
        # Skip rate limiting for unlimited plans
        if rate_limit == -1:
            return await call_next(request)
        
        # Apply endpoint-specific multiplier
        effective_limit = self._apply_endpoint_multiplier(request.url.path, rate_limit)
        
        # Create rate limiting identifier
        identifier = self._create_identifier(request, user_info)
        
        # Check rate limit
        rate_limit_result = await rate_limiter.is_allowed(
            identifier, 
            effective_limit, 
            self.window_seconds
        )
        
        if not rate_limit_result['allowed']:
            # Rate limit exceeded
            logger.warning(
                "Rate limit exceeded",
                identifier=identifier,
                current_count=rate_limit_result['current_count'],
                limit=effective_limit,
                path=request.url.path,
                method=request.method,
                user_id=user_info.get('user_id') if user_info else None
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Rate limit exceeded. Please try again later.",
                    "error_type": "rate_limit_exceeded",
                    "status_code": 429,
                    "rate_limit": {
                        "limit": effective_limit,
                        "current": rate_limit_result['current_count'],
                        "reset_time": rate_limit_result.get('retry_after', 0),
                        "window_seconds": self.window_seconds
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(effective_limit),
                    "X-RateLimit-Remaining": str(max(0, effective_limit - rate_limit_result['current_count'])),
                    "X-RateLimit-Reset": str(int(time.time()) + rate_limit_result.get('retry_after', 0)),
                    "Retry-After": str(rate_limit_result.get('retry_after', 0))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(effective_limit)
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_result.get('remaining', 0))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.window_seconds)
        
        return response
    
    async def _get_user_info(self, request: Request) -> Optional[dict]:
        """
        Extract user information from request for rate limiting
        """
        try:
            # Try to get user from Authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.split(" ")[1]
            payload = auth_service.token_manager.verify_token(token)
            
            return {
                "user_id": payload.get("sub"),
                "subscription_tier": payload.get("subscription_tier", "free"),
                "is_admin": payload.get("is_admin", False)
            }
            
        except Exception as e:
            # If token verification fails, treat as anonymous user
            logger.debug("Could not extract user info for rate limiting", error=str(e))
            return None
    
    def _get_rate_limit(self, user_info: Optional[dict]) -> int:
        """
        Get rate limit based on user subscription tier
        """
        if not user_info:
            # Anonymous users get free tier limits
            return settings.RATE_LIMIT_FREE
        
        if user_info.get("is_admin"):
            # Admins get unlimited access
            return -1
        
        tier = user_info.get("subscription_tier", "free")
        return settings.get_rate_limit_for_tier(tier)
    
    def _apply_endpoint_multiplier(self, path: str, base_limit: int) -> int:
        """
        Apply endpoint-specific rate limit multipliers
        """
        if base_limit == -1:  # Unlimited
            return -1
        
        # Find matching endpoint pattern
        multiplier = 1.0
        for pattern, mult in self.endpoint_multipliers.items():
            if path.startswith(pattern):
                multiplier = mult
                break
        
        return max(1, int(base_limit * multiplier))
    
    def _create_identifier(self, request: Request, user_info: Optional[dict]) -> str:
        """
        Create unique identifier for rate limiting
        """
        if user_info and user_info.get("user_id"):
            # Use user ID for authenticated users
            return f"user:{user_info['user_id']}"
        else:
            # Use IP address for anonymous users
            client_ip = self._get_client_ip(request)
            return f"ip:{client_ip}"
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request
        """
        # Check for forwarded headers (load balancer/proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"


class APIKeyRateLimiter:
    """
    Separate rate limiter for API key based access
    """
    
    def __init__(self, window_seconds: int = 3600):
        self.window_seconds = window_seconds
    
    async def check_api_key_limit(self, api_key: str, limit: int) -> dict:
        """
        Check rate limit for API key
        """
        identifier = f"api_key:{api_key}"
        return await rate_limiter.is_allowed(identifier, limit, self.window_seconds)


class BurstRateLimiter:
    """
    Additional burst rate limiter for short-term protection
    """
    
    def __init__(self, burst_limit: int = 10, burst_window: int = 60):
        self.burst_limit = burst_limit
        self.burst_window = burst_window
    
    async def check_burst_limit(self, identifier: str) -> dict:
        """
        Check burst rate limit (short-term high frequency protection)
        """
        burst_identifier = f"burst:{identifier}"
        return await rate_limiter.is_allowed(
            burst_identifier, 
            self.burst_limit, 
            self.burst_window
        )


# Global instances
api_key_rate_limiter = APIKeyRateLimiter()
burst_rate_limiter = BurstRateLimiter()


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log requests with rate limiting information
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request with timing and rate limit information
        """
        start_time = time.time()
        
        # Get client info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log request start
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            user_agent=user_agent,
            query_params=dict(request.query_params) if request.query_params else None
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log request completion
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time=round(process_time, 4),
            client_ip=client_ip,
            rate_limit_remaining=response.headers.get("X-RateLimit-Remaining"),
            rate_limit_limit=response.headers.get("X-RateLimit-Limit")
        )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
