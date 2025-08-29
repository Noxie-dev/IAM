"""
Celery Application Configuration
Phase 2: Backend Enhancement + DICE™ Integration

Celery setup for asynchronous task processing including DICE™ pipeline
"""

import asyncio
import logging
from typing import Any
from celery import Celery
from celery.signals import worker_init, worker_shutdown

from app.core.config import get_settings
from app.core.database import init_db, close_db

logger = logging.getLogger(__name__)
settings = get_settings()

# Create Celery instance
celery_app = Celery(
    "iam_saas",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.dice_tasks",
        "app.tasks.transcription_tasks",
        "app.tasks.notification_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.tasks.dice_tasks.*": {"queue": "dice_processing"},
        "app.tasks.transcription_tasks.*": {"queue": "transcription"},
        "app.tasks.notification_tasks.*": {"queue": "notifications"}
    },
    
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_max_retries=3,
    
    # Task retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-expired-jobs": {
            "task": "app.tasks.maintenance_tasks.cleanup_expired_jobs",
            "schedule": 3600.0,  # Run every hour
        },
        "update-usage-analytics": {
            "task": "app.tasks.analytics_tasks.update_usage_analytics",
            "schedule": 300.0,  # Run every 5 minutes
        }
    }
)

@worker_init.connect
def worker_init_handler(sender=None, **kwargs):
    """Initialize worker resources"""
    logger.info("🚀 Initializing Celery worker")
    
    # Initialize database connections
    # Note: In Celery workers, we need to handle async initialization carefully
    try:
        # For now, we'll initialize database connections when needed in tasks
        logger.info("✅ Celery worker initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Celery worker: {e}")
        raise

@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Cleanup worker resources"""
    logger.info("🛑 Shutting down Celery worker")
    
    try:
        # Cleanup will be handled in individual tasks
        logger.info("✅ Celery worker shutdown complete")
    except Exception as e:
        logger.error(f"❌ Error during Celery worker shutdown: {e}")

# Task decorator that handles async database operations
def async_task(func):
    """Decorator to handle async database operations in Celery tasks"""
    def wrapper(*args, **kwargs):
        # Create a new event loop for the task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the async function
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            # Clean up the event loop
            loop.close()
    
    return wrapper

if __name__ == "__main__":
    # For running Celery worker directly
    celery_app.start()




