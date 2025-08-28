# Phase 1: Infrastructure Setup
## IAM SaaS Platform Migration

This directory contains all the infrastructure setup components for migrating the IAM transcription application to a production-ready SaaS platform.

## 📋 Overview

Phase 1 focuses on establishing the foundational infrastructure:
- **PostgreSQL Database**: Scalable relational database replacing SQLite
- **Redis Cache**: Session management, rate limiting, and performance optimization
- **S3 Storage**: Persistent file storage using Wasabi (cost-effective S3-compatible)
- **Monitoring**: Basic monitoring and health checks

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │      Redis      │    │   S3 Storage    │
│   Database      │    │     Cache       │    │   (Wasabi)      │
│                 │    │                 │    │                 │
│ - User data     │    │ - Sessions      │    │ - Audio files   │
│ - Meetings      │    │ - Rate limits   │    │ - Transcripts   │
│ - Subscriptions │    │ - Cache         │    │ - Backups       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Files Structure

```
phase1_infrastructure/
├── README.md                           # This file
├── .env.infrastructure                 # Environment configuration
├── docker-compose.infrastructure.yml   # Docker services
├── database_setup.sql                  # PostgreSQL schema
├── migrate_sqlite_to_postgresql.py     # Data migration script
├── s3_storage_config.py                # S3 storage manager
├── redis_cache_config.py               # Redis cache manager
└── setup_infrastructure.py             # Automated setup script
```

## 🚀 Quick Start

### Prerequisites

1. **Docker & Docker Compose** installed
2. **Python 3.11+** with required packages
3. **S3 Storage Account** (Wasabi recommended)

### Installation

1. **Install Python dependencies:**
```bash
pip install psycopg2-binary redis boto3 python-dotenv
```

2. **Configure environment variables:**
```bash
cp .env.infrastructure .env
# Edit .env with your actual credentials
```

3. **Run automated setup:**
```bash
python setup_infrastructure.py
```

### Manual Setup (Alternative)

1. **Start infrastructure services:**
```bash
docker-compose -f docker-compose.infrastructure.yml up -d postgres redis
```

2. **Set up database schema:**
```bash
python -c "
import psycopg2
conn = psycopg2.connect('postgresql://iam_user:secure_password_123@localhost:5432/iam_saas')
with open('database_setup.sql', 'r') as f:
    conn.cursor().execute(f.read())
conn.commit()
"
```

3. **Migrate existing data:**
```bash
python migrate_sqlite_to_postgresql.py
```

4. **Test S3 storage:**
```bash
python s3_storage_config.py
```

## ⚙️ Configuration

### Database Configuration

```bash
# PostgreSQL settings
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=iam_saas
POSTGRES_USER=iam_user
POSTGRES_PASSWORD=secure_password_123
```

### Redis Configuration

```bash
# Redis settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis_password_123
REDIS_DB=0
```

### S3 Storage Configuration

```bash
# Wasabi S3-compatible storage
S3_ENDPOINT_URL=https://s3.wasabisys.com
S3_ACCESS_KEY=your_wasabi_access_key
S3_SECRET_KEY=your_wasabi_secret_key
S3_BUCKET_NAME=iam-transcription-files
```

## 🔧 Development Tools

### Database Management
- **pgAdmin**: http://localhost:5050
  - Email: admin@iam-app.com
  - Password: admin123

### Redis Management
- **Redis Commander**: http://localhost:8081
  - Username: admin
  - Password: admin123

## 📊 Monitoring

### Health Checks

```bash
# Check PostgreSQL
docker exec iam_postgres pg_isready -U iam_user -d iam_saas

# Check Redis
docker exec iam_redis redis-cli ping

# Check all services
docker-compose -f docker-compose.infrastructure.yml ps
```

### Performance Monitoring

```bash
# PostgreSQL stats
docker exec iam_postgres psql -U iam_user -d iam_saas -c "SELECT * FROM pg_stat_activity;"

# Redis info
docker exec iam_redis redis-cli info
```

## 🔒 Security

### Production Security Checklist

- [ ] Change all default passwords
- [ ] Generate secure JWT secret key
- [ ] Configure proper CORS origins
- [ ] Set up SSL certificates
- [ ] Enable database encryption at rest
- [ ] Configure Redis AUTH
- [ ] Set up VPC/firewall rules
- [ ] Enable audit logging

### Password Security

```bash
# Generate secure passwords
openssl rand -base64 32  # For database passwords
openssl rand -hex 64     # For JWT secret keys
```

## 📈 Performance Optimization

### Database Optimization

```sql
-- Create additional indexes for performance
CREATE INDEX CONCURRENTLY idx_meetings_user_status ON meetings(user_id, processing_status);
CREATE INDEX CONCURRENTLY idx_users_subscription_active ON users(subscription_tier, is_active);

-- Analyze tables for query optimization
ANALYZE users;
ANALYZE meetings;
```

### Redis Optimization

```bash
# Redis memory optimization
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## 🔄 Backup & Recovery

### Database Backup

```bash
# Create backup
docker exec iam_postgres pg_dump -U iam_user iam_saas > backup_$(date +%Y%m%d).sql

# Restore backup
docker exec -i iam_postgres psql -U iam_user iam_saas < backup_20241201.sql
```

### Redis Backup

```bash
# Create Redis snapshot
docker exec iam_redis redis-cli BGSAVE

# Copy snapshot
docker cp iam_redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

## 🐛 Troubleshooting

### Common Issues

1. **PostgreSQL connection refused**
   ```bash
   # Check if container is running
   docker ps | grep postgres
   
   # Check logs
   docker logs iam_postgres
   
   # Restart container
   docker restart iam_postgres
   ```

2. **Redis authentication failed**
   ```bash
   # Check Redis password in environment
   echo $REDIS_PASSWORD
   
   # Test connection
   docker exec iam_redis redis-cli -a $REDIS_PASSWORD ping
   ```

3. **S3 storage access denied**
   ```bash
   # Verify credentials
   python s3_storage_config.py
   
   # Check bucket permissions
   aws s3 ls s3://your-bucket-name --endpoint-url=https://s3.wasabisys.com
   ```

### Log Files

- **Setup logs**: `infrastructure_setup.log`
- **PostgreSQL logs**: `docker logs iam_postgres`
- **Redis logs**: `docker logs iam_redis`

## 📋 Testing

### Infrastructure Tests

```bash
# Test database connection
python -c "
import psycopg2
conn = psycopg2.connect('postgresql://iam_user:secure_password_123@localhost:5432/iam_saas')
print('✅ PostgreSQL connection successful')
"

# Test Redis connection
python -c "
import redis
r = redis.Redis(host='localhost', port=6379, password='redis_password_123')
r.ping()
print('✅ Redis connection successful')
"

# Test S3 storage
python s3_storage_config.py
```

## 🎯 Success Criteria

Phase 1 is complete when:

- [ ] PostgreSQL database is running and accessible
- [ ] Database schema is created with all tables and indexes
- [ ] Existing SQLite data is migrated successfully
- [ ] Redis cache is running and accessible
- [ ] S3 storage is configured and tested
- [ ] All health checks pass
- [ ] Development tools are accessible
- [ ] Backup procedures are tested

## 🔄 Next Steps

After completing Phase 1:

1. **Verify all services** are running correctly
2. **Test data migration** integrity
3. **Configure monitoring** and alerting
4. **Proceed to Phase 2**: Backend Enhancement (FastAPI migration)

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review log files for error details
3. Verify environment configuration
4. Test individual components separately

---

**Phase 1 Status**: ✅ Ready for deployment
**Next Phase**: Phase 2 - Backend Enhancement
