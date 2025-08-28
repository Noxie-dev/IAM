from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    company_name = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    
    # Subscription and billing
    subscription_tier = db.Column(db.String(50), default='free')
    subscription_status = db.Column(db.String(50), default='active')
    subscription_start_date = db.Column(db.DateTime)
    subscription_end_date = db.Column(db.DateTime)
    trial_end_date = db.Column(db.DateTime)
    
    # Usage tracking
    monthly_transcription_minutes = db.Column(db.Integer, default=0)
    total_transcription_minutes = db.Column(db.Integer, default=0)
    last_login = db.Column(db.DateTime)
    
    # Account management
    email_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'company_name': self.company_name,
            'phone': self.phone,
            'subscription_tier': self.subscription_tier,
            'subscription_status': self.subscription_status,
            'email_verified': self.email_verified,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
