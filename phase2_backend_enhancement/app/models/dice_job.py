"""
DICE™ Job Model
Phase 2: Backend Enhancement

SQLAlchemy 2.0 model for DICE™ job management and pipeline state tracking
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import String, Text, DateTime, Boolean, Float, Integer, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey

from app.core.database import Base


class DiceJob(Base):
    """
    DICE™ Job model for managing the dual intelligence context engine pipeline
    
    This model tracks the complete state of a DICE job from file upload
    through final minutes generation, including all intermediate results
    and processing metadata.
    """
    __tablename__ = "dice_jobs"
    
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
    
    # Job metadata
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    meeting_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Processing status
    status: Mapped[str] = mapped_column(
        String(50),
        default="queued",
        nullable=False,
        index=True
    )
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    current_step: Mapped[Optional[str]] = mapped_column(String(100))
    
    # File information (JSONB array of FileInfo objects)
    files: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=list,
        nullable=False
    )
    
    # Pipeline stage results (JSONB objects)
    pre_scan_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    draft_transcript: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    validation_report: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    final_minutes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    
    # Processing configuration
    processing_config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False
    )
    
    # Quality and validation metrics
    quality_scores: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False
    )
    
    # Human-in-the-loop data
    hitl_pending: Mapped[bool] = mapped_column(Boolean, default=False)
    hitl_assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    hitl_assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    hitl_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    hitl_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Processing timing and performance
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    total_processing_time: Mapped[Optional[float]] = mapped_column(Float)  # seconds
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Export and output URLs
    export_urls: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False
    )
    
    # South African context specific
    sa_context_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    sa_terms_detected: Mapped[int] = mapped_column(Integer, default=0)
    sa_names_corrected: Mapped[int] = mapped_column(Integer, default=0)
    
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
    
    # Version control for collaborative editing
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    # Add constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'processing_prescan', 'processing_ai_layer_1', 'processing_validation', 'hitl_pending', 'processing_ai_layer_2', 'processing_tts', 'complete', 'failed', 'cancelled')",
            name="valid_status"
        ),
        CheckConstraint(
            "progress_percentage >= 0 AND progress_percentage <= 100",
            name="valid_progress"
        ),
        CheckConstraint(
            "error_count >= 0",
            name="non_negative_error_count"
        ),
        CheckConstraint(
            "retry_count >= 0",
            name="non_negative_retry_count"
        ),
        CheckConstraint(
            "version >= 1",
            name="positive_version"
        ),
    )
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="dice_jobs")
    hitl_reviewer = relationship("User", foreign_keys=[hitl_assigned_to])
    
    def __repr__(self) -> str:
        return f"<DiceJob(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    @property
    def is_complete(self) -> bool:
        """Check if the job has completed successfully"""
        return self.status == "complete"
    
    @property
    def is_failed(self) -> bool:
        """Check if the job has failed"""
        return self.status == "failed"
    
    @property
    def is_processing(self) -> bool:
        """Check if the job is currently being processed"""
        return self.status.startswith("processing_")
    
    @property
    def requires_hitl(self) -> bool:
        """Check if the job requires human-in-the-loop review"""
        return self.status == "hitl_pending" or self.hitl_pending
    
    @property
    def processing_duration(self) -> Optional[float]:
        """Calculate total processing duration in seconds"""
        if self.processing_started_at and self.processing_completed_at:
            return (self.processing_completed_at - self.processing_started_at).total_seconds()
        elif self.processing_started_at:
            return (datetime.utcnow() - self.processing_started_at).total_seconds()
        return None
    
    def update_progress(self, percentage: float, step: Optional[str] = None):
        """Update job progress"""
        self.progress_percentage = max(0, min(100, percentage))
        if step:
            self.current_step = step
        self.updated_at = datetime.utcnow()
    
    def mark_step_complete(self, step: str, result_data: Dict[str, Any]):
        """Mark a pipeline step as complete and store results"""
        if step == "prescan":
            self.pre_scan_result = result_data
            self.status = "processing_ai_layer_1"
            self.progress_percentage = 25.0
        elif step == "ai_layer_1":
            self.draft_transcript = result_data
            self.status = "processing_validation"
            self.progress_percentage = 50.0
        elif step == "validation":
            self.validation_report = result_data
            # Check if HITL is required based on validation scores
            validation_score = result_data.get("scores", {}).get("overall", 0.0)
            auto_threshold = self.processing_config.get("auto_approval_threshold", 0.90)
            
            if validation_score < auto_threshold or self.processing_config.get("require_human_review", False):
                self.status = "hitl_pending"
                self.hitl_pending = True
                self.progress_percentage = 60.0
            else:
                self.status = "processing_ai_layer_2"
                self.progress_percentage = 75.0
        elif step == "ai_layer_2":
            self.final_minutes = result_data
            if self.processing_config.get("generate_tts", True):
                self.status = "processing_tts"
                self.progress_percentage = 90.0
            else:
                self.status = "complete"
                self.progress_percentage = 100.0
                self.processing_completed_at = datetime.utcnow()
        elif step == "tts":
            # Update final_minutes with TTS URLs
            if self.final_minutes:
                self.final_minutes.update(result_data)
            self.status = "complete"
            self.progress_percentage = 100.0
            self.processing_completed_at = datetime.utcnow()
        
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_message: str):
        """Mark job as failed with error details"""
        self.status = "failed"
        self.error_message = error_message
        self.error_count += 1
        self.last_error_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if self.processing_started_at and not self.processing_completed_at:
            self.processing_completed_at = datetime.utcnow()
    
    def assign_hitl_reviewer(self, reviewer_id: uuid.UUID):
        """Assign a human reviewer for HITL process"""
        self.hitl_assigned_to = reviewer_id
        self.hitl_assigned_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def complete_hitl_review(self, reviewer_notes: Optional[str] = None):
        """Mark HITL review as complete"""
        self.hitl_pending = False
        self.hitl_completed_at = datetime.utcnow()
        if reviewer_notes:
            self.hitl_notes = reviewer_notes
        self.status = "processing_ai_layer_2"
        self.progress_percentage = 75.0
        self.updated_at = datetime.utcnow()


class DiceJobLog(Base):
    """
    Detailed logging for DICE™ job processing events
    
    This model provides audit trail and debugging information
    for the DICE processing pipeline.
    """
    __tablename__ = "dice_job_logs"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Foreign key to DICE job
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dice_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Log details
    level: Mapped[str] = mapped_column(String(20), nullable=False)  # INFO, WARNING, ERROR, DEBUG
    step: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Additional context
    context_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False
    )
    
    # Performance metrics
    execution_time: Mapped[Optional[float]] = mapped_column(Float)  # seconds
    memory_usage: Mapped[Optional[float]] = mapped_column(Float)    # MB
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')",
            name="valid_log_level"
        ),
    )
    
    # Relationships
    job = relationship("DiceJob", back_populates="logs")
    
    def __repr__(self) -> str:
        return f"<DiceJobLog(id={self.id}, job_id={self.job_id}, level='{self.level}', step='{self.step}')>"


# Update relationships in related models
# This would be added to the User model in user.py:
# dice_jobs = relationship("DiceJob", foreign_keys="DiceJob.user_id", back_populates="user")

# Add back_populates to DiceJob for logs
DiceJob.logs = relationship("DiceJobLog", back_populates="job", cascade="all, delete-orphan")




