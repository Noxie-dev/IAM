#!/usr/bin/env python3
"""
Test script to debug FastAPI app import issues
"""

print("Testing FastAPI app imports...")

try:
    print("1. Testing FastAPI import...")
    from fastapi import FastAPI
    print("✅ FastAPI imported successfully")
except Exception as e:
    print(f"❌ FastAPI import failed: {e}")

try:
    print("2. Testing config import...")
    from app.core.config import settings
    print("✅ Config imported successfully")
except Exception as e:
    print(f"❌ Config import failed: {e}")

try:
    print("3. Testing database import...")
    from app.core.database import init_db
    print("✅ Database module imported successfully")
except Exception as e:
    print(f"❌ Database import failed: {e}")

try:
    print("4. Testing Redis import...")
    from app.core.redis_client import init_redis
    print("✅ Redis module imported successfully")
except Exception as e:
    print(f"❌ Redis import failed: {e}")

try:
    print("5. Testing middleware imports...")
    from app.middleware.error_handler import ErrorHandlerMiddleware
    print("✅ Middleware imported successfully")
except Exception as e:
    print(f"❌ Middleware import failed: {e}")

try:
    print("6. Testing API router import...")
    from app.api.v2 import api_router
    print("✅ API router imported successfully")
except Exception as e:
    print(f"❌ API router import failed: {e}")

try:
    print("7. Testing main app import...")
    from main import app
    print("✅ Main app imported successfully")
    print(f"App title: {app.title}")
except Exception as e:
    print(f"❌ Main app import failed: {e}")

print("FastAPI app import tests completed!")
