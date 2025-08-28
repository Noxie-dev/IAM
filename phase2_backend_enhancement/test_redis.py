#!/usr/bin/env python3
"""
Test Redis import issue
"""

print("Testing Redis imports...")

try:
    print("1. Testing redis import...")
    import redis
    print("✅ Redis imported successfully")
except Exception as e:
    print(f"❌ Redis import failed: {e}")

try:
    print("2. Testing aioredis import...")
    import aioredis
    print("✅ aioredis imported successfully")
except Exception as e:
    print(f"❌ aioredis import failed: {e}")

try:
    print("3. Testing redis exceptions...")
    from redis.exceptions import RedisError
    print("✅ Redis exceptions imported successfully")
except Exception as e:
    print(f"❌ Redis exceptions import failed: {e}")

print("Redis import tests completed!")
