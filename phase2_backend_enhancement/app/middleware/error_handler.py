"""
Error Handler Middleware
Phase 2: Backend Enhancement

Comprehensive error handling middleware with structured logging
"""

import traceback
from typing import Callable, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle all application errors with structured logging
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and handle any errors that occur
        """
        try:
            # Process the request
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # FastAPI HTTP exceptions - pass through with logging
            logger.warning(
                "HTTP exception occurred",
                status_code=e.status_code,
                detail=e.detail,
                path=request.url.path,
                method=request.method,
                user_agent=request.headers.get("user-agent"),
                client_ip=self._get_client_ip(request)
            )
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "error": e.detail,
                    "error_type": "http_error",
                    "status_code": e.status_code,
                    "path": request.url.path,
                    "method": request.method
                }
            )
            
        except ValueError as e:
            # Validation errors
            logger.warning(
                "Validation error occurred",
                error=str(e),
                path=request.url.path,
                method=request.method,
                client_ip=self._get_client_ip(request)
            )
            
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": str(e),
                    "error_type": "validation_error",
                    "status_code": 400
                }
            )
            
        except PermissionError as e:
            # Permission/authorization errors
            logger.warning(
                "Permission error occurred",
                error=str(e),
                path=request.url.path,
                method=request.method,
                client_ip=self._get_client_ip(request)
            )
            
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error": "Permission denied",
                    "error_type": "permission_error",
                    "status_code": 403
                }
            )
            
        except ConnectionError as e:
            # Database/Redis connection errors
            logger.error(
                "Connection error occurred",
                error=str(e),
                path=request.url.path,
                method=request.method,
                client_ip=self._get_client_ip(request)
            )
            
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": "Service temporarily unavailable. Please try again later.",
                    "error_type": "connection_error",
                    "status_code": 503
                }
            )
            
        except Exception as e:
            if "timeout" in str(e).lower():
                # Timeout errors
                logger.error(
                    "Timeout error occurred",
                    error=str(e),
                    path=request.url.path,
                    method=request.method,
                    client_ip=self._get_client_ip(request)
                )

                return JSONResponse(
                    status_code=504,
                    content={
                        "success": False,
                        "error": "Request timeout. Please try again.",
                        "error_type": "timeout_error",
                        "status_code": 504
                    }
                )
            
        except Exception as e:
            # Unhandled exceptions
            error_id = self._generate_error_id()
            
            logger.error(
                "Unhandled exception occurred",
                error_id=error_id,
                error=str(e),
                error_type=type(e).__name__,
                path=request.url.path,
                method=request.method,
                user_agent=request.headers.get("user-agent"),
                client_ip=self._get_client_ip(request),
                traceback=traceback.format_exc() if settings.DEBUG else None
            )
            
            # Return different responses based on environment
            if settings.DEBUG:
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error": str(e),
                        "error_type": "server_error",
                        "error_id": error_id,
                        "status_code": 500,
                        "traceback": traceback.format_exc()
                    }
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error": "An internal server error occurred. Please try again later.",
                        "error_type": "server_error",
                        "error_id": error_id,
                        "status_code": 500
                    }
                )
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request headers
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
    
    def _generate_error_id(self) -> str:
        """
        Generate unique error ID for tracking
        """
        import uuid
        return str(uuid.uuid4())[:8]


class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle maintenance mode
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Check if application is in maintenance mode
        """
        if settings.MAINTENANCE_MODE:
            # Allow health checks and admin endpoints during maintenance
            allowed_paths = ["/health", "/api/v2/health", "/docs", "/redoc"]
            
            if not any(request.url.path.startswith(path) for path in allowed_paths):
                return JSONResponse(
                    status_code=503,
                    content={
                        "success": False,
                        "error": "Application is currently under maintenance. Please try again later.",
                        "error_type": "maintenance_mode",
                        "status_code": 503
                    }
                )
        
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add security headers to response
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all requests
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response information
        """
        import time
        
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params) if request.query_params else None,
            user_agent=request.headers.get("user-agent"),
            client_ip=self._get_client_ip(request)
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time=round(process_time, 4),
            client_ip=self._get_client_ip(request)
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
