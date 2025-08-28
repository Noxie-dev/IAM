from datetime import datetime
import uuid
from src.models.user import db

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    message_id = db.Column(db.String(36), db.ForeignKey('messages.id'), nullable=True)
    type = db.Column(db.String(50), nullable=False, default='new_message')
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    message = db.relationship('Message', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message_id': self.message_id,
            'type': self.type,
            'content': self.content,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user': self.user.to_dict() if self.user else None,
            'message': self.message.to_dict() if self.message else None
        }
