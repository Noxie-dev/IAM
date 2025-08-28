from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.message import Message
from src.models.notification import Notification
from datetime import datetime
import uuid

message_bp = Blueprint('message', __name__)

@message_bp.route('/messages', methods=['GET'])
def get_messages():
    """Get messages for the current user (inbox)"""
    try:
        # Get query parameters
        user_id = request.args.get('user_id')
        folder = request.args.get('folder', 'inbox')  # inbox, sent, starred, archived
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Build query based on folder
        if folder == 'inbox':
            query = Message.query.filter_by(recipient_id=user_id, is_archived=False)
        elif folder == 'sent':
            query = Message.query.filter_by(sender_id=user_id, is_archived=False)
        elif folder == 'starred':
            query = Message.query.filter(
                ((Message.recipient_id == user_id) | (Message.sender_id == user_id)) &
                (Message.is_starred == True) &
                (Message.is_archived == False)
            )
        elif folder == 'archived':
            query = Message.query.filter(
                ((Message.recipient_id == user_id) | (Message.sender_id == user_id)) &
                (Message.is_archived == True)
            )
        else:
            return jsonify({'error': 'Invalid folder parameter'}), 400
        
        # Order by created_at descending
        query = query.order_by(Message.created_at.desc())
        
        # Pagination
        messages = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'messages': [msg.to_dict() for msg in messages.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': messages.total,
                'pages': messages.pages,
                'has_next': messages.has_next,
                'has_prev': messages.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@message_bp.route('/messages/<message_id>', methods=['GET'])
def get_message(message_id):
    """Get a specific message by ID"""
    try:
        message = Message.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Mark as read if recipient is viewing
        user_id = request.args.get('user_id')
        if user_id and message.recipient_id == user_id and not message.is_read:
            message.is_read = True
            db.session.commit()
        
        return jsonify(message.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@message_bp.route('/messages', methods=['POST'])
def create_message():
    """Create a new message"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['sender_id', 'recipient_id', 'subject', 'body']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create new message
        message = Message(
            sender_id=data['sender_id'],
            recipient_id=data['recipient_id'],
            subject=data['subject'],
            body=data['body']
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Create notification for recipient
        notification = Notification(
            user_id=data['recipient_id'],
            message_id=message.id,
            type='new_message',
            content=f'New message from {message.sender.first_name or message.sender.email}: {message.subject}'
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify(message.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@message_bp.route('/messages/<message_id>', methods=['PUT'])
def update_message(message_id):
    """Update message properties (read, starred, archived)"""
    try:
        message = Message.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'is_read' in data:
            message.is_read = data['is_read']
        if 'is_starred' in data:
            message.is_starred = data['is_starred']
        if 'is_archived' in data:
            message.is_archived = data['is_archived']
        
        db.session.commit()
        
        return jsonify(message.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@message_bp.route('/messages/<message_id>', methods=['DELETE'])
def delete_message(message_id):
    """Delete a message"""
    try:
        message = Message.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        db.session.delete(message)
        db.session.commit()
        
        return jsonify({'message': 'Message deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@message_bp.route('/messages/bulk', methods=['PUT'])
def bulk_update_messages():
    """Bulk update messages (mark as read, starred, archived)"""
    try:
        data = request.get_json()
        
        if 'message_ids' not in data or 'updates' not in data:
            return jsonify({'error': 'message_ids and updates are required'}), 400
        
        message_ids = data['message_ids']
        updates = data['updates']
        
        # Validate updates
        allowed_updates = ['is_read', 'is_starred', 'is_archived']
        for key in updates:
            if key not in allowed_updates:
                return jsonify({'error': f'Invalid update field: {key}'}), 400
        
        # Update messages
        messages = Message.query.filter(Message.id.in_(message_ids)).all()
        for message in messages:
            for key, value in updates.items():
                setattr(message, key, value)
        
        db.session.commit()
        
        return jsonify({'message': f'Updated {len(messages)} messages'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@message_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """Get notifications for a user"""
    try:
        user_id = request.args.get('user_id')
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        query = Notification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        query = query.order_by(Notification.created_at.desc())
        
        notifications = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'notifications': [notif.to_dict() for notif in notifications.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': notifications.total,
                'pages': notifications.pages,
                'has_next': notifications.has_next,
                'has_prev': notifications.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@message_bp.route('/notifications/<notification_id>', methods=['PUT'])
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.query.get(notification_id)
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify(notification.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@message_bp.route('/notifications/bulk', methods=['PUT'])
def bulk_mark_notifications_read():
    """Bulk mark notifications as read"""
    try:
        data = request.get_json()
        
        if 'notification_ids' not in data:
            return jsonify({'error': 'notification_ids is required'}), 400
        
        notification_ids = data['notification_ids']
        
        notifications = Notification.query.filter(Notification.id.in_(notification_ids)).all()
        for notification in notifications:
            notification.is_read = True
        
        db.session.commit()
        
        return jsonify({'message': f'Marked {len(notifications)} notifications as read'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
