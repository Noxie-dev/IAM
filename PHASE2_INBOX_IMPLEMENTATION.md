# Phase 2: Backend API & Real-time Service Implementation

## Overview

Phase 2 builds upon the database foundation from Phase 1 to create a comprehensive backend API with real-time capabilities for the inbox feature. This implementation uses FastAPI, SQLAlchemy 2.0, and WebSocket support for real-time notifications.

## Architecture Enhancements

### SQLAlchemy 2.0 Models

#### Enhanced Message Model (`app/models/message.py`)

```python
class Message(Base):
    __tablename__ = "messages"
    
    # Primary key with UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Foreign keys with cascade deletion
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Message content with validation
    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Status tracking
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    # Timestamps with automatic updates
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships with optimized loading
    sender: Mapped["User"] = relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="sent_messages",
        lazy="selectin"
    )
    recipient: Mapped["User"] = relationship(
        "User",
        foreign_keys=[recipient_id],
        back_populates="received_messages",
        lazy="selectin"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="message",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Composite indexes for performance
    __table_args__ = (
        Index("ix_messages_recipient_created", "recipient_id", "created_at"),
        Index("ix_messages_sender_created", "sender_id", "created_at"),
        Index("ix_messages_recipient_read", "recipient_id", "is_read"),
        Index("ix_messages_recipient_starred", "recipient_id", "is_starred"),
        Index("ix_messages_recipient_archived", "recipient_id", "is_archived"),
    )
```

**Key Features:**
- **UUID Primary Keys**: Scalable and secure identifier system
- **Cascade Deletion**: Automatic cleanup of related data
- **Optimized Relationships**: Eager loading with `selectin` strategy
- **Composite Indexes**: Performance optimization for common queries
- **Automatic Timestamps**: Server-side timestamp management
- **Helper Methods**: Convenient methods for common operations

#### Enhanced Notification Model (`app/models/notification.py`)

```python
class Notification(Base):
    __tablename__ = "notifications"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Notification content
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="new_message",
        index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Status
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notifications",
        lazy="selectin"
    )
    message: Mapped[Optional["Message"]] = relationship(
        "Message",
        back_populates="notifications",
        lazy="selectin"
    )
    
    # Factory methods for common notification types
    @classmethod
    def create_message_notification(cls, user_id: uuid.UUID, message_id: uuid.UUID, 
                                   sender_name: str, subject: str) -> "Notification":
        return cls(
            user_id=user_id,
            message_id=message_id,
            type="new_message",
            content=f"New message from {sender_name}: {subject}"
        )
    
    @classmethod
    def create_system_notification(cls, user_id: uuid.UUID, content: str, 
                                  notification_type: str = "system_alert") -> "Notification":
        return cls(
            user_id=user_id,
            message_id=None,
            type=notification_type,
            content=content
        )
```

### Pydantic Schemas (`app/schemas/message.py`)

Comprehensive validation and serialization schemas:

#### Message Schemas
- **MessageBase**: Base schema with common fields
- **MessageCreate**: Schema for creating new messages with validation
- **MessageUpdate**: Schema for updating message properties
- **MessageResponse**: Schema for API responses
- **MessageWithUsers**: Schema with user details included

#### Notification Schemas
- **NotificationBase**: Base notification schema
- **NotificationCreate**: Schema for creating notifications
- **NotificationResponse**: Schema for API responses
- **NotificationWithMessage**: Schema with message details

#### Bulk Operation Schemas
- **BulkMessageUpdate**: Schema for bulk message operations
- **BulkNotificationUpdate**: Schema for bulk notification operations

#### Real-time Event Schemas
- **MessageEvent**: Schema for real-time message events
- **NotificationEvent**: Schema for real-time notification events

#### Statistics Schemas
- **MessageStats**: Schema for message statistics
- **NotificationStats**: Schema for notification statistics

## API Endpoints

### Message Endpoints (`app/api/v2/endpoints/messages.py`)

#### Core CRUD Operations

**GET /api/v2/messages/**
```python
async def get_messages(
    folder: str = Query("inbox", description="Message folder"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    unread_only: bool = Query(False, description="Show only unread messages"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get messages for the current user with filtering and pagination
    """
```

**Features:**
- Folder-based filtering (inbox, sent, starred, archived)
- Pagination support
- Unread-only filtering
- Optimized queries with eager loading
- Real-time updates via WebSocket

**GET /api/v2/messages/{message_id}**
```python
async def get_message(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific message by ID with automatic read marking
    """
```

**Features:**
- Automatic read status marking
- Access control validation
- Real-time read status updates
- Cached message retrieval

**POST /api/v2/messages/**
```python
async def create_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new message with automatic notification
    """
```

**Features:**
- Automatic notification creation
- Real-time delivery to recipient
- Redis caching for performance
- Comprehensive logging

**PUT /api/v2/messages/{message_id}**
```python
async def update_message(
    message_id: uuid.UUID,
    message_update: MessageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update message properties (read, starred, archived)
    """
```

**Features:**
- Selective field updates
- Access control validation
- Real-time status updates
- Optimistic locking

**DELETE /api/v2/messages/{message_id}**
```python
async def delete_message(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a message with cascade cleanup
    """
```

**Features:**
- Cascade deletion of related data
- Cache invalidation
- Real-time deletion notifications
- Audit logging

#### Bulk Operations

**PUT /api/v2/messages/bulk**
```python
async def bulk_update_messages(
    bulk_update: BulkMessageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk update messages (mark as read, starred, archived)
    """
```

**Features:**
- Efficient bulk operations
- Access control validation
- Real-time bulk updates
- Performance optimization

#### Statistics

**GET /api/v2/messages/stats/summary**
```python
async def get_message_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get message statistics for the current user
    """
```

**Features:**
- Real-time statistics
- Optimized count queries
- Cached results
- Dashboard integration

### Notification Endpoints (`app/api/v2/endpoints/notifications.py`)

#### Core Operations

**GET /api/v2/notifications/**
```python
async def get_notifications(
    unread_only: bool = Query(False, description="Show only unread notifications"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get notifications for the current user with filtering and pagination
    """
```

**GET /api/v2/notifications/{notification_id}**
```python
async def get_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific notification by ID with automatic read marking
    """
```

**PUT /api/v2/notifications/{notification_id}/read**
```python
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a notification as read
    """
```

**DELETE /api/v2/notifications/{notification_id}**
```python
async def delete_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a notification
    """
```

#### Bulk Operations

**PUT /api/v2/notifications/bulk/read**
```python
async def bulk_mark_notifications_read(
    bulk_update: BulkNotificationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk mark notifications as read
    """
```

#### System Notifications

**POST /api/v2/notifications/system**
```python
async def create_system_notification(
    user_id: uuid.UUID,
    content: str,
    notification_type: str = "system_alert",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a system notification (admin only)
    """
```

#### Statistics

**GET /api/v2/notifications/stats/summary**
```python
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get notification statistics for the current user
    """
```

## Real-time Features

### WebSocket Integration

The implementation includes comprehensive WebSocket support for real-time updates:

#### Message Events
- **new_message**: When a new message is received
- **message_read**: When a message is marked as read
- **message_updated**: When message properties are updated
- **message_deleted**: When a message is deleted
- **messages_bulk_updated**: When bulk operations are performed

#### Notification Events
- **new_notification**: When a new notification is created
- **notification_read**: When a notification is marked as read
- **notification_deleted**: When a notification is deleted
- **notifications_bulk_read**: When bulk read operations are performed

### Redis Caching

Performance optimization through Redis caching:

```python
# Cache message for quick access
await redis_client.setex(
    f"message:{message.id}",
    3600,  # 1 hour
    message.to_dict()
)

# Remove from cache on deletion
await redis_client.delete(f"message:{message_id}")
```

## Performance Optimizations

### Database Optimizations

1. **Composite Indexes**: Optimized for common query patterns
2. **Eager Loading**: `selectin` strategy for relationship loading
3. **Query Optimization**: Efficient filtering and pagination
4. **Connection Pooling**: Optimized database connections

### Caching Strategy

1. **Message Caching**: Frequently accessed messages cached in Redis
2. **Statistics Caching**: Dashboard statistics cached for performance
3. **User Session Caching**: User data cached for quick access

### Real-time Performance

1. **WebSocket Connection Pooling**: Efficient WebSocket management
2. **Event Broadcasting**: Optimized real-time event delivery
3. **Connection State Management**: Proper connection lifecycle management

## Security Features

### Authentication & Authorization

1. **JWT Token Validation**: Secure token-based authentication
2. **Access Control**: User-specific data access validation
3. **Admin Privileges**: Admin-only system notification creation
4. **Input Validation**: Comprehensive Pydantic validation

### Data Protection

1. **SQL Injection Prevention**: Parameterized queries
2. **XSS Protection**: Input sanitization and validation
3. **CSRF Protection**: Token-based CSRF protection
4. **Rate Limiting**: API rate limiting for abuse prevention

## Error Handling

### Comprehensive Error Management

1. **HTTP Status Codes**: Proper HTTP status code usage
2. **Structured Error Responses**: Consistent error response format
3. **Logging**: Comprehensive error logging with context
4. **Graceful Degradation**: Fallback mechanisms for failures

### Validation Errors

```python
class ValidationError(BaseModel):
    """Schema for validation errors"""
    error: str = Field(..., description="Validation error message")
    field: str = Field(..., description="Field that failed validation")
    value: Optional[str] = Field(None, description="Invalid value")
```

## Testing Strategy

### Unit Testing

1. **Model Testing**: Database model validation
2. **Schema Testing**: Pydantic schema validation
3. **API Testing**: Endpoint functionality testing
4. **Integration Testing**: End-to-end workflow testing

### Performance Testing

1. **Load Testing**: High-volume message processing
2. **Concurrency Testing**: Multi-user scenarios
3. **Database Performance**: Query optimization testing
4. **Real-time Testing**: WebSocket performance testing

## Deployment Considerations

### Environment Configuration

1. **Database Configuration**: PostgreSQL connection settings
2. **Redis Configuration**: Caching and session storage
3. **WebSocket Configuration**: Real-time communication settings
4. **Security Configuration**: Authentication and authorization settings

### Monitoring & Observability

1. **Structured Logging**: Comprehensive application logging
2. **Performance Metrics**: API response time monitoring
3. **Error Tracking**: Error rate and pattern monitoring
4. **Real-time Metrics**: WebSocket connection monitoring

## API Documentation

### OpenAPI/Swagger Integration

The FastAPI implementation automatically generates comprehensive API documentation:

- **Interactive API Docs**: Swagger UI integration
- **Request/Response Examples**: Detailed examples for all endpoints
- **Schema Documentation**: Complete Pydantic schema documentation
- **Authentication Documentation**: JWT token usage examples

### API Examples

#### Creating a Message
```bash
curl -X POST "http://localhost:8000/api/v2/messages/" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_id": "550e8400-e29b-41d4-a716-446655440000",
    "subject": "Meeting Follow-up",
    "body": "Hi, I wanted to follow up on our meeting from yesterday..."
  }'
```

#### Getting Messages
```bash
curl -X GET "http://localhost:8000/api/v2/messages/?folder=inbox&page=1&per_page=20" \
  -H "Authorization: Bearer <jwt_token>"
```

#### Marking Messages as Read
```bash
curl -X PUT "http://localhost:8000/api/v2/messages/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"is_read": true}'
```

## Next Steps

Phase 2 provides a solid foundation for the inbox feature. Future enhancements could include:

1. **Advanced Search**: Full-text search capabilities
2. **Message Threading**: Conversation threading support
3. **File Attachments**: File upload and attachment support
4. **Email Integration**: SMTP/IMAP connectivity
5. **Mobile Push Notifications**: Push notification support
6. **Advanced Analytics**: Message analytics and insights
7. **Message Templates**: Predefined message templates
8. **Auto-Reply**: Automated response capabilities

## Conclusion

Phase 2 successfully implements a comprehensive backend API with real-time capabilities for the inbox feature. The implementation provides:

- ✅ **Enhanced SQLAlchemy 2.0 Models**: Modern database models with optimized relationships
- ✅ **Comprehensive Pydantic Schemas**: Robust validation and serialization
- ✅ **Full CRUD API Endpoints**: Complete message and notification management
- ✅ **Real-time WebSocket Support**: Live updates and notifications
- ✅ **Performance Optimizations**: Caching, indexing, and query optimization
- ✅ **Security Features**: Authentication, authorization, and data protection
- ✅ **Error Handling**: Comprehensive error management and logging
- ✅ **API Documentation**: Auto-generated OpenAPI documentation

The implementation follows modern best practices and provides a scalable foundation for future enhancements.
