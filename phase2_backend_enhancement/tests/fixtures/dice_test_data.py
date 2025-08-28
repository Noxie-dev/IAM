"""
Test fixtures and sample data for DICE algorithm unit tests
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import MagicMock, AsyncMock

from app.schemas.dice_schemas import (
    FileInfo, PreScanJSON, PreScanBlock, PreScanAudioSegment,
    DraftTranscriptJSON, TranscriptSegment, ValidationReportJSON,
    ValidationIssue, FinalMinutes
)


class DICETestFixtures:
    """Test fixtures for DICE algorithm testing"""
    
    @staticmethod
    def create_sample_file_info() -> FileInfo:
        """Create a sample FileInfo object for testing"""
        return FileInfo(
            file_id=uuid.uuid4(),
            s3_uri="s3://test-bucket/test-file.pdf",
            mime_type="application/pdf",
            original_filename="test_document.pdf",
            file_size=1024000,
            upload_timestamp=datetime.utcnow()
        )
    
    @staticmethod
    def create_sample_audio_file_info() -> FileInfo:
        """Create a sample audio FileInfo object for testing"""
        return FileInfo(
            file_id=uuid.uuid4(),
            s3_uri="s3://test-bucket/test-audio.wav",
            mime_type="audio/wav",
            original_filename="meeting_recording.wav",
            file_size=5242880,  # 5MB
            upload_timestamp=datetime.utcnow()
        )
    
    @staticmethod
    def create_sample_prescan_blocks() -> List[PreScanBlock]:
        """Create sample OCR blocks for testing"""
        return [
            PreScanBlock(
                type="text",
                bbox=[100.0, 200.0, 500.0, 250.0],
                text="Meeting Minutes - Board of Directors",
                confidence=0.95,
                page_number=1
            ),
            PreScanBlock(
                type="text",
                bbox=[100.0, 300.0, 600.0, 400.0],
                text="Attendees: John Smith (CEO), Jane Doe (CFO), Bob Wilson (CTO)",
                confidence=0.92,
                page_number=1
            ),
            PreScanBlock(
                type="table",
                bbox=[100.0, 450.0, 700.0, 600.0],
                text="Q3 Financial Results\nRevenue: $1.2M\nExpenses: $800K\nProfit: $400K",
                confidence=0.88,
                page_number=1
            )
        ]
    
    @staticmethod
    def create_sample_audio_segments() -> List[PreScanAudioSegment]:
        """Create sample audio segments for testing"""
        return [
            PreScanAudioSegment(
                start_time=0.0,
                end_time=30.5,
                speaker_hint="Speaker_1",
                confidence=0.87
            ),
            PreScanAudioSegment(
                start_time=30.5,
                end_time=65.2,
                speaker_hint="Speaker_2",
                confidence=0.92
            ),
            PreScanAudioSegment(
                start_time=65.2,
                end_time=120.8,
                speaker_hint="Speaker_1",
                confidence=0.89
            )
        ]
    
    @staticmethod
    def create_sample_prescan_result() -> PreScanJSON:
        """Create a complete PreScanJSON result for testing"""
        return PreScanJSON(
            ocr_confidence=0.92,
            diarization_confidence=0.89,
            entities_detected={
                "PERSON": ["John Smith", "Jane Doe", "Bob Wilson"],
                "ORG": ["Board of Directors", "Finance Department"],
                "MONEY": ["$1.2M", "$800K", "$400K"]
            },
            pages=DICETestFixtures.create_sample_prescan_blocks(),
            total_pages=1,
            audio_segments=DICETestFixtures.create_sample_audio_segments(),
            total_duration=120.8,
            processing_time=5.4,
            algorithm_version="1.0.0"
        )
    
    @staticmethod
    def create_sample_transcript_segments() -> List[TranscriptSegment]:
        """Create sample transcript segments for testing"""
        return [
            TranscriptSegment(
                speaker="John Smith",
                start_time=0.0,
                end_time=30.5,
                text="Welcome everyone to our Q3 board meeting. Let's start by reviewing our financial performance.",
                confidence=0.94
            ),
            TranscriptSegment(
                speaker="Jane Doe",
                start_time=30.5,
                end_time=65.2,
                text="Thank you John. Our Q3 revenue reached $1.2 million, which is a 15% increase from Q2. Operating expenses were $800,000.",
                confidence=0.91
            ),
            TranscriptSegment(
                speaker="Bob Wilson",
                start_time=65.2,
                end_time=120.8,
                text="From a technology perspective, we've successfully migrated to the new cloud infrastructure, which should reduce our operational costs by 20%.",
                confidence=0.88
            )
        ]
    
    @staticmethod
    def create_sample_draft_transcript() -> DraftTranscriptJSON:
        """Create a sample draft transcript for testing"""
        return DraftTranscriptJSON(
            language="en",
            segments=DICETestFixtures.create_sample_transcript_segments(),
            summary="Q3 board meeting discussing financial performance and technology updates. Revenue increased 15% to $1.2M, with successful cloud migration expected to reduce costs by 20%.",
            action_items=[
                "Review technology cost savings in Q4",
                "Prepare detailed financial breakdown for next meeting",
                "Schedule follow-up on cloud migration progress"
            ],
            key_topics=["Financial Performance", "Cloud Migration", "Cost Reduction"],
            model_used="gpt-4o",
            ai_provider="openai",
            confidence=0.91,
            processing_time=12.3,
            token_usage={"prompt_tokens": 1200, "completion_tokens": 800, "total_tokens": 2000}
        )
    
    @staticmethod
    def create_sample_validation_issues() -> List[ValidationIssue]:
        """Create sample validation issues for testing"""
        return [
            ValidationIssue(
                issue_id=str(uuid.uuid4()),
                type="name_mismatch",
                severity="medium",
                description="Speaker name 'John Smith' in transcript doesn't match document reference 'J. Smith'",
                suggested_fix="Normalize name to 'John Smith'",
                confidence=0.75,
                context={"transcript_name": "John Smith", "document_name": "J. Smith"}
            ),
            ValidationIssue(
                issue_id=str(uuid.uuid4()),
                type="timing_inconsistency",
                severity="low",
                description="Small gap detected in audio segments",
                suggested_fix="Interpolate timing for segment continuity",
                confidence=0.82,
                context={"gap_duration": 0.3, "segment_before": 65.2, "segment_after": 65.5}
            )
        ]
    
    @staticmethod
    def create_sample_validation_report() -> ValidationReportJSON:
        """Create a sample validation report for testing"""
        return ValidationReportJSON(
            overall_confidence=0.87,
            issues_found=DICETestFixtures.create_sample_validation_issues(),
            sa_context_score=0.92,
            name_normalization_applied=True,
            timing_adjustments_applied=True,
            processing_time=3.7,
            algorithm_version="2.0.0"
        )
    
    @staticmethod
    def create_sample_final_minutes() -> FinalMinutes:
        """Create sample final minutes for testing"""
        return FinalMinutes(
            title="Q3 2024 Board of Directors Meeting",
            date=datetime.utcnow(),
            attendees=["John Smith (CEO)", "Jane Doe (CFO)", "Bob Wilson (CTO)"],
            executive_summary="Quarterly review meeting covering financial performance and technology updates. Strong revenue growth of 15% achieved with successful cloud migration project completion.",
            key_decisions=[
                "Approved Q4 technology budget allocation",
                "Endorsed cloud migration cost savings strategy",
                "Scheduled monthly financial review meetings"
            ],
            action_items=[
                {
                    "task": "Review technology cost savings in Q4",
                    "assignee": "Bob Wilson",
                    "due_date": "2024-01-15",
                    "priority": "high"
                },
                {
                    "task": "Prepare detailed financial breakdown",
                    "assignee": "Jane Doe",
                    "due_date": "2024-01-10",
                    "priority": "medium"
                }
            ],
            discussion_topics=[
                {
                    "topic": "Q3 Financial Performance",
                    "summary": "Revenue increased 15% to $1.2M with controlled expense growth",
                    "duration_minutes": 15
                },
                {
                    "topic": "Cloud Migration Update",
                    "summary": "Successful migration completed with 20% cost reduction achieved",
                    "duration_minutes": 10
                }
            ],
            financial_data=[
                {"metric": "Q3 Revenue", "value": "$1.2M", "change": "+15%"},
                {"metric": "Operating Expenses", "value": "$800K", "change": "+5%"},
                {"metric": "Net Profit", "value": "$400K", "change": "+33%"}
            ],
            confidence_score=0.91,
            processing_time=8.2,
            word_count=1247,
            page_count=3,
            generated_by="DICE™ v2.0.0"
        )
    
    @staticmethod
    def create_mock_s3_client():
        """Create a mock S3 client for testing"""
        mock_s3 = MagicMock()
        mock_s3.download_file = MagicMock()
        mock_s3.upload_file = MagicMock()
        mock_s3.get_object = MagicMock(return_value={
            'Body': MagicMock(read=MagicMock(return_value=b'mock file content'))
        })
        return mock_s3
    
    @staticmethod
    def create_mock_openai_client():
        """Create a mock OpenAI client for testing"""
        mock_openai = MagicMock()
        mock_openai.audio.transcriptions.create = AsyncMock(return_value=MagicMock(
            text="This is a mock transcription of the audio file."
        ))
        mock_openai.chat.completions.create = AsyncMock(return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="Mock AI response"))]
        ))
        return mock_openai
    
    @staticmethod
    def create_mock_spacy_nlp():
        """Create a mock spaCy NLP model for testing"""
        mock_nlp = MagicMock()
        mock_doc = MagicMock()
        mock_doc.ents = [
            MagicMock(text="John Smith", label_="PERSON"),
            MagicMock(text="Board of Directors", label_="ORG"),
            MagicMock(text="$1.2M", label_="MONEY")
        ]
        mock_nlp.return_value = mock_doc
        return mock_nlp


class DICETestConstants:
    """Constants for DICE testing"""
    
    # Test file paths
    SAMPLE_PDF_PATH = "/tmp/test_document.pdf"
    SAMPLE_AUDIO_PATH = "/tmp/test_audio.wav"
    SAMPLE_IMAGE_PATH = "/tmp/test_image.jpg"
    
    # Expected processing times (for performance testing)
    MAX_PRESCAN_TIME = 30.0  # seconds
    MAX_AI_LAYER1_TIME = 60.0
    MAX_VALIDATION_TIME = 10.0
    MAX_AI_LAYER2_TIME = 45.0
    MAX_TTS_TIME = 15.0
    
    # Quality thresholds
    MIN_OCR_CONFIDENCE = 0.7
    MIN_TRANSCRIPT_CONFIDENCE = 0.8
    MIN_VALIDATION_CONFIDENCE = 0.75
    MIN_OVERALL_CONFIDENCE = 0.8
    
    # Test data sizes
    SMALL_FILE_SIZE = 1024 * 1024  # 1MB
    MEDIUM_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    LARGE_FILE_SIZE = 50 * 1024 * 1024  # 50MB
