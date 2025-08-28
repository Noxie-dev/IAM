#!/usr/bin/env python3
"""
IAM SaaS Platform - FastAPI Application
Phase 2: Backend Enhancement

Main FastAPI application with async support, authentication, and enhanced error handling.
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

import structlog
from prometheus_client import make_asgi_app
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

# Import our modules
from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.redis_client import init_redis, close_redis
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.request_logger import RequestLoggerMiddleware

# Import API routers
from app.api.v2 import api_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Initialize Sentry for error tracking
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(auto_enabling=True),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting IAM SaaS Platform API")
    
    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized")
        
        # Initialize Redis (temporarily disabled - Redis connection issues)
        # await init_redis()
        # logger.info("✅ Redis initialized")
        
        # Log startup completion
        logger.info("🎉 Application startup completed", 
                   environment=settings.ENVIRONMENT,
                   debug=settings.DEBUG)
        
        yield
        
    except Exception as e:
        logger.error("❌ Application startup failed", error=str(e))
        raise
    
    finally:
        # Shutdown
        logger.info("🛑 Shutting down IAM SaaS Platform API")
        
        try:
            # await close_redis()
            # logger.info("✅ Redis connections closed")
            
            await close_db()
            logger.info("✅ Database connections closed")
            
        except Exception as e:
            logger.error("❌ Error during shutdown", error=str(e))

# Create FastAPI application
app = FastAPI(
    title="IAM SaaS Platform API",
    description="""
    **IAM (In A Meeting) SaaS Platform API**
    
    A comprehensive transcription service platform with:
    
    * 🎤 **Audio Transcription** - High-quality speech-to-text conversion
    * 👥 **User Management** - Complete authentication and authorization
    * 💳 **Subscription Management** - Flexible pricing tiers
    * 📊 **Analytics** - Usage tracking and insights
    * 🔒 **Security** - JWT authentication with rate limiting
    * 🚀 **Performance** - Async processing with Redis caching
    
    ## Authentication
    
    Most endpoints require authentication using JWT tokens:
    
    1. Register or login to get an access token
    2. Include the token in the Authorization header: `Bearer <token>`
    3. Tokens expire after 24 hours and can be refreshed
    
    ## Rate Limits
    
    API calls are rate-limited based on subscription tier:
    
    * **Free**: 100 requests/hour
    * **Basic**: 500 requests/hour  
    * **Premium**: 2000 requests/hour
    * **Enterprise**: Unlimited
    
    ## Support
    
    For support, contact: support@iam-app.com
    """,
    version="2.0.0",
    contact={
        "name": "IAM Support Team",
        "email": "support@iam-app.com",
    },
    license_info={
        "name": "Proprietary",
    },
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add middleware (order matters!)

# 1. Trusted Host Middleware (security)
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 3. Request Logger Middleware
app.add_middleware(RequestLoggerMiddleware)

# 4. Rate Limiter Middleware (temporarily disabled - Redis connection issues)
# app.add_middleware(RateLimiterMiddleware)

# 5. Error Handler Middleware (should be last)
app.add_middleware(ErrorHandlerMiddleware)

# Include API routers
app.include_router(api_router, prefix="/api/v2")

# Add Prometheus metrics endpoint
if settings.ENABLE_METRICS:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for load balancers and monitoring
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": structlog.processors.TimeStamper(fmt="iso")._stamper()
    }

@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """
    Detailed health check with service dependencies
    """
    from app.core.database import get_db_health
    from app.core.redis_client import get_redis_health
    
    health_status = {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "services": {}
    }
    
    # Check database
    try:
        db_health = await get_db_health()
        health_status["services"]["database"] = db_health
    except Exception as e:
        health_status["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        redis_health = await get_redis_health()
        health_status["services"]["redis"] = redis_health
    except Exception as e:
        health_status["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    return health_status

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="IAM SaaS Platform API",
        version="2.0.0",
        description=app.description,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom HTTP exception handler with structured logging
    """
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "error_type": "http_error",
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    General exception handler for unhandled exceptions
    """
    logger.error(
        "Unhandled exception occurred",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error" if not settings.DEBUG else str(exc),
            "error_type": "server_error",
            "status_code": 500
        }
    )

# Development server
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
        access_log=True,
    )
