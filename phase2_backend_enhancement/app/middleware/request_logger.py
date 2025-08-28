"""
Request Logger Middleware
Phase 2: Backend Enhancement

Middleware for logging HTTP requests and responses
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response information
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
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
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
