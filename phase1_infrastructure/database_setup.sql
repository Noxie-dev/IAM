-- IAM SaaS Platform - PostgreSQL Database Schema
-- Phase 1: Infrastructure Setup
-- Version: 1.0

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table with enhanced fields for SaaS platform
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(200),
    phone VARCHAR(20),
    
    -- Subscription and billing
    subscription_tier VARCHAR(50) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'basic', 'premium', 'enterprise')),
    subscription_status VARCHAR(50) DEFAULT 'active' CHECK (subscription_status IN ('active', 'cancelled', 'suspended', 'trial')),
    subscription_start_date TIMESTAMP,
    subscription_end_date TIMESTAMP,
    trial_end_date TIMESTAMP,
    
    -- Usage tracking
    monthly_transcription_minutes INTEGER DEFAULT 0,
    total_transcription_minutes INTEGER DEFAULT 0,
    last_login TIMESTAMP,
    
    -- Account management
    email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes for performance
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Meetings/Transcriptions table with enhanced metadata
CREATE TABLE meetings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Basic meeting info
    title VARCHAR(500) NOT NULL,
    description TEXT,
    meeting_date TIMESTAMP,
    duration_seconds INTEGER,
    
    -- File storage
    audio_file_url TEXT,
    audio_file_size BIGINT,
    audio_file_format VARCHAR(10),
    original_filename VARCHAR(255),
    
    -- Transcription data
    transcription_text TEXT,
    transcription_metadata JSONB DEFAULT '{}',
    transcription_confidence DECIMAL(3,2),
    
    -- Processing status
    processing_status VARCHAR(50) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    processing_error TEXT,
    
    -- AI/ML metadata
    model_used VARCHAR(100),
    provider_used VARCHAR(50),
    language_detected VARCHAR(10),
    
    -- Usage and billing
    transcription_cost DECIMAL(10,4) DEFAULT 0.00,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User sessions for JWT token management
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    device_info JSONB DEFAULT '{}',
    ip_address INET,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Subscription plans configuration
CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    tier VARCHAR(50) NOT NULL,
    price_zar DECIMAL(10,2) NOT NULL,
    price_usd DECIMAL(10,2) NOT NULL,
    
    -- Limits
    monthly_minutes INTEGER NOT NULL,
    max_file_size_mb INTEGER NOT NULL,
    max_concurrent_uploads INTEGER DEFAULT 1,
    
    -- Features
    features JSONB DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Payment transactions
CREATE TABLE payment_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Transaction details
    amount_zar DECIMAL(10,2) NOT NULL,
    amount_usd DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'ZAR',
    
    -- Payment provider info
    provider VARCHAR(50) NOT NULL, -- 'stitch', 'paygate', 'stripe'
    provider_transaction_id VARCHAR(255),
    provider_reference VARCHAR(255),
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'refunded')),
    
    -- Metadata
    payment_method VARCHAR(50), -- 'eft', 'card', 'bank_transfer'
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Usage analytics
CREATE TABLE usage_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Event tracking
    event_type VARCHAR(100) NOT NULL, -- 'transcription_started', 'transcription_completed', 'login', etc.
    event_data JSONB DEFAULT '{}',
    
    -- Context
    session_id UUID,
    ip_address INET,
    user_agent TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW()
);

-- System configuration
CREATE TABLE system_config (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance optimization
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_subscription_tier ON users(subscription_tier);
CREATE INDEX idx_users_created_at ON users(created_at);

CREATE INDEX idx_meetings_user_id ON meetings(user_id);
CREATE INDEX idx_meetings_status ON meetings(processing_status);
CREATE INDEX idx_meetings_created_at ON meetings(created_at);
CREATE INDEX idx_meetings_user_created ON meetings(user_id, created_at);

CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_sessions_token_hash ON user_sessions(token_hash);

CREATE INDEX idx_transactions_user_id ON payment_transactions(user_id);
CREATE INDEX idx_transactions_status ON payment_transactions(status);
CREATE INDEX idx_transactions_created_at ON payment_transactions(created_at);

CREATE INDEX idx_analytics_user_id ON usage_analytics(user_id);
CREATE INDEX idx_analytics_event_type ON usage_analytics(event_type);
CREATE INDEX idx_analytics_created_at ON usage_analytics(created_at);

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_meetings_updated_at BEFORE UPDATE ON meetings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscription_plans_updated_at BEFORE UPDATE ON subscription_plans FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_payment_transactions_updated_at BEFORE UPDATE ON payment_transactions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default subscription plans
INSERT INTO subscription_plans (name, tier, price_zar, price_usd, monthly_minutes, max_file_size_mb, features) VALUES
('Free Plan', 'free', 0.00, 0.00, 60, 25, '{"support": "community", "export_formats": ["txt"], "retention_days": 30}'),
('Basic Plan', 'basic', 180.00, 10.00, 300, 50, '{"support": "email", "export_formats": ["txt", "pdf"], "retention_days": 90, "priority_processing": false}'),
('Premium Plan', 'premium', 360.00, 20.00, 1200, 100, '{"support": "priority", "export_formats": ["txt", "pdf", "docx", "srt"], "retention_days": 365, "priority_processing": true, "api_access": true}'),
('Enterprise Plan', 'enterprise', 720.00, 40.00, -1, 250, '{"support": "dedicated", "export_formats": ["txt", "pdf", "docx", "srt"], "retention_days": -1, "priority_processing": true, "api_access": true, "custom_integrations": true}');

-- Insert system configuration
INSERT INTO system_config (key, value, description) VALUES
('transcription_providers', '["openai", "azure", "google"]', 'Available transcription service providers'),
('default_provider', '"openai"', 'Default transcription provider'),
('max_file_size_mb', '250', 'Maximum file size for uploads in MB'),
('supported_formats', '["mp3", "wav", "m4a", "mp4", "mpeg", "mpga", "ogg", "webm", "flac"]', 'Supported audio file formats'),
('rate_limits', '{"free": 100, "basic": 500, "premium": 2000, "enterprise": -1}', 'API rate limits per hour by tier'),
('maintenance_mode', 'false', 'System maintenance mode flag');

-- Create views for common queries
CREATE VIEW user_subscription_details AS
SELECT 
    u.id,
    u.email,
    u.first_name,
    u.last_name,
    u.subscription_tier,
    u.subscription_status,
    sp.monthly_minutes,
    u.monthly_transcription_minutes,
    (sp.monthly_minutes - u.monthly_transcription_minutes) AS remaining_minutes,
    u.subscription_end_date
FROM users u
LEFT JOIN subscription_plans sp ON u.subscription_tier = sp.tier AND sp.is_active = true;

CREATE VIEW meeting_summary AS
SELECT 
    m.id,
    m.user_id,
    u.email,
    m.title,
    m.processing_status,
    m.duration_seconds,
    m.transcription_confidence,
    m.model_used,
    m.created_at,
    m.processing_completed_at
FROM meetings m
JOIN users u ON m.user_id = u.id;

-- ========= INBOX FEATURE TABLES =========

-- Table to store messages between users
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    is_starred BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Table for user notifications, primarily for new messages
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL DEFAULT 'new_message', -- e.g., 'new_message', 'meeting_update'
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for inbox feature performance
CREATE INDEX idx_messages_recipient_id ON messages(recipient_id);
CREATE INDEX idx_messages_sender_id ON messages(sender_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_is_read ON messages(is_read);
CREATE INDEX idx_messages_is_starred ON messages(is_starred);
CREATE INDEX idx_messages_is_archived ON messages(is_archived);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
CREATE INDEX idx_notifications_type ON notifications(type);

-- Trigger for automatic timestamp updates on messages table
CREATE TRIGGER update_messages_updated_at BEFORE UPDATE ON messages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed for your deployment)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO iam_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO iam_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO iam_app_user;
