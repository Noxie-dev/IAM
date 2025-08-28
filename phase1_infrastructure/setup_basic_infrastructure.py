#!/usr/bin/env python3
"""
Basic Infrastructure Setup Script
Phase 1: PostgreSQL and Redis setup only

This script sets up the core infrastructure without S3 dependencies.
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path
import psycopg2
import redis

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(command, check=True):
    """Run shell command with logging"""
    logger.info(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=check, capture_output=True, text=True)
        if result.stdout:
            logger.debug(f"Output: {result.stdout}")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        if e.stderr:
            logger.error(f"Error: {e.stderr}")
        raise

def setup_docker_services():
    """Start PostgreSQL and Redis containers"""
    logger.info("🐳 Starting Docker services...")
    
    try:
        # Start services
        run_command([
            'docker-compose', 
            '-f', 'docker-compose.infrastructure.yml',
            'up', '-d', 'postgres', 'redis'
        ])
        
        # Wait for services to start
        logger.info("⏳ Waiting for services to start...")
        time.sleep(15)
        
        return True
    except Exception as e:
        logger.error(f"Docker setup failed: {e}")
        return False

def test_postgres():
    """Test PostgreSQL connection"""
    logger.info("🔍 Testing PostgreSQL connection...")
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host='localhost',
                port='5433',
                database='iam_saas',
                user='iam_user',
                password='secure_password_123'
            )
            
            cursor = conn.cursor()
            cursor.execute('SELECT version();')
            version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            logger.info(f"✅ PostgreSQL connected: {version}")
            return True
            
        except Exception as e:
            logger.warning(f"PostgreSQL connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                logger.error("❌ PostgreSQL connection failed after all retries")
                return False

def test_redis():
    """Test Redis connection"""
    logger.info("🔍 Testing Redis connection...")
    
    try:
        r = redis.Redis(
            host='localhost',
            port=6379,
            password='redis_password_123',
            db=0
        )
        
        r.ping()
        info = r.info()
        
        logger.info(f"✅ Redis connected: version {info['redis_version']}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False

def setup_database_schema():
    """Set up PostgreSQL database schema"""
    logger.info("📊 Setting up database schema...")
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            port='5433',
            database='iam_saas',
            user='iam_user',
            password='secure_password_123'
        )
        
        # Read schema file
        schema_file = Path('database_setup.sql')
        if not schema_file.exists():
            logger.error("❌ Database schema file not found")
            return False
        
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        cursor = conn.cursor()
        cursor.execute(schema_sql)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        logger.info("✅ Database schema created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database schema setup failed: {e}")
        return False

def migrate_sqlite_data():
    """Migrate data from SQLite if it exists"""
    logger.info("📦 Checking for existing SQLite data...")
    
    sqlite_path = Path('../iam-backend/src/database/app.db')
    
    if not sqlite_path.exists():
        logger.info("ℹ️ No existing SQLite database found, creating default admin user")
        return create_default_admin_user()
    
    try:
        # Import migration script
        sys.path.append('.')
        from migrate_sqlite_to_postgresql import DatabaseMigrator
        
        postgres_config = {
            'host': 'localhost',
            'port': '5433',
            'database': 'iam_saas',
            'user': 'iam_user',
            'password': 'secure_password_123'
        }
        
        migrator = DatabaseMigrator(str(sqlite_path), postgres_config)
        results = migrator.run_migration()
        
        logger.info(f"✅ Data migration completed: {results}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Data migration failed: {e}")
        return False

def create_default_admin_user():
    """Create a default admin user"""
    logger.info("👤 Creating default admin user...")
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            port='5433',
            database='iam_saas',
            user='iam_user',
            password='secure_password_123'
        )
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (
                email, first_name, last_name, subscription_tier,
                is_active, is_admin
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
        """, (
            'admin@iam-app.com',
            'Admin',
            'User',
            'enterprise',
            True,
            True
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Default admin user created")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create admin user: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 IAM SaaS Platform - Basic Infrastructure Setup")
    print("=" * 55)
    
    results = {}
    
    # Setup steps
    steps = [
        ("Docker Services", setup_docker_services),
        ("PostgreSQL Test", test_postgres),
        ("Redis Test", test_redis),
        ("Database Schema", setup_database_schema),
        ("Data Migration", migrate_sqlite_data),
    ]
    
    # Execute steps
    for step_name, step_function in steps:
        logger.info(f"🔄 Executing: {step_name}")
        
        try:
            success = step_function()
            results[step_name] = success
            
            if success:
                logger.info(f"✅ {step_name} completed successfully")
            else:
                logger.warning(f"⚠️ {step_name} completed with issues")
                
        except Exception as e:
            logger.error(f"❌ {step_name} failed: {e}")
            results[step_name] = False
    
    # Summary
    print("\n" + "=" * 55)
    print("SETUP SUMMARY")
    print("=" * 55)
    
    success_count = 0
    for step, success in results.items():
        icon = "✅" if success else "❌"
        print(f"{icon} {step}")
        if success:
            success_count += 1
    
    print(f"\nCompleted: {success_count}/{len(results)} steps")
    
    if success_count == len(results):
        print("\n🎉 Infrastructure setup completed successfully!")
        print("\nAccess Information:")
        print("- PostgreSQL: localhost:5433")
        print("- Redis: localhost:6379")
        print("- pgAdmin: http://localhost:5050 (run with --profile development)")
        print("- Redis Commander: http://localhost:8081 (run with --profile development)")
        print("\nNext Steps:")
        print("1. Configure S3 storage credentials in .env file")
        print("2. Test the application with new infrastructure")
        print("3. Proceed to Phase 2: Backend Enhancement")
        return True
    else:
        print(f"\n⚠️ Setup completed with {len(results) - success_count} issues")
        print("Please review the logs and fix any problems before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
