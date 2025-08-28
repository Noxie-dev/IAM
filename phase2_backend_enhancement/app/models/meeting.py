"""
Meeting Model
Phase 2: Backend Enhancement

SQLAlchemy 2.0 Meeting model for transcription records
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal

from sqlalchemy import String, Integer, Text, DateTime, CheckConstraint, DECIMAL, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey

from app.core.database import Base


class Meeting(Base):
    """
    Meeting model for transcription records and metadata
    """
    __tablename__ = "meetings"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Foreign key to user
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Basic meeting information
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    meeting_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    
    # File storage information
    audio_file_url: Mapped[Optional[str]] = mapped_column(Text)
    audio_file_size: Mapped[Optional[int]] = mapped_column(BigInteger)
    audio_file_format: Mapped[Optional[str]] = mapped_column(String(10))
    original_filename: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Transcription data
    transcription_text: Mapped[Optional[str]] = mapped_column(Text)
    transcription_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False
    )
    transcription_confidence: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3, 2))
    
    # Processing status and timing
    processing_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
        index=True
    )
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    processing_error: Mapped[Optional[str]] = mapped_column(Text)
    
    # AI/ML metadata
    model_used: Mapped[Optional[str]] = mapped_column(String(100))
    provider_used: Mapped[Optional[str]] = mapped_column(String(50))
    language_detected: Mapped[Optional[str]] = mapped_column(String(10))
    
    # Usage and billing
    transcription_cost: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 4),
        default=Decimal('0.0000'),
        nullable=False
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships - disabled due to schema mismatch
    # user: Mapped["User"] = relationship(
    #     "User",
    #     back_populates="meetings",
    #     lazy="selectin"
    # )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "processing_status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')",
            name="ck_meetings_processing_status"
        ),
        CheckConstraint(
            "transcription_confidence >= 0.0 AND transcription_confidence <= 1.0",
            name="ck_meetings_confidence_range"
        ),
        CheckConstraint(
            "duration_seconds >= 0",
            name="ck_meetings_positive_duration"
        ),
        CheckConstraint(
            "audio_file_size >= 0",
            name="ck_meetings_positive_file_size"
        ),
    )
    
    def __repr__(self) -> str:
        return f"<Meeting(id={self.id}, title='{self.title}', status='{self.processing_status}')>"
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """Get duration in minutes"""
        if self.duration_seconds is None:
            return None
        return round(self.duration_seconds / 60.0, 2)
    
    @property
    def file_size_mb(self) -> Optional[float]:
        """Get file size in MB"""
        if self.audio_file_size is None:
            return None
        return round(self.audio_file_size / (1024 * 1024), 2)
    
    @property
    def processing_duration(self) -> Optional[float]:
        """Get processing duration in seconds"""
        if not self.processing_started_at or not self.processing_completed_at:
            return None
        
        delta = self.processing_completed_at - self.processing_started_at
        return delta.total_seconds()
    
    @property
    def is_completed(self) -> bool:
        """Check if transcription is completed"""
        return self.processing_status == "completed"
    
    @property
    def is_failed(self) -> bool:
        """Check if transcription failed"""
        return self.processing_status == "failed"
    
    @property
    def is_processing(self) -> bool:
        """Check if transcription is in progress"""
        return self.processing_status == "processing"
    
    @property
    def has_audio_file(self) -> bool:
        """Check if meeting has associated audio file"""
        return bool(self.audio_file_url)
    
    @property
    def has_transcription(self) -> bool:
        """Check if meeting has transcription text"""
        return bool(self.transcription_text and self.transcription_text.strip())
    
    def start_processing(self, provider: str, model: str) -> None:
        """Mark transcription as started"""
        self.processing_status = "processing"
        self.processing_started_at = datetime.utcnow()
        self.provider_used = provider
        self.model_used = model
        self.processing_error = None
    
    def complete_processing(self, 
                          transcription_text: str,
                          confidence: Optional[float] = None,
                          language: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> None:
        """Mark transcription as completed"""
        self.processing_status = "completed"
        self.processing_completed_at = datetime.utcnow()
        self.transcription_text = transcription_text
        
        if confidence is not None:
            self.transcription_confidence = Decimal(str(confidence))
        
        if language:
            self.language_detected = language
        
        if metadata:
            self.transcription_metadata.update(metadata)
    
    def fail_processing(self, error_message: str) -> None:
        """Mark transcription as failed"""
        self.processing_status = "failed"
        self.processing_completed_at = datetime.utcnow()
        self.processing_error = error_message
    
    def cancel_processing(self) -> None:
        """Cancel transcription processing"""
        self.processing_status = "cancelled"
        self.processing_completed_at = datetime.utcnow()
    
    def set_audio_file(self, 
                      file_url: str,
                      file_size: int,
                      file_format: str,
                      original_filename: str) -> None:
        """Set audio file information"""
        self.audio_file_url = file_url
        self.audio_file_size = file_size
        self.audio_file_format = file_format.lower()
        self.original_filename = original_filename
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to transcription"""
        if self.transcription_metadata is None:
            self.transcription_metadata = {}
        self.transcription_metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value"""
        if self.transcription_metadata is None:
            return default
        return self.transcription_metadata.get(key, default)
    
    def to_dict(self, include_transcription: bool = True) -> dict:
        """Convert meeting to dictionary"""
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "description": self.description,
            "meeting_date": self.meeting_date.isoformat() if self.meeting_date else None,
            "duration_seconds": self.duration_seconds,
            "duration_minutes": self.duration_minutes,
            "audio_file_url": self.audio_file_url,
            "audio_file_size": self.audio_file_size,
            "file_size_mb": self.file_size_mb,
            "audio_file_format": self.audio_file_format,
            "original_filename": self.original_filename,
            "processing_status": self.processing_status,
            "processing_started_at": self.processing_started_at.isoformat() if self.processing_started_at else None,
            "processing_completed_at": self.processing_completed_at.isoformat() if self.processing_completed_at else None,
            "processing_duration": self.processing_duration,
            "processing_error": self.processing_error,
            "model_used": self.model_used,
            "provider_used": self.provider_used,
            "language_detected": self.language_detected,
            "transcription_confidence": float(self.transcription_confidence) if self.transcription_confidence else None,
            "transcription_cost": float(self.transcription_cost),
            "transcription_metadata": self.transcription_metadata,
            "has_audio_file": self.has_audio_file,
            "has_transcription": self.has_transcription,
            "is_completed": self.is_completed,
            "is_failed": self.is_failed,
            "is_processing": self.is_processing,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        if include_transcription:
            data["transcription_text"] = self.transcription_text
        
        return data
