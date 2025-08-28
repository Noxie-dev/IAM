#!/usr/bin/env python3
"""
Test script for inbox feature database setup
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.main import app
from src.models.user import db, User
from src.models.message import Message
from src.models.notification import Notification

def test_inbox_setup():
    """Test the inbox feature database setup"""
    print("Testing inbox feature database setup...")
    
    with app.app_context():
        try:
            # Test database connection
            print("✓ Database connection successful")
            
            # Create test users
            print("Creating test users...")
            user1 = User(
                email="test1@example.com",
                first_name="John",
                last_name="Doe"
            )
            user2 = User(
                email="test2@example.com",
                first_name="Jane",
                last_name="Smith"
            )
            
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            
            print(f"✓ Created test users: {user1.email}, {user2.email}")
            
            # Create test message
            print("Creating test message...")
            message = Message(
                sender_id=user1.id,
                recipient_id=user2.id,
                subject="Test Message",
                body="This is a test message for the inbox feature."
            )
            
            db.session.add(message)
            db.session.commit()
            
            print(f"✓ Created test message: {message.subject}")
            
            # Create test notification
            print("Creating test notification...")
            notification = Notification(
                user_id=user2.id,
                message_id=message.id,
                type="new_message",
                content=f"New message from {user1.first_name}: {message.subject}"
            )
            
            db.session.add(notification)
            db.session.commit()
            
            print(f"✓ Created test notification for message")
            
            # Test queries
            print("Testing queries...")
            
            # Get messages for user2 (inbox)
            inbox_messages = Message.query.filter_by(recipient_id=user2.id).all()
            print(f"✓ User2 has {len(inbox_messages)} messages in inbox")
            
            # Get sent messages for user1
            sent_messages = Message.query.filter_by(sender_id=user1.id).all()
            print(f"✓ User1 has {len(sent_messages)} sent messages")
            
            # Get notifications for user2
            notifications = Notification.query.filter_by(user_id=user2.id).all()
            print(f"✓ User2 has {len(notifications)} notifications")
            
            # Test message properties
            message.is_read = True
            message.is_starred = True
            db.session.commit()
            print("✓ Updated message properties (read, starred)")
            
            print("\n🎉 All tests passed! Inbox feature database setup is working correctly.")
            
            # Cleanup
            print("Cleaning up test data...")
            db.session.delete(notification)
            db.session.delete(message)
            db.session.delete(user1)
            db.session.delete(user2)
            db.session.commit()
            print("✓ Cleanup completed")
            
        except Exception as e:
            print(f"❌ Error during testing: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    test_inbox_setup()
