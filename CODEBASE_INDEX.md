# IAM Application - Codebase Index

## 📋 Overview

The IAM (In A Meeting) application is a comprehensive meeting transcription SaaS platform with a multi-phase development approach. The codebase is organized into distinct phases representing the evolution from a proof-of-concept to a production-ready SaaS platform.

## 🏗️ Architecture Overview

```
IAM Application
├── Phase 1: Infrastructure Foundation
├── Phase 2: Backend Enhancement  
├── Phase 3: Frontend Enhancement
└── Production Ready Components
```

## 📁 Directory Structure

### Root Level
```
iam-app/
├── README.md                           # Main project documentation
├── PRD_IAM_SAAS_MIGRATION.md          # Product Requirements Document
├── PRODUCTION_MIGRATION_PLAN.md        # Migration strategy
├── ARCHITECTURE_COMPARISON.md          # Architecture analysis
├── AUDIO_ENHANCEMENT_INTEGRATION.md    # Audio processing features
├── TRANSCRIPTION_IMPROVEMENTS.md       # Transcription enhancements
├── TEST_RESULTS_SUMMARY.md             # Testing documentation
├── WORKSPACE_SETUP.md                  # Development setup guide
├── start-backend.sh                    # Backend startup script
├── start-frontend.sh                   # Frontend startup script
├── start-dev.sh                        # Development startup script
└── test_transcription.py               # Transcription testing script
```

### Core Application Components

#### 1. Original Application (`iam-backend/` & `iam-frontend/`)
```
iam-backend/
├── requirements.txt                    # Python dependencies
├── src/
│   ├── main.py                        # Flask application entry point
│   ├── models/
│   │   ├── user.py                    # User database model
│   │   └── meeting.py                 # Meeting database model
│   ├── routes/
│   │   ├── user.py                    # User authentication routes
│   │   ├── meeting.py                 # Meeting management routes
│   │   └── payment.py                 # Stripe payment integration
│   ├── database/
│   │   └── app.db                     # SQLite database
│   └── static/                        # Built frontend files
└── venv/                              # Python virtual environment

iam-frontend/
├── package.json                       # Node.js dependencies
├── vite.config.js                     # Vite build configuration
├── src/
│   ├── App.jsx                        # Main React application
│   ├── main.jsx                       # Application entry point
│   ├── components/
│   │   ├── AudioRecorder.jsx          # Audio recording component
│   │   ├── MeetingsList.jsx           # Meeting management UI
│   │   ├── PaymentModal.jsx           # Payment processing modal
│   │   ├── AuthModal.jsx              # Authentication modal
│   │   ├── LandingPage.jsx            # Marketing landing page
│   │   ├── MainApp.jsx                # Main application interface
│   │   ├── Toast.jsx                  # Notification system
│   │   └── ui/                        # shadcn/ui components
│   ├── hooks/
│   │   └── useToast.js                # Toast notification hook
│   └── lib/
│       └── utils.js                   # Utility functions
├── public/                            # Static assets
└── dist/                              # Built application
```

## 🔧 Phase 1: Infrastructure Foundation

### Purpose
Establish production-ready infrastructure with PostgreSQL, Redis, and S3 storage.

### Key Components
```
phase1_infrastructure/
├── README.md                          # Infrastructure documentation
├── docker-compose.infrastructure.yml  # Docker services configuration
├── database_setup.sql                 # PostgreSQL schema
├── migrate_sqlite_to_postgresql.py    # Data migration script
├── s3_storage_config.py               # S3 storage manager
├── redis_cache_config.py              # Redis cache manager
├── setup_infrastructure.py            # Automated setup script
├── test_infrastructure.py             # Infrastructure testing
└── postgres_init.sql/                 # PostgreSQL initialization
```

### Infrastructure Services
- **PostgreSQL 15**: Primary database with async support
- **Redis 7**: Caching, sessions, and rate limiting
- **Wasabi S3**: Cost-effective file storage
- **pgAdmin**: Database management interface
- **Redis Commander**: Redis management interface

## 🚀 Phase 2: Backend Enhancement

### Purpose
Migrate from Flask to FastAPI with enhanced features, authentication, and scalability.

### Key Components
```
phase2_backend_enhancement/
├── main.py                            # FastAPI application entry point
├── requirements.txt                   # Enhanced Python dependencies
├── alembic/                           # Database migration management
├── app/
│   ├── __init__.py
│   ├── api/
│   │   └── v2/                        # API version 2 endpoints
│   ├── core/
│   │   ├── config.py                  # Application configuration
│   │   ├── database.py                # Database connection management
│   │   └── redis_client.py            # Redis client configuration
│   ├── middleware/
│   │   ├── error_handler.py           # Global error handling
│   │   ├── rate_limiter.py            # Rate limiting middleware
│   │   └── request_logger.py          # Request logging
│   ├── models/                        # SQLAlchemy models
│   ├── schemas/                       # Pydantic schemas
│   ├── services/                      # Business logic services
│   └── utils/                         # Utility functions
├── tests/                             # Comprehensive test suite
└── requirements-audio.txt             # Audio processing dependencies
```

### Enhanced Features
- **FastAPI**: Modern async web framework
- **JWT Authentication**: Secure token-based auth
- **Background Tasks**: Celery integration for async processing
- **Rate Limiting**: Subscription-based rate limiting
- **Structured Logging**: Comprehensive logging with structlog
- **Error Tracking**: Sentry integration
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Health Checks**: Monitoring endpoints

## 🎨 Phase 3: Frontend Enhancement

### Purpose
Upgrade to Next.js 14 with TypeScript, real-time features, and enhanced UX.

### Key Components
```
phase3_frontend_enhancement/
└── iam-frontend/
    ├── package.json                   # Next.js dependencies
    ├── next.config.ts                 # Next.js configuration
    ├── tsconfig.json                  # TypeScript configuration
    ├── src/
    │   ├── app/                       # Next.js App Router
    │   ├── components/
    │   │   ├── upload/
    │   │   │   └── FileUpload.tsx     # Advanced file upload component
    │   │   └── ui/                    # Enhanced UI components
    │   ├── contexts/
    │   │   └── AuthContext.tsx        # Authentication context
    │   ├── lib/
    │   │   └── api.ts                 # API client
    │   └── types/                     # TypeScript type definitions
    └── public/                        # Static assets
```

### Enhanced Features
- **Next.js 14**: React framework with SSR/SSG
- **TypeScript**: Type-safe development
- **Real-time Updates**: WebSocket integration
- **Chunked Uploads**: Large file upload support
- **Advanced UI**: Enhanced components and animations
- **Mobile Responsive**: Optimized for all devices

## 🔑 Key Features by Component

### Authentication System
- **JWT Tokens**: Secure authentication with refresh tokens
- **Role-based Access**: User permissions and subscription tiers
- **Session Management**: Redis-backed session storage
- **OAuth Integration**: Social login support (planned)

### Audio Processing
- **Web Audio API**: Browser-based audio recording
- **IndexedDB Storage**: Local audio file storage
- **Chunked Uploads**: Large file upload support
- **Audio Enhancement**: Noise reduction and quality improvement
- **Multi-format Support**: MP3, WAV, M4A, FLAC, etc.

### Transcription Engine
- **OpenAI Whisper**: Primary transcription provider
- **Multi-provider Support**: Azure, Google fallbacks
- **Retry Logic**: Robust error handling and retries
- **Real-time Progress**: Live transcription updates
- **Speaker Detection**: Multi-speaker identification (planned)

### Payment Integration
- **Stripe**: International payment processing
- **South African Gateways**: Stitch, PayGate integration
- **Subscription Management**: Tiered pricing plans
- **Usage Tracking**: Transcription minute tracking
- **Billing Automation**: Automated invoicing

### Database Models

#### User Model
```python
class User:
    id: UUID
    email: str
    password_hash: str
    subscription_tier: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

#### Meeting Model
```python
class Meeting:
    id: UUID
    user_id: UUID
    title: str
    audio_file_url: str
    transcription_text: str
    transcription_metadata: JSON
    processing_status: str
    created_at: datetime
    updated_at: datetime
```

## 🔧 Development Tools & Scripts

### Startup Scripts
- `start-backend.sh`: Start Flask backend server
- `start-frontend.sh`: Start React development server
- `start-dev.sh`: Start both frontend and backend

### Testing
- `test_transcription.py`: Test transcription functionality
- `test_your_code.py`: General code testing
- `create_test_audio.py`: Generate test audio files

### Infrastructure
- `setup_infrastructure.py`: Automated infrastructure setup
- `test_infrastructure.py`: Infrastructure health checks
- `migrate_sqlite_to_postgresql.py`: Database migration

## 📊 Technology Stack Summary

### Frontend Technologies
- **React 19**: UI framework
- **Next.js 14**: Full-stack React framework (Phase 3)
- **TypeScript**: Type-safe JavaScript (Phase 3)
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: High-quality UI components
- **Vite**: Build tool and dev server
- **React Router**: Client-side routing
- **IndexedDB**: Local storage for audio files

### Backend Technologies
- **Flask**: Python web framework (Original)
- **FastAPI**: Modern async Python framework (Phase 2)
- **SQLAlchemy**: Database ORM
- **Alembic**: Database migrations
- **Celery**: Background task processing
- **Redis**: Caching and session storage
- **PostgreSQL**: Primary database (Phase 1+)
- **SQLite**: Development database (Original)

### Infrastructure & Services
- **Docker**: Containerization
- **PostgreSQL**: Production database
- **Redis**: Caching and sessions
- **Wasabi S3**: File storage
- **OpenAI API**: Transcription service
- **Stripe**: Payment processing
- **Sentry**: Error tracking
- **Prometheus**: Metrics collection

### Development Tools
- **ESLint**: JavaScript linting
- **Prettier**: Code formatting
- **Pytest**: Python testing
- **Alembic**: Database migrations
- **pgAdmin**: Database management
- **Redis Commander**: Redis management

## 🚀 Deployment & Environment

### Development Environment
- **Local Development**: Docker Compose for services
- **Hot Reloading**: Vite for frontend, uvicorn for backend
- **Database**: PostgreSQL with pgAdmin
- **Caching**: Redis with Redis Commander

### Production Environment
- **Platform**: Railway/DigitalOcean App Platform
- **Database**: Managed PostgreSQL
- **Storage**: Wasabi S3-compatible storage
- **CDN**: Cloudflare for static assets
- **Monitoring**: Sentry for error tracking

## 📈 Performance & Scalability

### Current Performance
- **Response Time**: <2s for API calls
- **File Upload**: Up to 250MB audio files
- **Concurrent Users**: 100+ supported
- **Transcription Accuracy**: 95%+ with Whisper

### Scalability Features
- **Async Processing**: Background task queues
- **Caching**: Redis for session and data caching
- **CDN**: Static asset delivery
- **Auto-scaling**: Platform-based scaling
- **Database Optimization**: Connection pooling and indexing

## 🔒 Security Features

### Authentication & Authorization
- **JWT Tokens**: Secure token-based authentication
- **Password Hashing**: bcrypt with configurable rounds
- **Rate Limiting**: Subscription-based rate limits
- **CORS**: Configured cross-origin resource sharing
- **Input Validation**: Pydantic schema validation

### Data Protection
- **Encryption**: TLS 1.3 for data in transit
- **Secure Storage**: S3 with encryption at rest
- **POPIA Compliance**: South African data protection
- **Audit Logging**: Comprehensive access logs
- **Session Security**: Secure session management

## 📋 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh
- `POST /api/auth/logout` - User logout

### Transcription
- `POST /api/transcribe` - Upload and transcribe audio
- `GET /api/meetings` - List user meetings
- `GET /api/meetings/{id}` - Get specific meeting
- `DELETE /api/meetings/{id}` - Delete meeting

### Payments
- `POST /api/create-payment-intent` - Create payment intent
- `POST /api/confirm-payment` - Confirm payment
- `GET /api/subscription-plans` - Get available plans

## 🎯 Future Roadmap

### Planned Features
- **Real-time Transcription**: Live transcription during recording
- **Speaker Diarization**: Multi-speaker identification
- **Meeting Summaries**: AI-generated summaries
- **Team Collaboration**: Shared workspaces
- **API Access**: Public API for integrations
- **Mobile Apps**: Native iOS and Android applications

### Technical Improvements
- **WebSocket Integration**: Real-time features
- **Progressive Web App**: Offline functionality
- **Advanced Analytics**: Usage insights and reporting
- **Multi-language Support**: Internationalization
- **Advanced Search**: Full-text search with filters

## 📞 Support & Documentation

### Documentation Files
- `README.md`: Main project documentation
- `PRD_IAM_SAAS_MIGRATION.md`: Product requirements
- `DEVELOPMENT.md`: Development guidelines
- `TESTING.md`: Testing procedures
- `ARCHITECTURE_COMPARISON.md`: Architecture analysis

### Support Resources
- **API Documentation**: Auto-generated Swagger docs
- **Error Tracking**: Sentry for production issues
- **Health Checks**: Monitoring endpoints
- **Logs**: Structured logging for debugging

---

**Last Updated**: December 2024  
**Version**: 2.0.0  
**Status**: Production Ready with Continuous Enhancement
