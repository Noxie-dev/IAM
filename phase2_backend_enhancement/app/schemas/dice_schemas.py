"""
DICE™ - Dual Intelligence Context Engine
Data Schemas and Contracts

Pydantic models for DICE™ pipeline data validation and serialization
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any, Union
import uuid
from datetime import datetime
from decimal import Decimal

class FileInfo(BaseModel):
    """Information about uploaded files for processing"""
    file_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    s3_uri: str
    mime_type: str
    original_filename: str
    file_size: int
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)

class PreScanBlock(BaseModel):
    """OCR/Document scanning block result"""
    type: Literal["text", "table", "handwriting", "image"]
    bbox: List[float] = Field(description="Bounding box coordinates [x1, y1, x2, y2]")
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    page_number: Optional[int] = None

class PreScanAudioSegment(BaseModel):
    """Audio segment from diarization"""
    start_time: float = Field(ge=0.0)
    end_time: float = Field(ge=0.0)
    speaker_hint: Optional[str] = None  # e.g., "Speaker_1", "Speaker_2"
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)

class PreScanJSON(BaseModel):
    """Complete pre-scan results from Algorithm 1: Extractor"""
    ocr_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    diarization_confidence: Optional[float] = Field(ge=0.0, le=1.0, default=None)
    entities_detected: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Detected entities: {'names': [], 'organizations': [], 'locations': []}"
    )
    
    # Document-specific data
    pages: Optional[List[PreScanBlock]] = Field(default=None)
    total_pages: Optional[int] = None
    
    # Audio-specific data
    audio_segments: Optional[List[PreScanAudioSegment]] = Field(default=None)
    total_duration: Optional[float] = None
    
    # Processing metadata
    processing_time: float = Field(default=0.0)
    algorithm_version: str = Field(default="1.0.0")

class TranscriptSegment(BaseModel):
    """Individual transcript segment with speaker and timing"""
    segment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    speaker: str
    start_time: float = Field(ge=0.0)
    end_time: float = Field(ge=0.0)
    text: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    
    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)

class DraftTranscriptJSON(BaseModel):
    """Draft transcript from AI Layer 1"""
    language: str = Field(default="en")
    segments: List[TranscriptSegment]
    summary: Optional[str] = None
    action_items: List[str] = Field(default_factory=list)
    key_topics: List[str] = Field(default_factory=list)
    
    # Model metadata
    model_used: str = Field(default="gpt-4o")
    ai_provider: str = Field(default="openai")
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    
    # Processing metadata
    processing_time: float = Field(default=0.0)
    token_usage: Optional[Dict[str, int]] = None
    
    @property
    def total_duration(self) -> float:
        if not self.segments:
            return 0.0
        return max(segment.end_time for segment in self.segments)
    
    @property
    def word_count(self) -> int:
        return sum(len(segment.text.split()) for segment in self.segments)

class ValidationIssue(BaseModel):
    """Individual validation issue found by Algorithm 2"""
    issue_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: Literal["grammar", "name_spell", "coherence", "term_suggestion", "context_error"]
    severity: Literal["low", "medium", "high", "critical"]
    segment_id: str = Field(description="References TranscriptSegment.segment_id")
    segment_index: int = Field(ge=0)
    
    # Issue details
    original_text: str
    suggested_text: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    
    # Context
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    notes: Optional[str] = None
    
    # South African specific
    sa_context_applied: bool = Field(default=False)
    sa_term_match: Optional[str] = None

class ValidationReportJSON(BaseModel):
    """Complete validation report from Algorithm 2: Validator"""
    issues: List[ValidationIssue] = Field(default_factory=list)
    
    # Quality scores
    scores: Dict[str, float] = Field(
        default_factory=lambda: {
            "grammar": 0.0,
            "sa_names": 0.0,
            "coherence": 0.0,
            "overall": 0.0
        }
    )
    
    # Statistics
    total_segments_analyzed: int = Field(default=0)
    total_words_analyzed: int = Field(default=0)
    issues_by_severity: Dict[str, int] = Field(
        default_factory=lambda: {"low": 0, "medium": 0, "high": 0, "critical": 0}
    )
    
    # Processing metadata
    processing_time: float = Field(default=0.0)
    algorithm_version: str = Field(default="1.0.0")
    sa_dictionary_version: str = Field(default="1.0.0")
    
    # Recommendations
    requires_human_review: bool = Field(default=False)
    auto_approval_eligible: bool = Field(default=False)

class FinalActionItem(BaseModel):
    """Structured action item from meeting minutes"""
    item_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner: str
    item: str
    due_date: Optional[str] = None
    priority: Literal["low", "medium", "high"] = Field(default="medium")
    status: Literal["pending", "in_progress", "completed"] = Field(default="pending")
    category: Optional[str] = None

class FinalDecision(BaseModel):
    """Structured decision from meeting minutes"""
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision: str
    rationale: Optional[str] = None
    stakeholders: List[str] = Field(default_factory=list)
    implementation_date: Optional[str] = None

class FinalMinutes(BaseModel):
    """Final meeting minutes from AI Layer 2: Refine"""
    # Meeting metadata
    title: str
    meeting_date: datetime
    participants: List[str] = Field(default_factory=list)
    meeting_type: Optional[str] = None
    location: Optional[str] = None
    
    # Content
    executive_summary: str
    key_topics_discussed: List[str] = Field(default_factory=list)
    decisions: List[FinalDecision] = Field(default_factory=list)
    action_items: List[FinalActionItem] = Field(default_factory=list)
    
    # Full transcript (corrected and refined)
    full_transcript: List[TranscriptSegment]
    
    # Audio outputs
    tts_audio_url: Optional[str] = None
    tts_summary_url: Optional[str] = None
    
    # Version control
    version: int = Field(default=1)
    hitl_approved_by: Optional[uuid.UUID] = None
    hitl_approved_at: Optional[datetime] = None
    hitl_notes: Optional[str] = None
    
    # Processing metadata
    ai_model_used: str = Field(default="gpt-4o")
    processing_time: float = Field(default=0.0)
    quality_score: float = Field(ge=0.0, le=1.0, default=0.0)
    
    # Export formats
    export_formats: List[str] = Field(
        default_factory=lambda: ["pdf", "docx", "txt", "json"]
    )

class DiceJobStatus(BaseModel):
    """Job status with detailed progress information"""
    status: Literal[
        "queued", "processing_prescan", "processing_ai_layer_1", 
        "processing_validation", "hitl_pending", "processing_ai_layer_2", 
        "processing_tts", "complete", "failed", "cancelled"
    ]
    progress_percentage: float = Field(ge=0.0, le=100.0, default=0.0)
    current_step: Optional[str] = None
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Step-specific progress
    steps_completed: List[str] = Field(default_factory=list)
    steps_remaining: List[str] = Field(default_factory=list)

# Request/Response Schemas for API endpoints

class DiceJobCreateRequest(BaseModel):
    """Request to create a new DICE job"""
    files: List[FileInfo]
    meeting_title: str
    meeting_description: Optional[str] = None
    expected_language: str = Field(default="en")
    
    # Processing options
    enable_sa_context: bool = Field(default=True)
    auto_approval_threshold: float = Field(ge=0.0, le=1.0, default=0.90)
    require_human_review: bool = Field(default=False)
    
    # TTS options
    generate_tts: bool = Field(default=True)
    tts_voice: str = Field(default="alloy")

class DiceJobResponse(BaseModel):
    """Response after creating or querying a DICE job"""
    job_id: uuid.UUID
    status: DiceJobStatus
    created_at: datetime
    updated_at: datetime
    
    # Results (populated as available)
    pre_scan_result: Optional[PreScanJSON] = None
    draft_transcript: Optional[DraftTranscriptJSON] = None
    validation_report: Optional[ValidationReportJSON] = None
    final_minutes: Optional[FinalMinutes] = None
    
    # URLs for file downloads
    download_urls: Dict[str, str] = Field(default_factory=dict)

class HITLReviewRequest(BaseModel):
    """Request for human-in-the-loop review submission"""
    job_id: uuid.UUID
    reviewer_id: uuid.UUID
    
    # Edited transcript
    edited_segments: List[TranscriptSegment]
    
    # Issue resolutions
    resolved_issues: List[str] = Field(default_factory=list)  # List of issue_ids
    ignored_issues: List[str] = Field(default_factory=list)   # List of issue_ids
    
    # Additional edits
    manual_corrections: List[Dict[str, Any]] = Field(default_factory=list)
    reviewer_notes: Optional[str] = None
    
    # Approval
    approved: bool = Field(default=False)
    require_reprocessing: bool = Field(default=False)

class HITLReviewResponse(BaseModel):
    """Response after HITL review submission"""
    success: bool
    job_id: uuid.UUID
    next_step: str
    estimated_completion: Optional[datetime] = None
    message: str

# Export Schemas

class ExportRequest(BaseModel):
    """Request to export meeting minutes in specific format"""
    job_id: uuid.UUID
    format: Literal["pdf", "docx", "txt", "json", "srt"]
    include_transcript: bool = Field(default=True)
    include_metadata: bool = Field(default=True)
    template: Optional[str] = None

class ExportResponse(BaseModel):
    """Response with export file information"""
    success: bool
    download_url: str
    expires_at: datetime
    file_size: int
    format: str

# Analytics and Reporting

class DiceAnalytics(BaseModel):
    """Analytics data for DICE processing"""
    total_jobs: int = 0
    jobs_by_status: Dict[str, int] = Field(default_factory=dict)
    average_processing_time: float = 0.0
    success_rate: float = 0.0
    
    # Quality metrics
    average_quality_scores: Dict[str, float] = Field(default_factory=dict)
    hitl_review_rate: float = 0.0
    auto_approval_rate: float = 0.0
    
    # SA Context metrics
    sa_terms_applied: int = 0
    sa_names_corrected: int = 0
    sa_context_accuracy: float = 0.0

class ProcessingMetrics(BaseModel):
    """Detailed processing metrics for monitoring"""
    job_id: uuid.UUID
    step_timings: Dict[str, float] = Field(default_factory=dict)
    resource_usage: Dict[str, Any] = Field(default_factory=dict)
    quality_metrics: Dict[str, float] = Field(default_factory=dict)
    error_count: int = 0
    retry_count: int = 0



