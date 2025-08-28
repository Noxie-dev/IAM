#!/usr/bin/env python3
"""
Redis Caching Configuration
Phase 1: Infrastructure - Caching Layer Setup

This module provides Redis caching functionality for session management,
rate limiting, and performance optimization.
"""

import redis
import json
import pickle
import os
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Union
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)

class RedisManager:
    """
    Redis cache manager with connection pooling and error handling
    """
    
    def __init__(self, 
                 host: str = None,
                 port: int = None,
                 password: str = None,
                 db: int = 0,
                 max_connections: int = 20):
        """
        Initialize Redis manager
        
        Args:
            host: Redis server host
            port: Redis server port
            password: Redis password
            db: Redis database number
            max_connections: Maximum connections in pool
        """
        
        # Load from environment if not provided
        self.host = host or os.getenv('REDIS_HOST', 'localhost')
        self.port = port or int(os.getenv('REDIS_PORT', '6379'))
        self.password = password or os.getenv('REDIS_PASSWORD')
        self.db = db or int(os.getenv('REDIS_DB', '0'))
        
        # Create connection pool
        self.pool = redis.ConnectionPool(
            host=self.host,
            port=self.port,
            password=self.password,
            db=self.db,
            max_connections=max_connections,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        # Create Redis client
        self.redis_client = redis.Redis(connection_pool=self.pool)
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test Redis connection"""
        try:
            self.redis_client.ping()
            logger.info(f"Redis connection successful: {self.host}:{self.port}")
        except redis.ConnectionError as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from Redis cache
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        try:
            value = self.redis_client.get(key)
            if value is None:
                return default
            
            # Try to deserialize JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                try:
                    return pickle.loads(value.encode('latin1'))
                except:
                    return value
                    
        except redis.RedisError as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set value in Redis cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Serialize value
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value)
            elif isinstance(value, (str, int, float, bool)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = pickle.dumps(value).decode('latin1')
            
            # Set with optional TTL
            if ttl:
                return self.redis_client.setex(key, ttl, serialized_value)
            else:
                return self.redis_client.set(key, serialized_value)
                
        except redis.RedisError as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            return bool(self.redis_client.delete(key))
        except redis.RedisError as e:
            logger.error(f"Redis DELETE error for key '{key}': {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            return bool(self.redis_client.exists(key))
        except redis.RedisError as e:
            logger.error(f"Redis EXISTS error for key '{key}': {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for key"""
        try:
            return bool(self.redis_client.expire(key, ttl))
        except redis.RedisError as e:
            logger.error(f"Redis EXPIRE error for key '{key}': {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        try:
            return self.redis_client.incr(key, amount)
        except redis.RedisError as e:
            logger.error(f"Redis INCR error for key '{key}': {e}")
            return None
    
    def get_keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern"""
        try:
            return self.redis_client.keys(pattern)
        except redis.RedisError as e:
            logger.error(f"Redis KEYS error for pattern '{pattern}': {e}")
            return []

class SessionManager:
    """
    Redis-based session management for JWT tokens and user sessions
    """
    
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
        self.default_ttl = 24 * 3600  # 24 hours
    
    def create_session(self, user_id: str, session_data: Dict[str, Any], ttl: int = None) -> str:
        """
        Create new user session
        
        Args:
            user_id: User UUID
            session_data: Session data to store
            ttl: Session TTL in seconds
            
        Returns:
            Session ID
        """
        session_id = self._generate_session_id(user_id)
        session_key = f"{self.session_prefix}{session_id}"
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        
        # Add metadata
        session_data.update({
            'user_id': user_id,
            'session_id': session_id,
            'created_at': datetime.utcnow().isoformat(),
            'last_accessed': datetime.utcnow().isoformat()
        })
        
        # Store session data
        ttl = ttl or self.default_ttl
        self.redis.set(session_key, session_data, ttl)
        
        # Track user sessions
        user_sessions = self.redis.get(user_sessions_key, [])
        if session_id not in user_sessions:
            user_sessions.append(session_id)
            self.redis.set(user_sessions_key, user_sessions, ttl)
        
        logger.info(f"Session created for user {user_id}: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        session_key = f"{self.session_prefix}{session_id}"
        session_data = self.redis.get(session_key)
        
        if session_data:
            # Update last accessed time
            session_data['last_accessed'] = datetime.utcnow().isoformat()
            self.redis.set(session_key, session_data, self.default_ttl)
        
        return session_data
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        session_key = f"{self.session_prefix}{session_id}"
        
        # Get session data to find user_id
        session_data = self.redis.get(session_key)
        if session_data and 'user_id' in session_data:
            user_id = session_data['user_id']
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            
            # Remove from user sessions list
            user_sessions = self.redis.get(user_sessions_key, [])
            if session_id in user_sessions:
                user_sessions.remove(session_id)
                self.redis.set(user_sessions_key, user_sessions)
        
        return self.redis.delete(session_key)
    
    def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user"""
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        user_sessions = self.redis.get(user_sessions_key, [])
        
        deleted_count = 0
        for session_id in user_sessions:
            session_key = f"{self.session_prefix}{session_id}"
            if self.redis.delete(session_key):
                deleted_count += 1
        
        # Clear user sessions list
        self.redis.delete(user_sessions_key)
        
        logger.info(f"Deleted {deleted_count} sessions for user {user_id}")
        return deleted_count
    
    def _generate_session_id(self, user_id: str) -> str:
        """Generate unique session ID"""
        timestamp = datetime.utcnow().isoformat()
        data = f"{user_id}:{timestamp}:{os.urandom(16).hex()}"
        return hashlib.sha256(data.encode()).hexdigest()

class RateLimiter:
    """
    Redis-based rate limiting for API endpoints
    """
    
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager
        self.rate_limit_prefix = "rate_limit:"
    
    def is_allowed(self, identifier: str, limit: int, window: int) -> Dict[str, Any]:
        """
        Check if request is allowed under rate limit
        
        Args:
            identifier: Unique identifier (user_id, IP, etc.)
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            Dict with allowed status and metadata
        """
        key = f"{self.rate_limit_prefix}{identifier}"
        
        try:
            # Get current count
            current_count = self.redis.get(key, 0)
            
            if isinstance(current_count, str):
                current_count = int(current_count)
            
            if current_count >= limit:
                # Rate limit exceeded
                ttl = self.redis.redis_client.ttl(key)
                return {
                    'allowed': False,
                    'current_count': current_count,
                    'limit': limit,
                    'reset_time': ttl,
                    'retry_after': ttl
                }
            
            # Increment counter
            new_count = self.redis.increment(key)
            
            # Set expiration on first request
            if new_count == 1:
                self.redis.expire(key, window)
            
            return {
                'allowed': True,
                'current_count': new_count,
                'limit': limit,
                'remaining': limit - new_count,
                'reset_time': window
            }
            
        except Exception as e:
            logger.error(f"Rate limiting error for {identifier}: {e}")
            # Allow request on error (fail open)
            return {
                'allowed': True,
                'current_count': 0,
                'limit': limit,
                'remaining': limit,
                'error': str(e)
            }

class CacheDecorator:
    """
    Decorator for caching function results
    """
    
    def __init__(self, redis_manager: RedisManager, ttl: int = 3600, prefix: str = "cache:"):
        self.redis = redis_manager
        self.ttl = ttl
        self.prefix = prefix
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = self._generate_cache_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_result = self.redis.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            self.redis.set(cache_key, result, self.ttl)
            logger.debug(f"Cache miss for {cache_key}, result cached")
            
            return result
        
        return wrapper
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function name and arguments"""
        key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{self.prefix}{key_hash}"

# Factory functions
def create_redis_manager() -> RedisManager:
    """Create Redis manager with environment configuration"""
    return RedisManager()

def create_session_manager() -> SessionManager:
    """Create session manager with Redis backend"""
    redis_manager = create_redis_manager()
    return SessionManager(redis_manager)

def create_rate_limiter() -> RateLimiter:
    """Create rate limiter with Redis backend"""
    redis_manager = create_redis_manager()
    return RateLimiter(redis_manager)

def create_cache_decorator(ttl: int = 3600) -> CacheDecorator:
    """Create cache decorator with Redis backend"""
    redis_manager = create_redis_manager()
    return CacheDecorator(redis_manager, ttl)

# Example usage and testing
if __name__ == "__main__":
    try:
        # Test Redis connection
        redis_mgr = create_redis_manager()
        
        # Test basic operations
        redis_mgr.set("test_key", {"message": "Hello Redis!"}, 60)
        result = redis_mgr.get("test_key")
        print(f"✅ Redis basic operations: {result}")
        
        # Test session management
        session_mgr = create_session_manager()
        session_id = session_mgr.create_session("user123", {"role": "admin"})
        session_data = session_mgr.get_session(session_id)
        print(f"✅ Session management: {session_data}")
        
        # Test rate limiting
        rate_limiter = create_rate_limiter()
        result = rate_limiter.is_allowed("user123", 10, 60)
        print(f"✅ Rate limiting: {result}")
        
        # Cleanup
        redis_mgr.delete("test_key")
        session_mgr.delete_session(session_id)
        
        print("✅ Redis configuration successful")
        
    except Exception as e:
        print(f"❌ Redis configuration failed: {e}")
        print("Please check your Redis server and environment variables:")
        print("- REDIS_HOST (default: localhost)")
        print("- REDIS_PORT (default: 6379)")
        print("- REDIS_PASSWORD (optional)")
        print("- REDIS_DB (default: 0)")
