#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script
Phase 1: Infrastructure - Database Migration

This script migrates data from the current SQLite database to the new PostgreSQL schema.
"""

import sqlite3
import psycopg2
import psycopg2.extras
import uuid
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self, sqlite_path: str, postgres_config: Dict[str, str]):
        self.sqlite_path = sqlite_path
        self.postgres_config = postgres_config
        self.sqlite_conn = None
        self.postgres_conn = None
        
    def connect_databases(self):
        """Connect to both SQLite and PostgreSQL databases"""
        try:
            # Connect to SQLite
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"Connected to SQLite database: {self.sqlite_path}")
            
            # Connect to PostgreSQL
            self.postgres_conn = psycopg2.connect(**self.postgres_config)
            self.postgres_conn.autocommit = False
            logger.info("Connected to PostgreSQL database")
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def close_connections(self):
        """Close database connections"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.postgres_conn:
            self.postgres_conn.close()
        logger.info("Database connections closed")
    
    def get_sqlite_tables(self) -> List[str]:
        """Get list of tables in SQLite database"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found SQLite tables: {tables}")
        return tables
    
    def migrate_users(self):
        """Migrate users from SQLite to PostgreSQL"""
        logger.info("Starting users migration...")
        
        sqlite_cursor = self.sqlite_conn.cursor()
        postgres_cursor = self.postgres_conn.cursor()
        
        try:
            # Check if users table exists in SQLite
            sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
            if not sqlite_cursor.fetchone():
                logger.warning("No users table found in SQLite, creating default admin user")
                self.create_default_admin_user()
                return
            
            # Fetch users from SQLite
            sqlite_cursor.execute("SELECT * FROM users")
            sqlite_users = sqlite_cursor.fetchall()
            
            migrated_count = 0
            user_id_mapping = {}
            
            for user in sqlite_users:
                # Generate new UUID for PostgreSQL
                new_user_id = str(uuid.uuid4())
                user_id_mapping[user['id']] = new_user_id
                
                # Map SQLite user data to PostgreSQL schema
                postgres_cursor.execute("""
                    INSERT INTO users (
                        id, email, first_name, last_name, subscription_tier,
                        is_active, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (email) DO NOTHING
                """, (
                    new_user_id,
                    user.get('email', f'user{user["id"]}@example.com'),
                    user.get('username', 'Unknown'),  # Map username to first_name
                    '',  # No last_name in SQLite
                    'free',  # Default subscription tier
                    True,  # is_active
                    datetime.now(),  # created_at
                    datetime.now()   # updated_at
                ))
                
                migrated_count += 1
            
            self.postgres_conn.commit()
            logger.info(f"Successfully migrated {migrated_count} users")
            return user_id_mapping
            
        except Exception as e:
            self.postgres_conn.rollback()
            logger.error(f"Users migration failed: {e}")
            raise
    
    def migrate_meetings(self, user_id_mapping: Dict[int, str]):
        """Migrate meetings from SQLite to PostgreSQL"""
        logger.info("Starting meetings migration...")
        
        sqlite_cursor = self.sqlite_conn.cursor()
        postgres_cursor = self.postgres_conn.cursor()
        
        try:
            # Check if meetings table exists
            sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meetings';")
            if not sqlite_cursor.fetchone():
                logger.warning("No meetings table found in SQLite")
                return
            
            # Fetch meetings from SQLite
            sqlite_cursor.execute("SELECT * FROM meetings")
            sqlite_meetings = sqlite_cursor.fetchall()
            
            migrated_count = 0
            
            for meeting in sqlite_meetings:
                # Generate new UUID for PostgreSQL
                new_meeting_id = str(uuid.uuid4())
                
                # Map user ID (handle case where user might not exist)
                sqlite_user_id = meeting.get('user_id')
                postgres_user_id = user_id_mapping.get(sqlite_user_id)
                
                if not postgres_user_id:
                    # Create a default user if mapping doesn't exist
                    postgres_user_id = self.get_or_create_default_user()
                
                # Parse date field
                created_at = meeting.get('date')
                if created_at:
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except:
                        created_at = datetime.now()
                else:
                    created_at = datetime.now()
                
                # Map SQLite meeting data to PostgreSQL schema
                postgres_cursor.execute("""
                    INSERT INTO meetings (
                        id, user_id, title, transcription_text, 
                        processing_status, created_at, updated_at,
                        transcription_metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    new_meeting_id,
                    postgres_user_id,
                    meeting.get('title', 'Untitled Meeting'),
                    meeting.get('transcription_text', ''),
                    'completed' if meeting.get('transcription_text') else 'pending',
                    created_at,
                    datetime.now(),
                    json.dumps({
                        'local_audio_id': meeting.get('local_audio_id'),
                        'migrated_from_sqlite': True,
                        'original_id': meeting.get('id')
                    })
                ))
                
                migrated_count += 1
            
            self.postgres_conn.commit()
            logger.info(f"Successfully migrated {migrated_count} meetings")
            
        except Exception as e:
            self.postgres_conn.rollback()
            logger.error(f"Meetings migration failed: {e}")
            raise
    
    def get_or_create_default_user(self) -> str:
        """Get or create a default user for orphaned meetings"""
        postgres_cursor = self.postgres_conn.cursor()
        
        # Check if default user exists
        postgres_cursor.execute("SELECT id FROM users WHERE email = %s", ('default@iam-app.com',))
        result = postgres_cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create default user
        default_user_id = str(uuid.uuid4())
        postgres_cursor.execute("""
            INSERT INTO users (
                id, email, first_name, last_name, subscription_tier,
                is_active, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            default_user_id,
            'default@iam-app.com',
            'Default',
            'User',
            'free',
            True,
            datetime.now(),
            datetime.now()
        ))
        
        logger.info("Created default user for orphaned meetings")
        return default_user_id
    
    def create_default_admin_user(self):
        """Create a default admin user"""
        postgres_cursor = self.postgres_conn.cursor()
        
        admin_user_id = str(uuid.uuid4())
        postgres_cursor.execute("""
            INSERT INTO users (
                id, email, first_name, last_name, subscription_tier,
                is_active, is_admin, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
        """, (
            admin_user_id,
            'admin@iam-app.com',
            'Admin',
            'User',
            'enterprise',
            True,
            True,
            datetime.now(),
            datetime.now()
        ))
        
        self.postgres_conn.commit()
        logger.info("Created default admin user")
    
    def verify_migration(self):
        """Verify the migration was successful"""
        logger.info("Verifying migration...")
        
        postgres_cursor = self.postgres_conn.cursor()
        
        # Count records in PostgreSQL
        postgres_cursor.execute("SELECT COUNT(*) FROM users")
        pg_users_count = postgres_cursor.fetchone()[0]
        
        postgres_cursor.execute("SELECT COUNT(*) FROM meetings")
        pg_meetings_count = postgres_cursor.fetchone()[0]
        
        logger.info(f"PostgreSQL - Users: {pg_users_count}, Meetings: {pg_meetings_count}")
        
        # Verify data integrity
        postgres_cursor.execute("""
            SELECT COUNT(*) FROM meetings m 
            LEFT JOIN users u ON m.user_id = u.id 
            WHERE u.id IS NULL
        """)
        orphaned_meetings = postgres_cursor.fetchone()[0]
        
        if orphaned_meetings > 0:
            logger.warning(f"Found {orphaned_meetings} meetings with invalid user references")
        else:
            logger.info("All meetings have valid user references")
        
        return {
            'users_migrated': pg_users_count,
            'meetings_migrated': pg_meetings_count,
            'orphaned_meetings': orphaned_meetings
        }
    
    def run_migration(self):
        """Run the complete migration process"""
        logger.info("Starting SQLite to PostgreSQL migration...")
        
        try:
            self.connect_databases()
            
            # Get SQLite table info
            sqlite_tables = self.get_sqlite_tables()
            
            # Migrate users first (to get ID mappings)
            user_id_mapping = self.migrate_users()
            
            # Migrate meetings
            self.migrate_meetings(user_id_mapping)
            
            # Verify migration
            results = self.verify_migration()
            
            logger.info("Migration completed successfully!")
            logger.info(f"Migration results: {results}")
            
            return results
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            self.close_connections()

def main():
    """Main migration function"""
    
    # Configuration
    sqlite_path = os.path.join(os.path.dirname(__file__), '../iam-backend/src/database/app.db')
    
    postgres_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'iam_saas'),
        'user': os.getenv('POSTGRES_USER', 'iam_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'your_password')
    }
    
    # Check if SQLite database exists
    if not os.path.exists(sqlite_path):
        logger.warning(f"SQLite database not found at {sqlite_path}")
        logger.info("Creating PostgreSQL schema without migration...")
        
        # Just create the default admin user
        migrator = DatabaseMigrator(sqlite_path, postgres_config)
        try:
            migrator.connect_databases()
            migrator.create_default_admin_user()
            logger.info("PostgreSQL setup completed with default admin user")
        except Exception as e:
            logger.error(f"Setup failed: {e}")
        finally:
            migrator.close_connections()
        return
    
    # Run migration
    migrator = DatabaseMigrator(sqlite_path, postgres_config)
    results = migrator.run_migration()
    
    print("\n" + "="*50)
    print("MIGRATION SUMMARY")
    print("="*50)
    print(f"Users migrated: {results['users_migrated']}")
    print(f"Meetings migrated: {results['meetings_migrated']}")
    print(f"Orphaned meetings: {results['orphaned_meetings']}")
    print("="*50)

if __name__ == "__main__":
    main()
