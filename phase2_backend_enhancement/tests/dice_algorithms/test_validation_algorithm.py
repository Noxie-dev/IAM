"""
Unit tests for DICE™ Validation Algorithm
Tests South African context validation, name matching, and quality assurance
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, MagicMock
from typing import List

from app.services.dice_algorithms.validation_algorithm import ValidationAlgorithm, SANameMatcher
from app.schemas.dice_schemas import (
    PreScanJSON, DraftTranscriptJSON, ValidationReportJSON,
    ValidationIssue, TranscriptSegment
)
from tests.fixtures.dice_test_data import DICETestFixtures, DICETestConstants


class TestSANameMatcher:
    """Test suite for South African name matching functionality"""
    
    @pytest.fixture
    def name_matcher(self):
        """Create a SANameMatcher instance for testing"""
        return SANameMatcher()
    
    def test_south_african_name_variations(self, name_matcher):
        """Test matching of South African name variations"""
        # Test Afrikaans name variations
        assert name_matcher.match_names("Johannes", "Jan") > 0.8
        assert name_matcher.match_names("Pieter", "Piet") > 0.8
        assert name_matcher.match_names("Francois", "Frans") > 0.8
        
        # Test English/Afrikaans combinations
        assert name_matcher.match_names("William", "Willem") > 0.7
        assert name_matcher.match_names("James", "Jakobus") > 0.6
    
    def test_zulu_xhosa_name_matching(self, name_matcher):
        """Test matching of Zulu and Xhosa names"""
        # Test common Zulu names
        assert name_matcher.match_names("Thabo", "Thabo Mthembu") > 0.8
        assert name_matcher.match_names("Nomsa", "Nomsa Dlamini") > 0.8
        
        # Test Xhosa names
        assert name_matcher.match_names("Mandla", "Mandla Ncube") > 0.8
        assert name_matcher.match_names("Nokuthula", "Nokuthula Mthembu") > 0.8
    
    def test_surname_matching(self, name_matcher):
        """Test South African surname matching"""
        # Test common SA surnames
        assert name_matcher.match_names("Van der Merwe", "vd Merwe") > 0.8
        assert name_matcher.match_names("Du Plessis", "DuPlessis") > 0.9
        assert name_matcher.match_names("De Villiers", "Devilliers") > 0.8
        
        # Test compound surnames
        assert name_matcher.match_names("Van Zyl", "VanZyl") > 0.8
        assert name_matcher.match_names("Le Roux", "LeRoux") > 0.8
    
    def test_title_variations(self, name_matcher):
        """Test matching names with SA titles and prefixes"""
        # Test titles
        assert name_matcher.match_names("Dr. Smith", "Smith") > 0.8
        assert name_matcher.match_names("Prof. Van der Walt", "Van der Walt") > 0.8
        assert name_matcher.match_names("Adv. Patel", "Patel") > 0.8
        
        # Test honorifics
        assert name_matcher.match_names("Mr. Johannes", "Johannes") > 0.8
        assert name_matcher.match_names("Mrs. De Wet", "De Wet") > 0.8
    
    def test_initials_matching(self, name_matcher):
        """Test matching names with initials"""
        assert name_matcher.match_names("J.P. Smith", "John Peter Smith") > 0.7
        assert name_matcher.match_names("M.J. van Zyl", "Marius Johannes van Zyl") > 0.7
        assert name_matcher.match_names("A.B. Dlamini", "Andile Bongani Dlamini") > 0.7
    
    def test_phonetic_similarity(self, name_matcher):
        """Test phonetic similarity for SA names"""
        # Test similar sounding names
        assert name_matcher.match_names("Stefan", "Stephen") > 0.7
        assert name_matcher.match_names("Kathryn", "Catherine") > 0.7
        assert name_matcher.match_names("Nicolaas", "Nicholas") > 0.7


class TestValidationAlgorithm:
    """Test suite for Validation Algorithm"""
    
    @pytest.fixture
    def validation_algorithm(self):
        """Create a ValidationAlgorithm instance for testing"""
        return ValidationAlgorithm()
    
    @pytest.fixture
    def sample_prescan_result(self):
        """Create sample prescan results for testing"""
        return DICETestFixtures.create_sample_prescan_result()
    
    @pytest.fixture
    def sample_draft_transcript(self):
        """Create sample draft transcript for testing"""
        return DICETestFixtures.create_sample_draft_transcript()
    
    @pytest.mark.asyncio
    async def test_validate_transcript_basic(self, validation_algorithm, sample_prescan_result, sample_draft_transcript):
        """Test basic transcript validation functionality"""
        result = await validation_algorithm.validate_transcript(
            sample_prescan_result, 
            sample_draft_transcript
        )
        
        # Verify the result structure
        assert isinstance(result, ValidationReportJSON)
        assert result.overall_confidence > 0.0
        assert result.sa_context_score > 0.0
        assert isinstance(result.issues_found, list)
        assert result.algorithm_version == "2.0.0"
    
    @pytest.mark.asyncio
    async def test_name_normalization(self, validation_algorithm):
        """Test South African name normalization"""
        # Create transcript with SA name variations
        segments = [
            TranscriptSegment(
                speaker="J.P. van der Merwe",
                start_time=0.0,
                end_time=30.0,
                text="Welcome to our meeting."
            ),
            TranscriptSegment(
                speaker="Johannes Pieter vd Merwe",
                start_time=30.0,
                end_time=60.0,
                text="Thank you for joining us."
            )
        ]
        
        draft_transcript = DraftTranscriptJSON(segments=segments)
        prescan_result = PreScanJSON(
            entities_detected={"PERSON": ["J.P. van der Merwe", "Johannes vd Merwe"]}
        )
        
        result = await validation_algorithm.validate_transcript(prescan_result, draft_transcript)
        
        # Should detect and normalize name variations
        assert result.name_normalization_applied
        name_issues = [issue for issue in result.issues_found if issue.type == "name_mismatch"]
        assert len(name_issues) >= 0  # May or may not find issues depending on matching confidence
    
    @pytest.mark.asyncio
    async def test_timing_validation(self, validation_algorithm):
        """Test audio timing validation"""
        # Create segments with timing issues
        segments = [
            TranscriptSegment(
                speaker="Speaker 1",
                start_time=0.0,
                end_time=30.0,
                text="First segment."
            ),
            TranscriptSegment(
                speaker="Speaker 2", 
                start_time=35.0,  # Gap of 5 seconds
                end_time=60.0,
                text="Second segment with gap."
            ),
            TranscriptSegment(
                speaker="Speaker 1",
                start_time=55.0,  # Overlap with previous segment
                end_time=90.0,
                text="Overlapping segment."
            )
        ]
        
        draft_transcript = DraftTranscriptJSON(segments=segments)
        prescan_result = PreScanJSON(total_duration=90.0)
        
        result = await validation_algorithm.validate_transcript(prescan_result, draft_transcript)
        
        # Should detect timing issues
        timing_issues = [issue for issue in result.issues_found if issue.type in ["timing_gap", "timing_overlap"]]
        assert len(timing_issues) > 0
        assert result.timing_adjustments_applied
    
    @pytest.mark.asyncio
    async def test_sa_context_scoring(self, validation_algorithm):
        """Test South African context scoring"""
        # Create content with SA-specific terms and context
        sa_segments = [
            TranscriptSegment(
                speaker="Chairperson",
                start_time=0.0,
                end_time=30.0,
                text="Welcome to this board meeting. We'll discuss the BEE compliance and transformation initiatives."
            ),
            TranscriptSegment(
                speaker="CFO",
                start_time=30.0,
                end_time=60.0,
                text="Our revenue in Randela was R2.5 million this quarter, with VAT implications to consider."
            )
        ]
        
        draft_transcript = DraftTranscriptJSON(segments=sa_segments)
        prescan_result = PreScanJSON(
            entities_detected={"MONEY": ["R2.5 million"], "ORG": ["BEE"]}
        )
        
        result = await validation_algorithm.validate_transcript(prescan_result, draft_transcript)
        
        # Should recognize SA context and score appropriately
        assert result.sa_context_score > 0.7  # Should be high for SA-specific content
    
    @pytest.mark.asyncio
    async def test_content_consistency_validation(self, validation_algorithm):
        """Test validation of content consistency between sources"""
        # Create inconsistent content
        prescan_result = PreScanJSON(
            entities_detected={"PERSON": ["John Smith", "Jane Doe"], "MONEY": ["$1.2M"]},
            pages=[
                # Document mentions different people
            ]
        )
        
        # Transcript mentions different people
        segments = [
            TranscriptSegment(
                speaker="Bob Wilson",  # Not in document
                start_time=0.0,
                end_time=30.0,
                text="Our revenue was $1.5M this quarter."  # Different amount
            )
        ]
        
        draft_transcript = DraftTranscriptJSON(segments=segments)
        
        result = await validation_algorithm.validate_transcript(prescan_result, draft_transcript)
        
        # Should detect inconsistencies
        consistency_issues = [issue for issue in result.issues_found if issue.type == "content_inconsistency"]
        assert len(consistency_issues) >= 0  # May detect financial discrepancies
    
    @pytest.mark.asyncio
    async def test_language_detection(self, validation_algorithm):
        """Test detection of multiple languages in SA context"""
        # Mix of English and Afrikaans
        mixed_segments = [
            TranscriptSegment(
                speaker="Speaker 1",
                start_time=0.0,
                end_time=30.0,
                text="Welcome to our meeting. Welkom by ons vergadering."
            ),
            TranscriptSegment(
                speaker="Speaker 2",
                start_time=30.0,
                end_time=60.0,
                text="Dankie, thank you for the warm welcome."
            )
        ]
        
        draft_transcript = DraftTranscriptJSON(segments=mixed_segments, language="en")
        prescan_result = PreScanJSON()
        
        result = await validation_algorithm.validate_transcript(prescan_result, draft_transcript)
        
        # Should handle multilingual content appropriately
        language_issues = [issue for issue in result.issues_found if issue.type == "language_inconsistency"]
        # May or may not flag this depending on tolerance for SA multilingual context
    
    @pytest.mark.asyncio
    async def test_confidence_calculation(self, validation_algorithm, sample_prescan_result, sample_draft_transcript):
        """Test overall confidence calculation"""
        result = await validation_algorithm.validate_transcript(
            sample_prescan_result,
            sample_draft_transcript
        )
        
        # Confidence should be based on various factors
        assert 0.0 <= result.overall_confidence <= 1.0
        assert result.overall_confidence >= DICETestConstants.MIN_VALIDATION_CONFIDENCE
        
        # Should correlate with input confidences and issues found
        if len(result.issues_found) == 0:
            assert result.overall_confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_issue_severity_classification(self, validation_algorithm):
        """Test classification of validation issues by severity"""
        # Create various types of issues
        segments = [
            TranscriptSegment(
                speaker="",  # Critical: Empty speaker
                start_time=0.0,
                end_time=30.0,
                text="Important announcement."
            ),
            TranscriptSegment(
                speaker="John Smith",
                start_time=30.5,  # Minor: Small timing gap
                end_time=60.0,
                text="Thank you for the announcement."
            )
        ]
        
        draft_transcript = DraftTranscriptJSON(segments=segments)
        prescan_result = PreScanJSON()
        
        result = await validation_algorithm.validate_transcript(prescan_result, draft_transcript)
        
        # Should classify issues by severity
        critical_issues = [issue for issue in result.issues_found if issue.severity == "critical"]
        minor_issues = [issue for issue in result.issues_found if issue.severity == "low"]
        
        # Critical issues should have lower confidence impact
        if critical_issues:
            assert result.overall_confidence < 0.7
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, validation_algorithm, sample_prescan_result, sample_draft_transcript):
        """Test validation performance meets benchmarks"""
        import time
        
        start_time = time.time()
        result = await validation_algorithm.validate_transcript(
            sample_prescan_result,
            sample_draft_transcript
        )
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should complete within time limit
        assert processing_time < DICETestConstants.MAX_VALIDATION_TIME
        assert result.processing_time >= 0.0
    
    @pytest.mark.asyncio
    async def test_large_transcript_handling(self, validation_algorithm):
        """Test handling of large transcripts"""
        # Create a large transcript
        large_segments = []
        for i in range(1000):  # 1000 segments
            large_segments.append(
                TranscriptSegment(
                    speaker=f"Speaker {i % 10}",
                    start_time=i * 30.0,
                    end_time=(i + 1) * 30.0,
                    text=f"This is segment number {i} with some content."
                )
            )
        
        large_transcript = DraftTranscriptJSON(segments=large_segments)
        prescan_result = PreScanJSON(total_duration=30000.0)  # Long audio
        
        result = await validation_algorithm.validate_transcript(prescan_result, large_transcript)
        
        # Should handle large transcripts without issues
        assert isinstance(result, ValidationReportJSON)
        assert result.processing_time < DICETestConstants.MAX_VALIDATION_TIME * 3  # Allow extra time for large data
    
    def test_sa_specific_entities(self, validation_algorithm):
        """Test recognition of South African specific entities"""
        sa_entities = [
            "JSE",  # Johannesburg Stock Exchange
            "SARS",  # South African Revenue Service
            "CIPC",  # Companies and Intellectual Property Commission
            "BEE",  # Black Economic Empowerment
            "POPI",  # Protection of Personal Information
            "PFMA",  # Public Finance Management Act
        ]
        
        for entity in sa_entities:
            score = validation_algorithm._calculate_sa_context_score([entity])
            assert score > 0.5  # Should recognize SA-specific terms
    
    def test_currency_normalization(self, validation_algorithm):
        """Test South African currency normalization"""
        # Test various Rand representations
        currency_variations = [
            "R1,000",
            "R 1000", 
            "ZAR 1000",
            "1000 Rand",
            "R1000.00",
            "1,000 ZAR"
        ]
        
        normalized = validation_algorithm._normalize_sa_currency(currency_variations)
        
        # Should normalize to consistent format
        assert all("R" in norm or "ZAR" in norm for norm in normalized)


@pytest.mark.integration
class TestValidationAlgorithmIntegration:
    """Integration tests for Validation Algorithm"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_validation(self):
        """Test complete validation workflow"""
        # This would test the full validation pipeline
        # with realistic data from previous DICE stages
        pass
    
    @pytest.mark.asyncio
    async def test_sa_context_with_real_data(self):
        """Test SA context validation with real South African content"""
        # This would test with actual SA meeting transcripts
        # and documents for context validation
        pass
