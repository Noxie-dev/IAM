#!/usr/bin/env python3
"""
Test script to debug import issues
"""

print("Starting import tests...")

try:
    print("1. Testing pydantic...")
    from pydantic import BaseModel
    print("✅ Pydantic imported successfully")
except Exception as e:
    print(f"❌ Pydantic import failed: {e}")

try:
    print("2. Testing pydantic-settings...")
    from pydantic_settings import BaseSettings
    print("✅ Pydantic-settings imported successfully")
except Exception as e:
    print(f"❌ Pydantic-settings import failed: {e}")

try:
    print("3. Testing basic config class...")
    from typing import Optional
    from pydantic import Field
    from pydantic_settings import BaseSettings
    
    class TestSettings(BaseSettings):
        debug: bool = Field(default=True)
        name: str = Field(default="test")
    
    test_settings = TestSettings()
    print(f"✅ Basic config class works: debug={test_settings.debug}")
except Exception as e:
    print(f"❌ Basic config class failed: {e}")

try:
    print("4. Testing app config import...")
    from app.core.config import Settings
    print("✅ App config class imported successfully")
except Exception as e:
    print(f"❌ App config class import failed: {e}")

try:
    print("5. Testing app config instantiation...")
    from app.core.config import settings
    print(f"✅ App config instantiated successfully: debug={settings.DEBUG}")
except Exception as e:
    print(f"❌ App config instantiation failed: {e}")

print("Import tests completed!")
