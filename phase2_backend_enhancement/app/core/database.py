"""
Async Database Configuration
Phase 2: Backend Enhancement

SQLAlchemy 2.0 with async support and PostgreSQL connection
"""

import asyncio
from typing import AsyncGenerator, Dict, Any
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import NullPool
from sqlalchemy import text, MetaData
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Database engine and session maker
engine: AsyncEngine | None = None
async_session_maker: async_sessionmaker[AsyncSession] | None = None

# SQLAlchemy Base
class Base(DeclarativeBase):
    """
    Base class for all database models
    """
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )

async def init_db() -> None:
    """
    Initialize database connection and create engine
    """
    global engine, async_session_maker
    
    logger.info("🔗 Initializing database connection")
    
    try:
        # Create async engine
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=True,  # Validate connections before use
            poolclass=NullPool if settings.ENVIRONMENT == "test" else None,
        )
        
        # Create session maker
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )
        
        # Test connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        logger.info("✅ Database connection established", 
                   url=settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL)
        
    except Exception as e:
        logger.error("❌ Database initialization failed", error=str(e))
        raise

async def close_db() -> None:
    """
    Close database connections
    """
    global engine
    
    if engine:
        logger.info("🔌 Closing database connections")
        await engine.dispose()
        engine = None
        logger.info("✅ Database connections closed")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session
    
    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            # Use db session
    """
    if not async_session_maker:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager to get database session
    
    Usage:
        async with get_db_session() as db:
            # Use db session
    """
    if not async_session_maker:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()

async def get_db_health() -> Dict[str, Any]:
    """
    Check database health for monitoring
    """
    if not engine:
        return {"status": "unhealthy", "error": "Database not initialized"}
    
    try:
        async with engine.begin() as conn:
            # Test basic query
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            
            # Test connection pool
            pool = engine.pool
            pool_status = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
            }
            
            return {
                "status": "healthy",
                "version": version,
                "pool": pool_status,
                "url": settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else "hidden"
            }
            
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }

class DatabaseManager:
    """
    Database manager for advanced operations
    """
    
    def __init__(self):
        self.engine = engine
        self.session_maker = async_session_maker
    
    async def execute_raw_query(self, query: str, params: Dict[str, Any] = None) -> Any:
        """
        Execute raw SQL query
        """
        async with get_db_session() as db:
            result = await db.execute(text(query), params or {})
            await db.commit()
            return result
    
    async def get_table_stats(self) -> Dict[str, Any]:
        """
        Get database table statistics
        """
        query = """
        SELECT 
            schemaname,
            tablename,
            attname,
            n_distinct,
            correlation
        FROM pg_stats 
        WHERE schemaname = 'public'
        ORDER BY tablename, attname;
        """
        
        async with get_db_session() as db:
            result = await db.execute(text(query))
            rows = result.fetchall()
            
            stats = {}
            for row in rows:
                table = row.tablename
                if table not in stats:
                    stats[table] = {}
                stats[table][row.attname] = {
                    "n_distinct": row.n_distinct,
                    "correlation": row.correlation
                }
            
            return stats
    
    async def analyze_tables(self) -> None:
        """
        Run ANALYZE on all tables for query optimization
        """
        query = """
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public';
        """
        
        async with get_db_session() as db:
            result = await db.execute(text(query))
            tables = [row.tablename for row in result.fetchall()]
            
            for table in tables:
                await db.execute(text(f"ANALYZE {table};"))
                logger.info(f"Analyzed table: {table}")
            
            await db.commit()
            logger.info(f"Analyzed {len(tables)} tables")

# Create global database manager instance
db_manager = DatabaseManager()

# Transaction decorator
def transactional(func):
    """
    Decorator to wrap function in database transaction
    
    Usage:
        @transactional
        async def create_user(db: AsyncSession, user_data: dict):
            # This will be wrapped in a transaction
            pass
    """
    async def wrapper(*args, **kwargs):
        # Find AsyncSession in arguments
        db_session = None
        for arg in args:
            if isinstance(arg, AsyncSession):
                db_session = arg
                break
        
        if not db_session:
            # Look in kwargs
            for value in kwargs.values():
                if isinstance(value, AsyncSession):
                    db_session = value
                    break
        
        if not db_session:
            raise ValueError("No AsyncSession found in function arguments")
        
        try:
            result = await func(*args, **kwargs)
            await db_session.commit()
            return result
        except Exception as e:
            await db_session.rollback()
            logger.error("Transaction rolled back", error=str(e))
            raise
    
    return wrapper

# Database utilities
async def create_tables():
    """
    Create all database tables (for development/testing)
    """
    if not engine:
        raise RuntimeError("Database not initialized")
    
    logger.info("Creating database tables")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✅ Database tables created")

async def drop_tables():
    """
    Drop all database tables (for development/testing)
    """
    if not engine:
        raise RuntimeError("Database not initialized")
    
    logger.warning("Dropping all database tables")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.warning("⚠️ All database tables dropped")

# Export commonly used items
__all__ = [
    "Base",
    "init_db",
    "close_db",
    "get_db",
    "get_db_session",
    "get_db_health",
    "db_manager",
    "transactional",
    "create_tables",
    "drop_tables",
]
