# IAM SaaS Platform - Intelligent Audio Management

## 🚀 Overview

IAM (Intelligent Audio Management) is a comprehensive SaaS platform that provides AI-powered audio transcription, meeting management, and real-time communication features. The platform includes an advanced inbox system for seamless user communication and collaboration.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│   WebSocket     │◄─────────────┘
                        │   (Real-time)   │
                        └─────────────────┘
                                │
                        ┌─────────────────┐
                        │   Redis Cache   │
                        └─────────────────┘
```

## 🛠️ Technology Stack

### Frontend Stack

#### **Core Framework**
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe JavaScript development
- **React 18** - UI library with hooks and concurrent features

#### **Styling & UI**
- **Tailwind CSS** - Utility-first CSS framework
- **Headless UI** - Unstyled, accessible UI components
- **React Hot Toast** - Toast notifications
- **Lucide React** - Modern icon library

#### **State Management & Data Fetching**
- **React Hooks** - Built-in state management
- **React Context** - Global state management
- **Axios** - HTTP client with interceptors
- **SWR/React Query** - Data fetching and caching

#### **Real-time Communication**
- **WebSocket API** - Real-time bidirectional communication
- **Socket.io Client** - WebSocket abstraction layer

#### **Development Tools**
- **ESLint** - Code linting
- **Prettier** - Code formatting
- **TypeScript** - Static type checking
- **Jest** - Unit testing
- **React Testing Library** - Component testing

### Backend Stack

#### **Core Framework**
- **FastAPI** - Modern Python web framework
- **Python 3.11+** - Programming language
- **Uvicorn** - ASGI server
- **Gunicorn** - WSGI HTTP Server

#### **Database & ORM**
- **PostgreSQL 15** - Primary database
- **SQLAlchemy 2.0** - Modern Python ORM
- **Alembic** - Database migration tool
- **AsyncPG** - Async PostgreSQL driver

#### **Caching & Session Management**
- **Redis 7** - In-memory data store
- **Redis-py** - Python Redis client
- **Session Management** - JWT-based authentication

#### **Authentication & Security**
- **JWT (JSON Web Tokens)** - Stateless authentication
- **bcrypt** - Password hashing
- **PyJWT** - JWT implementation
- **CORS** - Cross-origin resource sharing
- **Rate Limiting** - API request throttling

#### **File Storage**
- **AWS S3** - Cloud object storage
- **boto3** - AWS SDK for Python
- **MinIO** - S3-compatible storage (development)

#### **AI & Machine Learning**
- **OpenAI Whisper** - Speech-to-text transcription
- **FFmpeg** - Audio/video processing
- **NumPy** - Numerical computing
- **Pandas** - Data manipulation

#### **Real-time Communication**
- **WebSocket** - Real-time bidirectional communication
- **FastAPI WebSocket** - WebSocket support
- **Redis Pub/Sub** - Message broadcasting

#### **Monitoring & Logging**
- **Structlog** - Structured logging
- **Sentry** - Error tracking
- **Prometheus** - Metrics collection
- **Grafana** - Monitoring dashboards

### Database Stack

#### **Primary Database**
- **PostgreSQL 15** - Relational database
- **UUID Primary Keys** - Globally unique identifiers
- **JSONB Columns** - Flexible data storage
- **Full-text Search** - PostgreSQL FTS
- **Connection Pooling** - PgBouncer

#### **Caching Layer**
- **Redis 7** - In-memory cache
- **Redis Cluster** - High availability
- **Redis Sentinel** - Failover management

#### **Database Design Patterns**
- **Normalized Schema** - 3NF compliance
- **Indexing Strategy** - Performance optimization
- **Partitioning** - Large table management
- **Backup Strategy** - Point-in-time recovery

### Payment & Billing Stack

#### **Payment Gateway**
- **Stripe** - Primary payment processor
- **Stripe Elements** - Secure payment forms
- **Stripe Webhooks** - Real-time payment events
- **Stripe Connect** - Multi-party payments

#### **Billing System**
- **Stripe Billing** - Subscription management
- **Usage-based Billing** - Pay-per-minute transcription
- **Tiered Pricing** - Multiple subscription levels
- **Invoice Generation** - Automated billing

#### **Alternative Payment Methods**
- **PayPal** - Secondary payment option
- **Apple Pay** - Mobile payments
- **Google Pay** - Digital wallet
- **Bank Transfers** - ACH payments

## 🗄️ Database Schema

### Core Tables

#### **Users Table**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'free',
    subscription_status VARCHAR(50) DEFAULT 'active',
    monthly_transcription_minutes INTEGER DEFAULT 0,
    total_transcription_minutes INTEGER DEFAULT 0,
    remaining_minutes INTEGER DEFAULT 60,
    email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    is_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### **Meetings Table**
```sql
CREATE TABLE meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    meeting_date TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    audio_file_url VARCHAR(500),
    audio_file_size BIGINT,
    file_size_mb DECIMAL(10,2),
    audio_file_format VARCHAR(20),
    original_filename VARCHAR(255),
    transcription_text TEXT,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    processing_error TEXT,
    model_used VARCHAR(100),
    provider_used VARCHAR(100),
    language_detected VARCHAR(10),
    transcription_confidence DECIMAL(5,4),
    transcription_cost DECIMAL(10,4) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### **Messages Table (Inbox Feature)**
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    is_starred BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### **Notifications Table**
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL DEFAULT 'new_message',
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Indexes for Performance
```sql
-- Users indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_subscription_tier ON users(subscription_tier);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Meetings indexes
CREATE INDEX idx_meetings_user_id ON meetings(user_id);
CREATE INDEX idx_meetings_processing_status ON meetings(processing_status);
CREATE INDEX idx_meetings_created_at ON meetings(created_at);
CREATE INDEX idx_meetings_meeting_date ON meetings(meeting_date);

-- Messages indexes
CREATE INDEX idx_messages_recipient_id ON messages(recipient_id);
CREATE INDEX idx_messages_sender_id ON messages(sender_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_is_read ON messages(is_read);
CREATE INDEX idx_messages_is_starred ON messages(is_starred);
CREATE INDEX idx_messages_is_archived ON messages(is_archived);

-- Notifications indexes
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
CREATE INDEX idx_notifications_type ON notifications(type);
```

## 🔐 Authentication & Security

### JWT Authentication Flow
```python
# JWT Token Structure
{
    "sub": "user_id",
    "email": "user@example.com",
    "exp": 1640995200,
    "iat": 1640908800,
    "type": "access"
}

# Authentication Middleware
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Extract JWT token
    # Validate token
    # Add user to request state
    response = await call_next(request)
    return response
```

### Security Features
- **Password Hashing**: bcrypt with salt rounds
- **Rate Limiting**: Redis-based throttling
- **CORS Protection**: Configured origins
- **Input Validation**: Pydantic models
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Input sanitization
- **CSRF Protection**: Token-based validation

## 🤖 AI & Machine Learning Algorithms

### Speech-to-Text Transcription

#### **OpenAI Whisper Integration**
```python
import whisper

class TranscriptionService:
    def __init__(self):
        self.model = whisper.load_model("base")
    
    async def transcribe_audio(self, audio_file_path: str) -> TranscriptionResult:
        # Load audio file
        audio = whisper.load_audio(audio_file_path)
        
        # Transcribe with Whisper
        result = self.model.transcribe(audio)
        
        return TranscriptionResult(
            text=result["text"],
            language=result["language"],
            confidence=result.get("confidence", 0.0),
            segments=result.get("segments", [])
        )
```

#### **Algorithm Features**
- **Language Detection**: Automatic language identification
- **Speaker Diarization**: Multiple speaker identification
- **Noise Reduction**: Audio preprocessing
- **Confidence Scoring**: Transcription accuracy metrics
- **Time Stamping**: Word-level timing information

### Audio Processing Pipeline

#### **FFmpeg Processing**
```python
import ffmpeg

class AudioProcessor:
    def process_audio(self, input_path: str, output_path: str):
        # Convert to WAV format
        # Normalize audio levels
        # Remove silence
        # Optimize for transcription
        
        stream = ffmpeg.input(input_path)
        stream = ffmpeg.output(stream, output_path,
                             acodec='pcm_s16le',
                             ar=16000,
                             ac=1)
        ffmpeg.run(stream)
```

#### **Processing Steps**
1. **Format Conversion**: Convert to WAV format
2. **Sample Rate**: Standardize to 16kHz
3. **Channels**: Convert to mono
4. **Normalization**: Adjust audio levels
5. **Silence Removal**: Remove background noise
6. **Chunking**: Split large files

### Natural Language Processing

#### **Text Analysis**
```python
from transformers import pipeline

class TextAnalyzer:
    def __init__(self):
        self.sentiment_analyzer = pipeline("sentiment-analysis")
        self.summarizer = pipeline("summarization")
    
    def analyze_sentiment(self, text: str) -> SentimentResult:
        result = self.sentiment_analyzer(text)
        return SentimentResult(
            sentiment=result[0]["label"],
            confidence=result[0]["score"]
        )
    
    def generate_summary(self, text: str) -> str:
        summary = self.summarizer(text, max_length=150, min_length=50)
        return summary[0]["summary_text"]
```

## 💳 Payment & Billing System

### Stripe Integration

#### **Subscription Management**
```python
import stripe
from stripe import Subscription, Customer

class BillingService:
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    async def create_subscription(self, user_id: str, price_id: str) -> Subscription:
        # Create or get customer
        customer = await self.get_or_create_customer(user_id)
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": price_id}],
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent']
        )
        
        return subscription
```

#### **Usage-Based Billing**
```python
class UsageBilling:
    def calculate_transcription_cost(self, duration_minutes: float) -> float:
        # Tier-based pricing
        if duration_minutes <= 100:
            rate = 0.10  # $0.10 per minute
        elif duration_minutes <= 500:
            rate = 0.08  # $0.08 per minute
        else:
            rate = 0.06  # $0.06 per minute
        
        return duration_minutes * rate
    
    async def record_usage(self, user_id: str, minutes: float):
        # Record usage in Stripe
        stripe.SubscriptionItem.create_usage_record(
            subscription_item_id,
            quantity=int(minutes * 100),  # Convert to cents
            timestamp=int(time.time())
        )
```

### Pricing Tiers

#### **Free Tier**
- 60 minutes/month transcription
- Basic audio processing
- Email support
- Standard quality

#### **Pro Tier ($29/month)**
- 500 minutes/month transcription
- Advanced audio processing
- Priority support
- High quality transcription
- Export options

#### **Enterprise Tier ($99/month)**
- Unlimited transcription
- Custom audio processing
- Dedicated support
- API access
- Custom integrations

## 🔄 Real-time Communication

### WebSocket Implementation

#### **Connection Management**
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.redis_client = redis.Redis()
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
        # Subscribe to Redis channel
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(f"user:{user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        # Broadcast to all connected users
        for connection in self.active_connections.values():
            await connection.send_json(message)
```

#### **Real-time Features**
- **Live Notifications**: Instant message delivery
- **Typing Indicators**: Real-time typing status
- **Online Status**: User presence tracking
- **Message Sync**: Cross-device synchronization
- **File Sharing**: Real-time file transfer

## 📊 Performance Optimization

### Caching Strategy

#### **Redis Caching Layers**
```python
class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis()
    
    async def cache_user_data(self, user_id: str, data: dict, ttl: int = 3600):
        key = f"user:{user_id}:data"
        await self.redis_client.setex(key, ttl, json.dumps(data))
    
    async def get_cached_user_data(self, user_id: str) -> Optional[dict]:
        key = f"user:{user_id}:data"
        data = await self.redis_client.get(key)
        return json.loads(data) if data else None
```

#### **Cache Levels**
1. **Application Cache**: In-memory caching
2. **Redis Cache**: Distributed caching
3. **CDN Cache**: Static asset caching
4. **Browser Cache**: Client-side caching

### Database Optimization

#### **Query Optimization**
```sql
-- Optimized queries with proper indexing
EXPLAIN ANALYZE 
SELECT m.*, u.email as sender_email 
FROM messages m 
JOIN users u ON m.sender_id = u.id 
WHERE m.recipient_id = $1 
ORDER BY m.created_at DESC 
LIMIT 20;
```

#### **Performance Techniques**
- **Connection Pooling**: PgBouncer configuration
- **Query Optimization**: Index usage analysis
- **Partitioning**: Large table management
- **Read Replicas**: Load distribution

## 🧪 Testing Strategy

### Testing Pyramid

#### **Unit Tests**
```python
import pytest
from unittest.mock import Mock, patch

class TestTranscriptionService:
    @patch('whisper.load_model')
    def test_transcribe_audio(self, mock_whisper):
        # Mock Whisper model
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "Hello world",
            "language": "en",
            "confidence": 0.95
        }
        mock_whisper.return_value = mock_model
        
        service = TranscriptionService()
        result = service.transcribe_audio("test.wav")
        
        assert result.text == "Hello world"
        assert result.language == "en"
```

#### **Integration Tests**
```python
class TestMessageAPI:
    async def test_send_message(self, client, auth_headers):
        message_data = {
            "recipient_id": "user-uuid",
            "subject": "Test",
            "body": "Test message"
        }
        
        response = await client.post(
            "/api/v2/messages/",
            json=message_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        assert response.json()["subject"] == "Test"
```

#### **End-to-End Tests**
```python
class TestInboxFeature:
    async def test_complete_message_flow(self, browser):
        # Login
        await browser.goto("/login")
        await browser.fill("#email", "user@example.com")
        await browser.fill("#password", "password")
        await browser.click("#login-button")
        
        # Send message
        await browser.goto("/inbox")
        await browser.click("#compose-button")
        await browser.fill("#recipient", "recipient@example.com")
        await browser.fill("#subject", "Test Subject")
        await browser.fill("#body", "Test message body")
        await browser.click("#send-button")
        
        # Verify message sent
        await browser.wait_for_selector(".message-sent")
        assert await browser.text_content(".message-sent") == "Message sent successfully"
```

## 🚀 Deployment & DevOps

### Containerization

#### **Docker Configuration**
```dockerfile
# Frontend Dockerfile
FROM node:18-alpine AS frontend
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Backend Dockerfile
FROM python:3.11-slim AS backend
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### **Docker Compose**
```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/iam
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=iam
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
```

### CI/CD Pipeline

#### **GitHub Actions**
```yaml
name: CI/CD Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          # Deployment steps
```

## 📈 Monitoring & Analytics

### Application Monitoring

#### **Sentry Integration**
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0,
    environment="production"
)
```

#### **Performance Metrics**
- **Response Time**: API endpoint performance
- **Error Rate**: Application error tracking
- **User Engagement**: Feature usage analytics
- **System Resources**: CPU, memory, disk usage

### Business Analytics

#### **User Metrics**
- **Monthly Active Users (MAU)**
- **Daily Active Users (DAU)**
- **User Retention Rate**
- **Feature Adoption Rate**

#### **Business Metrics**
- **Monthly Recurring Revenue (MRR)**
- **Customer Acquisition Cost (CAC)**
- **Customer Lifetime Value (CLV)**
- **Churn Rate**

## 🔧 Development Setup

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 15
- Redis 7
- Docker & Docker Compose

### Installation

#### **1. Clone Repository**
```bash
git clone https://github.com/your-org/iam-saas-platform.git
cd iam-saas-platform
```

#### **2. Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload
```

#### **3. Frontend Setup**
```bash
cd frontend
npm install

# Set environment variables
cp .env.example .env.local
# Edit .env.local with your configuration

# Start development server
npm run dev
```

#### **4. Database Setup**
```bash
# Start PostgreSQL and Redis
docker-compose up -d db redis

# Create database
createdb iam_development

# Run migrations
alembic upgrade head
```

### Environment Variables

#### **Backend (.env)**
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/iam_development
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# OpenAI
OPENAI_API_KEY=sk-...

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

#### **Frontend (.env.local)**
```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Stripe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...

# Analytics
NEXT_PUBLIC_GA_TRACKING_ID=G-XXXXXXXXXX
```

## 📚 API Documentation

### REST API Endpoints

#### **Authentication**
```http
POST /api/v1/auth/login
POST /api/v1/auth/register
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
```

#### **Users**
```http
GET /api/v1/users/me
PUT /api/v1/users/me
GET /api/v1/users/{user_id}
```

#### **Meetings**
```http
GET /api/v1/meetings
POST /api/v1/meetings
GET /api/v1/meetings/{meeting_id}
PUT /api/v1/meetings/{meeting_id}
DELETE /api/v1/meetings/{meeting_id}
POST /api/v1/meetings/{meeting_id}/upload
POST /api/v1/meetings/{meeting_id}/transcribe
```

#### **Messages (Inbox)**
```http
GET /api/v2/messages
POST /api/v2/messages
GET /api/v2/messages/{message_id}
PATCH /api/v2/messages/{message_id}
DELETE /api/v2/messages/{message_id}
PUT /api/v2/messages/bulk
GET /api/v2/messages/stats/summary
```

#### **WebSocket Endpoints**
```http
GET /api/v2/messages/ws/{user_id}
```

### WebSocket Events

#### **Client to Server**
```json
{
  "type": "ping",
  "timestamp": 1640995200
}
```

#### **Server to Client**
```json
{
  "type": "new_message",
  "data": {
    "id": "message-uuid",
    "sender": "sender-uuid",
    "subject": "Hello",
    "body": "How are you?",
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Run tests**: `npm test` and `pytest`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Code Standards

- **TypeScript**: Strict mode enabled
- **Python**: PEP 8 compliance
- **Testing**: Minimum 80% coverage
- **Documentation**: Comprehensive docstrings
- **Security**: Regular security audits

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.iam-platform.com](https://docs.iam-platform.com)
- **Issues**: [GitHub Issues](https://github.com/your-org/iam-saas-platform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/iam-saas-platform/discussions)
- **Email**: support@iam-platform.com

## 🙏 Acknowledgments

- **OpenAI** for Whisper speech recognition
- **Stripe** for payment processing
- **FastAPI** for the excellent web framework
- **Next.js** for the React framework
- **PostgreSQL** for the database
- **Redis** for caching and real-time features

---

**Built with ❤️ by the IAM Team**