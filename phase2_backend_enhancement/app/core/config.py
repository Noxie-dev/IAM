"""
Application Configuration
Phase 2: Backend Enhancement

Centralized configuration management using Pydantic Settings
"""

import os
from typing import List, Optional, Any, Dict
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support
    """
    
    # Application
    APP_NAME: str = "IAM SaaS Platform"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # API Configuration
    API_V2_PREFIX: str = "/api/v2"
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
        ],
        env="CORS_ORIGINS"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        env="ALLOWED_HOSTS"
    )
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://iam_user:secure_password_123@localhost:5433/iam_saas",
        env="DATABASE_URL"
    )
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=30, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    DB_POOL_RECYCLE: int = Field(default=3600, env="DB_POOL_RECYCLE")
    
    # Redis Configuration
    REDIS_URL: str = Field(
        default="redis://:redis_password_123@localhost:6379/0",
        env="REDIS_URL"
    )
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(default="redis_password_123", env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    
    # Authentication & Security
    SECRET_KEY: str = Field(
        default="your_super_secure_jwt_secret_key_here_change_in_production",
        env="JWT_SECRET_KEY"
    )
    ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Password Security
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_HASH_ROUNDS: int = Field(default=12, env="PASSWORD_HASH_ROUNDS")
    
    # Rate Limiting
    RATE_LIMIT_FREE: int = Field(default=100, env="RATE_LIMIT_FREE")
    RATE_LIMIT_BASIC: int = Field(default=500, env="RATE_LIMIT_BASIC")
    RATE_LIMIT_PREMIUM: int = Field(default=2000, env="RATE_LIMIT_PREMIUM")
    RATE_LIMIT_ENTERPRISE: int = Field(default=-1, env="RATE_LIMIT_ENTERPRISE")
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    TRANSCRIPTION_PROVIDERS: List[str] = Field(
        default=["openai", "azure", "google"],
        env="TRANSCRIPTION_PROVIDERS"
    )
    DEFAULT_TRANSCRIPTION_PROVIDER: str = Field(
        default="openai",
        env="DEFAULT_TRANSCRIPTION_PROVIDER"
    )
    
    # File Storage (S3/Wasabi)
    S3_ENDPOINT_URL: str = Field(
        default="https://s3.wasabisys.com",
        env="S3_ENDPOINT_URL"
    )
    S3_ACCESS_KEY: Optional[str] = Field(env="S3_ACCESS_KEY")
    S3_SECRET_KEY: Optional[str] = Field(env="S3_SECRET_KEY")
    S3_BUCKET_NAME: str = Field(
        default="iam-transcription-files",
        env="S3_BUCKET_NAME"
    )
    S3_REGION: str = Field(default="us-east-1", env="S3_REGION")
    
    # File Upload Limits
    MAX_FILE_SIZE_MB: int = Field(default=250, env="MAX_FILE_SIZE_MB")
    SUPPORTED_AUDIO_FORMATS: List[str] = Field(
        default=["mp3", "wav", "m4a", "mp4", "mpeg", "mpga", "ogg", "webm", "flac"],
        env="SUPPORTED_AUDIO_FORMATS"
    )
    
    # Payment Gateways (South African)
    STITCH_CLIENT_ID: Optional[str] = Field(default=None, env="STITCH_CLIENT_ID")
    STITCH_CLIENT_SECRET: Optional[str] = Field(default=None, env="STITCH_CLIENT_SECRET")
    STITCH_ENVIRONMENT: str = Field(default="sandbox", env="STITCH_ENVIRONMENT")

    PAYGATE_ID: Optional[str] = Field(default=None, env="PAYGATE_ID")
    PAYGATE_SECRET: Optional[str] = Field(default=None, env="PAYGATE_SECRET")
    PAYGATE_ENVIRONMENT: str = Field(default="test", env="PAYGATE_ENVIRONMENT")

    STRIPE_PUBLISHABLE_KEY: Optional[str] = Field(default=None, env="STRIPE_PUBLISHABLE_KEY")
    STRIPE_SECRET_KEY: Optional[str] = Field(default=None, env="STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(default=None, env="STRIPE_WEBHOOK_SECRET")
    
    # Monitoring & Logging
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")

    # Email Configuration
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_FROM_EMAIL: str = Field(
        default="noreply@iam-app.com",
        env="SMTP_FROM_EMAIL"
    )
    
    # Business Configuration
    SUBSCRIPTION_PLANS: Dict[str, Dict[str, Any]] = {
        "free": {
            "name": "Free Plan",
            "price_zar": 0.00,
            "price_usd": 0.00,
            "monthly_minutes": 60,
            "max_file_size_mb": 25,
            "features": {
                "support": "community",
                "export_formats": ["txt"],
                "retention_days": 30
            }
        },
        "basic": {
            "name": "Basic Plan",
            "price_zar": 180.00,
            "price_usd": 10.00,
            "monthly_minutes": 300,
            "max_file_size_mb": 50,
            "features": {
                "support": "email",
                "export_formats": ["txt", "pdf"],
                "retention_days": 90,
                "priority_processing": False
            }
        },
        "premium": {
            "name": "Premium Plan",
            "price_zar": 360.00,
            "price_usd": 20.00,
            "monthly_minutes": 1200,
            "max_file_size_mb": 100,
            "features": {
                "support": "priority",
                "export_formats": ["txt", "pdf", "docx", "srt"],
                "retention_days": 365,
                "priority_processing": True,
                "api_access": True
            }
        },
        "enterprise": {
            "name": "Enterprise Plan",
            "price_zar": 720.00,
            "price_usd": 40.00,
            "monthly_minutes": -1,  # Unlimited
            "max_file_size_mb": 250,
            "features": {
                "support": "dedicated",
                "export_formats": ["txt", "pdf", "docx", "srt"],
                "retention_days": -1,  # Unlimited
                "priority_processing": True,
                "api_access": True,
                "custom_integrations": True
            }
        }
    }
    
    # Feature Flags
    ENABLE_REGISTRATION: bool = Field(default=True, env="ENABLE_REGISTRATION")
    ENABLE_SOCIAL_LOGIN: bool = Field(default=False, env="ENABLE_SOCIAL_LOGIN")
    ENABLE_TEAM_FEATURES: bool = Field(default=False, env="ENABLE_TEAM_FEATURES")
    ENABLE_API_ACCESS: bool = Field(default=False, env="ENABLE_API_ACCESS")
    ENABLE_WEBHOOKS: bool = Field(default=False, env="ENABLE_WEBHOOKS")
    MAINTENANCE_MODE: bool = Field(default=False, env="MAINTENANCE_MODE")
    
    # Celery Configuration (Background Tasks)
    CELERY_BROKER_URL: str = Field(
        default="redis://:redis_password_123@localhost:6379/1",
        env="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://:redis_password_123@localhost:6379/2",
        env="CELERY_RESULT_BACKEND"
    )
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v):
        """Parse allowed hosts from string or list"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @field_validator("TRANSCRIPTION_PROVIDERS", mode="before")
    @classmethod
    def assemble_transcription_providers(cls, v):
        """Parse transcription providers from string or list"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @field_validator("SUPPORTED_AUDIO_FORMATS", mode="before")
    @classmethod
    def assemble_audio_formats(cls, v):
        """Parse audio formats from string or list"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Get CORS origins for middleware"""
        return self.BACKEND_CORS_ORIGINS
    
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Get synchronous database URL for Alembic"""
        return self.DATABASE_URL.replace("+asyncpg", "")
    
    def get_rate_limit_for_tier(self, tier: str) -> int:
        """Get rate limit for subscription tier"""
        rate_limits = {
            "free": self.RATE_LIMIT_FREE,
            "basic": self.RATE_LIMIT_BASIC,
            "premium": self.RATE_LIMIT_PREMIUM,
            "enterprise": self.RATE_LIMIT_ENTERPRISE,
        }
        return rate_limits.get(tier, self.RATE_LIMIT_FREE)
    
    def get_subscription_plan(self, tier: str) -> Dict[str, Any]:
        """Get subscription plan details"""
        return self.SUBSCRIPTION_PLANS.get(tier, self.SUBSCRIPTION_PLANS["free"])
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance"""
    return settings


# Validate critical settings
def validate_settings():
    """Validate critical application settings"""
    errors = []

    if not settings.SECRET_KEY or settings.SECRET_KEY == "your_super_secure_jwt_secret_key_here_change_in_production":
        if settings.ENVIRONMENT == "production":
            errors.append("SECRET_KEY must be set to a secure value in production")

    # Temporarily disable OpenAI API key validation for development
    # if not settings.OPENAI_API_KEY:
    #     errors.append("OPENAI_API_KEY is required for transcription services")

    if settings.ENVIRONMENT == "production":
        if settings.DEBUG:
            errors.append("DEBUG should be False in production")

        if not settings.SENTRY_DSN:
            errors.append("SENTRY_DSN should be configured for production error tracking")

    if errors:
        raise ValueError(f"Configuration errors: {'; '.join(errors)}")

# Validate settings on import
validate_settings()
