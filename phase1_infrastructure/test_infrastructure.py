#!/usr/bin/env python3
"""
Infrastructure Test Script
Test PostgreSQL and Redis connections
"""

import psycopg2
import redis
import sys

def test_postgresql():
    """Test PostgreSQL connection"""
    print("🔍 Testing PostgreSQL...")
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            port='5433',
            database='iam_saas',
            user='iam_user',
            password='secure_password_123'
        )
        
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute('SELECT version();')
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL: {version}")
        
        # Test our schema
        cursor.execute('SELECT COUNT(*) FROM users;')
        user_count = cursor.fetchone()[0]
        print(f"✅ Users table: {user_count} users")
        
        cursor.execute('SELECT COUNT(*) FROM meetings;')
        meeting_count = cursor.fetchone()[0]
        print(f"✅ Meetings table: {meeting_count} meetings")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL failed: {e}")
        return False

def test_redis():
    """Test Redis connection"""
    print("\n🔍 Testing Redis...")
    
    try:
        # Test with password
        r = redis.Redis(
            host='localhost',
            port=6379,
            password='redis_password_123',
            db=0,
            decode_responses=True
        )
        
        # Test basic operations
        r.ping()
        print("✅ Redis connection successful")
        
        # Test set/get
        r.set('test_key', 'test_value', ex=60)
        value = r.get('test_key')
        print(f"✅ Redis set/get: {value}")
        
        # Test info
        info = r.info()
        print(f"✅ Redis version: {info['redis_version']}")
        
        # Cleanup
        r.delete('test_key')
        
        return True
        
    except Exception as e:
        print(f"❌ Redis failed: {e}")
        return False

def test_session_management():
    """Test session management functionality"""
    print("\n🔍 Testing Session Management...")
    
    try:
        # Import our Redis manager
        sys.path.append('.')
        from redis_cache_config import create_session_manager
        
        session_mgr = create_session_manager()
        
        # Create a test session
        session_id = session_mgr.create_session('test-user-123', {
            'role': 'admin',
            'permissions': ['read', 'write']
        })
        
        print(f"✅ Session created: {session_id}")
        
        # Retrieve session
        session_data = session_mgr.get_session(session_id)
        print(f"✅ Session retrieved: {session_data['role']}")
        
        # Delete session
        session_mgr.delete_session(session_id)
        print("✅ Session deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ Session management failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 IAM Infrastructure Tests")
    print("=" * 40)
    
    results = []
    
    # Run tests
    results.append(("PostgreSQL", test_postgresql()))
    results.append(("Redis", test_redis()))
    results.append(("Session Management", test_session_management()))
    
    # Summary
    print("\n" + "=" * 40)
    print("TEST RESULTS")
    print("=" * 40)
    
    passed = 0
    for test_name, success in results:
        icon = "✅" if success else "❌"
        print(f"{icon} {test_name}")
        if success:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("\n🎉 All infrastructure tests passed!")
        print("\nInfrastructure is ready for Phase 2!")
        return True
    else:
        print(f"\n⚠️ {len(results) - passed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
