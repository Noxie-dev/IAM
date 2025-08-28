"""
Redis Client Configuration
Phase 2: Backend Enhancement

Async Redis client for caching, sessions, and rate limiting
"""

import json
import pickle
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta

import redis.asyncio as redis
import structlog
from redis.exceptions import RedisError

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Global Redis client
redis_client: Optional[redis.Redis] = None

async def init_redis() -> None:
    """
    Initialize Redis connection
    """
    global redis_client
    
    logger.info("🔗 Initializing Redis connection")
    
    try:
        # Create Redis client
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        
        # Test connection
        await redis_client.ping()
        
        # Get Redis info
        info = await redis_client.info()
        
        logger.info("✅ Redis connection established",
                   version=info.get("redis_version"),
                   host=settings.REDIS_HOST,
                   port=settings.REDIS_PORT)
        
    except Exception as e:
        logger.error("❌ Redis initialization failed", error=str(e))
        raise

async def close_redis() -> None:
    """
    Close Redis connection
    """
    global redis_client
    
    if redis_client:
        logger.info("🔌 Closing Redis connection")
        await redis_client.close()
        redis_client = None
        logger.info("✅ Redis connection closed")

async def get_redis() -> redis.Redis:
    """
    Get Redis client instance
    """
    if not redis_client:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return redis_client

async def get_redis_health() -> Dict[str, Any]:
    """
    Check Redis health for monitoring
    """
    if not redis_client:
        return {"status": "unhealthy", "error": "Redis not initialized"}
    
    try:
        # Test ping
        await redis_client.ping()
        
        # Get Redis info
        info = await redis_client.info()
        
        # Get memory usage
        memory_info = {
            "used_memory": info.get("used_memory"),
            "used_memory_human": info.get("used_memory_human"),
            "used_memory_peak": info.get("used_memory_peak"),
            "used_memory_peak_human": info.get("used_memory_peak_human"),
        }
        
        # Get connection info
        connection_info = {
            "connected_clients": info.get("connected_clients"),
            "total_connections_received": info.get("total_connections_received"),
            "rejected_connections": info.get("rejected_connections"),
        }
        
        return {
            "status": "healthy",
            "version": info.get("redis_version"),
            "uptime_seconds": info.get("uptime_in_seconds"),
            "memory": memory_info,
            "connections": connection_info,
        }
        
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }

class RedisManager:
    """
    High-level Redis operations manager
    """
    
    def __init__(self):
        self.client = None
    
    async def _get_client(self) -> redis.Redis:
        """Get Redis client"""
        if not self.client:
            self.client = await get_redis()
        return self.client
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from Redis with automatic deserialization
        """
        try:
            client = await self._get_client()
            value = await client.get(key)
            
            if value is None:
                return default
            
            # Try JSON first, then pickle, then return as string
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                try:
                    return pickle.loads(value.encode('latin1'))
                except:
                    return value
                    
        except RedisError as e:
            logger.error("Redis GET error", key=key, error=str(e))
            return default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in Redis with automatic serialization
        """
        try:
            client = await self._get_client()
            
            # Serialize value
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value)
            elif isinstance(value, (str, int, float, bool)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = pickle.dumps(value).decode('latin1')
            
            # Set with optional TTL
            if ttl:
                return await client.setex(key, ttl, serialized_value)
            else:
                return await client.set(key, serialized_value)
                
        except RedisError as e:
            logger.error("Redis SET error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            client = await self._get_client()
            return bool(await client.delete(key))
        except RedisError as e:
            logger.error("Redis DELETE error", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            client = await self._get_client()
            return bool(await client.exists(key))
        except RedisError as e:
            logger.error("Redis EXISTS error", key=key, error=str(e))
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for key"""
        try:
            client = await self._get_client()
            return bool(await client.expire(key, ttl))
        except RedisError as e:
            logger.error("Redis EXPIRE error", key=key, error=str(e))
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        try:
            client = await self._get_client()
            return await client.incr(key, amount)
        except RedisError as e:
            logger.error("Redis INCR error", key=key, error=str(e))
            return None
    
    async def get_keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern"""
        try:
            client = await self._get_client()
            return await client.keys(pattern)
        except RedisError as e:
            logger.error("Redis KEYS error", pattern=pattern, error=str(e))
            return []
    
    async def hash_set(self, key: str, field: str, value: Any) -> bool:
        """Set hash field"""
        try:
            client = await self._get_client()
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            return bool(await client.hset(key, field, serialized_value))
        except RedisError as e:
            logger.error("Redis HSET error", key=key, field=field, error=str(e))
            return False
    
    async def hash_get(self, key: str, field: str) -> Any:
        """Get hash field"""
        try:
            client = await self._get_client()
            value = await client.hget(key, field)
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except RedisError as e:
            logger.error("Redis HGET error", key=key, field=field, error=str(e))
            return None
    
    async def hash_get_all(self, key: str) -> Dict[str, Any]:
        """Get all hash fields"""
        try:
            client = await self._get_client()
            hash_data = await client.hgetall(key)
            
            # Deserialize values
            result = {}
            for field, value in hash_data.items():
                try:
                    result[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[field] = value
            
            return result
            
        except RedisError as e:
            logger.error("Redis HGETALL error", key=key, error=str(e))
            return {}

class SessionManager:
    """
    Redis-based session management for JWT tokens
    """
    
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
        self.default_ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    async def create_session(self, user_id: str, session_data: Dict[str, Any], ttl: Optional[int] = None) -> str:
        """Create new user session"""
        import hashlib
        import os
        
        # Generate session ID
        timestamp = datetime.utcnow().isoformat()
        data = f"{user_id}:{timestamp}:{os.urandom(16).hex()}"
        session_id = hashlib.sha256(data.encode()).hexdigest()
        
        session_key = f"{self.session_prefix}{session_id}"
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        
        # Add metadata
        session_data.update({
            "user_id": user_id,
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat()
        })
        
        # Store session data
        ttl = ttl or self.default_ttl
        await self.redis.set(session_key, session_data, ttl)
        
        # Track user sessions
        user_sessions = await self.redis.get(user_sessions_key, [])
        if session_id not in user_sessions:
            user_sessions.append(session_id)
            await self.redis.set(user_sessions_key, user_sessions, ttl)
        
        logger.info("Session created", user_id=user_id, session_id=session_id)
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        session_key = f"{self.session_prefix}{session_id}"
        session_data = await self.redis.get(session_key)
        
        if session_data:
            # Update last accessed time
            session_data['last_accessed'] = datetime.utcnow().isoformat()
            await self.redis.set(session_key, session_data, self.default_ttl)
        
        return session_data
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        session_key = f"{self.session_prefix}{session_id}"
        
        # Get session data to find user_id
        session_data = await self.redis.get(session_key)
        if session_data and 'user_id' in session_data:
            user_id = session_data['user_id']
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            
            # Remove from user sessions list
            user_sessions = await self.redis.get(user_sessions_key, [])
            if session_id in user_sessions:
                user_sessions.remove(session_id)
                await self.redis.set(user_sessions_key, user_sessions)
        
        return await self.redis.delete(session_key)
    
    async def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user"""
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        user_sessions = await self.redis.get(user_sessions_key, [])
        
        deleted_count = 0
        for session_id in user_sessions:
            session_key = f"{self.session_prefix}{session_id}"
            if await self.redis.delete(session_key):
                deleted_count += 1
        
        # Clear user sessions list
        await self.redis.delete(user_sessions_key)
        
        logger.info("Deleted user sessions", user_id=user_id, count=deleted_count)
        return deleted_count

class RateLimiter:
    """
    Redis-based rate limiting
    """
    
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager
        self.rate_limit_prefix = "rate_limit:"
    
    async def is_allowed(self, identifier: str, limit: int, window: int) -> Dict[str, Any]:
        """Check if request is allowed under rate limit"""
        key = f"{self.rate_limit_prefix}{identifier}"
        
        try:
            # Get current count
            current_count = await self.redis.get(key, 0)
            
            if isinstance(current_count, str):
                current_count = int(current_count)
            
            if current_count >= limit:
                # Rate limit exceeded
                client = await get_redis()
                ttl = await client.ttl(key)
                return {
                    'allowed': False,
                    'current_count': current_count,
                    'limit': limit,
                    'reset_time': ttl,
                    'retry_after': ttl
                }
            
            # Increment counter
            new_count = await self.redis.increment(key)
            
            # Set expiration on first request
            if new_count == 1:
                await self.redis.expire(key, window)
            
            return {
                'allowed': True,
                'current_count': new_count,
                'limit': limit,
                'remaining': limit - new_count,
                'reset_time': window
            }
            
        except Exception as e:
            logger.error("Rate limiting error", identifier=identifier, error=str(e))
            # Allow request on error (fail open)
            return {
                'allowed': True,
                'current_count': 0,
                'limit': limit,
                'remaining': limit,
                'error': str(e)
            }

# Create global instances
redis_manager = RedisManager()
session_manager = SessionManager(redis_manager)
rate_limiter = RateLimiter(redis_manager)

# Export commonly used items
__all__ = [
    "init_redis",
    "close_redis",
    "get_redis",
    "get_redis_health",
    "redis_manager",
    "session_manager",
    "rate_limiter",
]
